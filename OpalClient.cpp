#include "OpalClient.h"
#include "Config.h"
#include "SerialBuffer.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <mbedtls/sha256.h>

// ============================================================
//  Opal router client
// ============================================================
static String   opal_sid           = "";
static bool     opal_paused        = false;
static volatile unsigned long opal_sid_time = 0;
static uint64_t opal_last_rx       = 0;
static bool     opal_have_baseline = false;
static unsigned long opal_last_ok_ms = 0;

#define OPAL_LOGIN_REFRESH_MS 240000UL

// ------------------------------------------------------------
static String sha256_hex(const String &input) {
    byte hash[32];
    mbedtls_sha256((const unsigned char*)input.c_str(), input.length(), hash, 0);

    char hex[65];
    for (int i = 0; i < 32; i++) {
        sprintf(hex + i * 2, "%02x", hash[i]);
    }
    hex[64] = 0;
    return String(hex);
}

// ------------------------------------------------------------
static bool rpc_call(const String &json_body, String &response) {
    digitalWrite(LED_PIN, LOW);

    HTTPClient http;
    String url = String("http://") + OPAL_IP + "/rpc";

    if (!http.begin(url)) {
        log_print("[OPAL] http.begin failed\n");
        digitalWrite(LED_PIN, HIGH);
        return false;
    }
    http.setTimeout(3000);
    http.addHeader("Content-Type", "application/json");

    int code = http.POST(json_body);
    if (code != 200) {
        log_print("[OPAL] HTTP %d\n", code);
        http.end();
        digitalWrite(LED_PIN, HIGH);
        return false;
    }

    response = http.getString();
    http.end();

    digitalWrite(LED_PIN, HIGH);
    return true;
}

// ------------------------------------------------------------
static bool opal_login() {
    log_print("[OPAL] logging in...\n");

    String challenge_body =
        "{\"jsonrpc\":\"2.0\",\"method\":\"challenge\","
        "\"params\":{\"username\":\"" OPAL_USER "\"},\"id\":1}";

    String challenge_resp;
    if (!rpc_call(challenge_body, challenge_resp)) {
        log_print("[OPAL] challenge failed\n");
        return false;
    }

    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, challenge_resp);
    if (err) {
        log_print("[OPAL] challenge JSON: %s\n", err.c_str());
        return false;
    }

    const char* salt  = doc["result"]["salt"];
    const char* nonce = doc["result"]["nonce"];
    int alg           = doc["result"]["alg"] | 5;

    if (!salt || !nonce) {
        log_print("[OPAL] no salt/nonce in challenge\n");
        return false;
    }

    log_print("[OPAL] salt=%s alg=%d\n", salt, alg);

    extern const char* OPAL_CRYPT_HASH;

    String login_input = String(OPAL_USER) + ":" + OPAL_CRYPT_HASH + ":" + nonce;
    String login_hash  = sha256_hex(login_input);

    String login_body =
        "{\"jsonrpc\":\"2.0\",\"method\":\"login\","
        "\"params\":{\"username\":\"" OPAL_USER "\",\"hash\":\"" + login_hash + "\"},"
        "\"id\":2}";

    String login_resp;
    if (!rpc_call(login_body, login_resp)) {
        log_print("[OPAL] login HTTP failed\n");
        return false;
    }

    StaticJsonDocument<512> login_doc;
    err = deserializeJson(login_doc, login_resp);
    if (err) {
        log_print("[OPAL] login JSON: %s\n", err.c_str());
        return false;
    }

    const char* sid = login_doc["result"]["sid"];
    if (!sid) {
        log_print("[OPAL] no sid in login response\n");
        return false;
    }

    opal_sid      = String(sid);
    opal_sid_time = millis();
    log_print("[OPAL] SID set t=%lu len=%u\n",
              (unsigned long)opal_sid_time, opal_sid.length());

    log_print("[OPAL] login OK\n");
    return true;
}

// ------------------------------------------------------------
static bool opal_ensure_login() {
    bool sid_empty = (opal_sid.length() == 0);
    bool sid_expired = (millis() - opal_sid_time > OPAL_LOGIN_REFRESH_MS);
    log_print("[OPAL] check t=%lu now=%lu diff=%lu\n",
              (unsigned long)opal_sid_time,
              (unsigned long)millis(),
              (unsigned long)(millis() - opal_sid_time));
    if (sid_empty || sid_expired) {
        log_print("[OPAL] relogin (empty=%d expired=%d age=%lus)\n",
                  sid_empty ? 1 : 0, sid_expired ? 1 : 0,
                  (unsigned long)((millis() - opal_sid_time) / 1000UL));
        if (!opal_login()) {
            return false;
        }
    }
    return true;
}

// ------------------------------------------------------------
void opal_init() {
    opal_sid           = "";
    opal_sid_time      = 0;
    opal_have_baseline = false;

    if (!opal_login()) {
        log_print("[OPAL] init: login failed, will retry in poll\n");
    }
}

// ------------------------------------------------------------
// Poll traffic statistics from connected clients list
// ------------------------------------------------------------
bool opal_poll(uint64_t &rx_total) {
    if (opal_paused) return false;
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    if (!opal_ensure_login()) {
        return false;
    }

    String body = String("{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":[\"") +
                  opal_sid + "\",\"clients\",\"get_list\",{}],\"id\":3}";

    String resp;
    if (!rpc_call(body, resp)) {
        log_print("[OPAL] poll rpc failed\n");
        return false;
    }

    StaticJsonDocument<8192> doc;
    DeserializationError err = deserializeJson(doc, resp);
    if (err) {
        log_print("[OPAL] poll JSON: %s\n", err.c_str());
        return false;
    }

    if (doc.containsKey("error")) {
        log_print("[OPAL] poll denied, forcing relogin\n");
        opal_sid = "";
        return false;
    }

    JsonArray clients = doc["result"]["clients"];
    if (clients.isNull()) {
        log_print("[OPAL] no clients array\n");
        return false;
    }

    uint64_t total = 0;
    for (JsonObject c : clients) {
        if (c["total_rx"].is<const char*>()) {
            total += strtoull(c["total_rx"].as<const char*>(), NULL, 10);
        } else {
            total += c["total_rx"].as<uint64_t>();
        }
    }

    rx_total = total;
    opal_last_ok_ms = millis();
    return true;
}

bool opal_ok_recently() {
    if (opal_last_ok_ms == 0) return false;
    return (millis() - opal_last_ok_ms) < 45000;   // 3 ticks * 15s
}

// ------------------------------------------------------------
// Enable or disable the Wi-Fi repeater via JSON-RPC
// ------------------------------------------------------------
bool opal_set_repeater(bool enable) {
    if (opal_paused) return false;
    if (WiFi.status() != WL_CONNECTED) {
        log_print("[OPAL] repeater: WiFi not connected\n");
        return false;
    }

    for (int attempt = 0; attempt < 2; attempt++) {
        if (!opal_ensure_login()) {
            log_print("[OPAL] repeater: login failed\n");
            return false;
        }

        String action = enable ? "scan" : "disconnect";
        String body = String("{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":[\"") +
                      opal_sid + "\",\"repeater\",\"" + action + "\",{}],\"id\":24}";

        log_print("[OPAL] repeater POST: %s\n", body.c_str());

        String resp;
        if (!rpc_call(body, resp)) {
            log_print("[OPAL] repeater: rpc_call failed\n");
            return false;
        }

        log_print("[OPAL] repeater response: %s\n", resp.c_str());

        StaticJsonDocument<512> doc;
        DeserializationError err = deserializeJson(doc, resp);
        if (err) {
            log_print("[OPAL] repeater JSON parse error: %s\n", err.c_str());
            return false;
        }

        if (doc.containsKey("error")) {
            log_print("[OPAL] repeater command denied, forcing relogin\n");
            opal_sid = "";
            continue;
        }

        log_print("[OPAL] Repeater %s successfully\n", enable ? "STARTED" : "STOPPED");
        return true;
    }

    return false;
}

// ------------------------------------------------------------
void opal_force_relogin() { 
    opal_sid = ""; 
}

bool opal_logged_in() { 
    return opal_sid.length() > 0; 
}

void opal_pause() { 
    opal_paused = true; 
    log_print("[OPAL] paused\n"); 
}

void opal_resume() { 
    opal_paused = false; 
    opal_sid = ""; 
    log_print("[OPAL] resumed\n"); 
}

bool opal_is_paused() { 
    return opal_paused; 
}