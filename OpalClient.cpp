#include "OpalClient.h"
#include "Config.h"

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <mbedtls/sha256.h>

// ============================================================
//  Opal router client — implementation
//
//  Login:  POST /rpc  {"method":"challenge",...}
//          → get salt, nonce, alg
//          → compute SHA256 crypt with openssl-equivalent
//          → POST /rpc  {"method":"login",...}
//          → get sid
//
//  Poll:   POST /rpc  {"method":"call","params":[sid,"clients","get_list",{}]}
//          → sum total_rx across all clients
// ============================================================

static String   opal_sid           = "";
static uint32_t opal_sid_time      = 0;    // millis when SID was obtained
static uint64_t opal_last_rx       = 0;
static bool     opal_have_baseline = false;

// ------------------------------------------------------------
//  SHA256 hex helper
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
//  HTTP POST to /rpc
// ------------------------------------------------------------
static bool rpc_call(const String &json_body, String &response) {
    HTTPClient http;
    String url = String("http://") + OPAL_IP + "/rpc";

    if (!http.begin(url)) {
        Serial.println("[OPAL] http.begin failed");
        return false;
    }
    http.setTimeout(3000);
    http.addHeader("Content-Type", "application/json");

    int code = http.POST(json_body);
    if (code != 200) {
        Serial.printf("[OPAL] HTTP %d\n", code);
        http.end();
        return false;
    }

    response = http.getString();
    http.end();
    return true;
}

// ------------------------------------------------------------
//  Login
// ------------------------------------------------------------
static bool opal_login() {
    Serial.println("[OPAL] logging in...");

    // --- Step 1: challenge ---
    String challenge_body =
        "{\"jsonrpc\":\"2.0\",\"method\":\"challenge\","
        "\"params\":{\"username\":\"" OPAL_USER "\"},\"id\":1}";

    String challenge_resp;
    if (!rpc_call(challenge_body, challenge_resp)) {
        Serial.println("[OPAL] challenge failed");
        return false;
    }

    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, challenge_resp);
    if (err) {
        Serial.printf("[OPAL] challenge JSON: %s\n", err.c_str());
        return false;
    }

    const char* salt  = doc["result"]["salt"];
    const char* nonce = doc["result"]["nonce"];
    int alg           = doc["result"]["alg"] | 5;

    if (!salt || !nonce) {
        Serial.println("[OPAL] no salt/nonce in challenge");
        return false;
    }

    Serial.printf("[OPAL] salt=%s alg=%d\n", salt, alg);

    // --- Step 2: pre-computed crypt hash ---
    // We precomputed this from: openssl passwd -5 -salt <SALT> <PASSWORD>
    // It's a fixed value as long as the password and salt don't change.
    // Stored in secrets.h to avoid needing to implement SHA256-crypt.
    extern const char* OPAL_CRYPT_HASH;

    // --- Step 3: login hash = SHA256(user:crypt:nonce) ---
    String login_input = String(OPAL_USER) + ":" + OPAL_CRYPT_HASH + ":" + nonce;
    String login_hash  = sha256_hex(login_input);

    String login_body =
        "{\"jsonrpc\":\"2.0\",\"method\":\"login\","
        "\"params\":{\"username\":\"" OPAL_USER "\",\"hash\":\"" + login_hash + "\"},"
        "\"id\":2}";

    String login_resp;
    if (!rpc_call(login_body, login_resp)) {
        Serial.println("[OPAL] login HTTP failed");
        return false;
    }

    StaticJsonDocument<512> login_doc;
    err = deserializeJson(login_doc, login_resp);
    if (err) {
        Serial.printf("[OPAL] login JSON: %s\n", err.c_str());
        return false;
    }

    const char* sid = login_doc["result"]["sid"];
    if (!sid) {
        Serial.println("[OPAL] no sid in login response");
        return false;
    }

    opal_sid      = String(sid);
    opal_sid_time = millis();

    Serial.printf("[OPAL] login OK, sid=%s...\n", opal_sid.substring(0, 16).c_str());
    return true;
}

// ------------------------------------------------------------
//  Init
// ------------------------------------------------------------
void opal_init() {
    opal_sid           = "";
    opal_sid_time      = 0;
    opal_have_baseline = false;

    if (!opal_login()) {
        Serial.println("[OPAL] init: login failed, will retry in poll");
    }
}

// ------------------------------------------------------------
//  Poll — fetch client list, sum total_rx
// ------------------------------------------------------------
bool opal_poll(uint64_t &rx_total) {
    // Not connected to WiFi?
    if (WiFi.status() != WL_CONNECTED) {
        return false;
    }

    // SID expired?
    if (opal_sid.length() == 0) {
        if (!opal_login()) {
            return false;
        }
    }

    // Refresh SID every 50 minutes
    if (millis() - opal_sid_time > OPAL_LOGIN_REFRESH_MS) {
        Serial.println("[OPAL] SID refresh");
        if (!opal_login()) {
            return false;
        }
    }

    // --- Fetch client list ---
    String body =
        "{\"jsonrpc\":\"2.0\",\"method\":\"call\","
        "\"params\":[\"" + opal_sid + "\",\"clients\",\"get_list\",{}],"
        "\"id\":3}";

    String resp;
    if (!rpc_call(body, resp)) {
        return false;
    }

    StaticJsonDocument<8192> doc;
    DeserializationError err = deserializeJson(doc, resp);
    if (err) {
        Serial.printf("[OPAL] poll JSON: %s\n", err.c_str());
        return false;
    }

    // Access denied? Force re-login next time
    if (doc.containsKey("error")) {
        Serial.println("[OPAL] poll denied, forcing relogin");
        opal_sid = "";
        return false;
    }

    JsonArray clients = doc["result"]["clients"];
    if (clients.isNull()) {
        Serial.println("[OPAL] no clients array");
        return false;
    }

    // Sum total_rx across all clients
    uint64_t total = 0;
    for (JsonObject c : clients) {
        // total_rx may be string or number
        if (c["total_rx"].is<const char*>()) {
            total += strtoull(c["total_rx"].as<const char*>(), NULL, 10);
        } else {
            total += c["total_rx"].as<uint64_t>();
        }
    }

    rx_total = total;
    return true;
}

// ------------------------------------------------------------
//  Force relogin on next poll
// ------------------------------------------------------------
void opal_force_relogin() {
    opal_sid = "";
}

// ------------------------------------------------------------
//  Status
// ------------------------------------------------------------
bool opal_logged_in() {
    return opal_sid.length() > 0;
}