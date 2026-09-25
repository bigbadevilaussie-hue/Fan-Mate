#include "OpalClient.h"
#include "Config.h"

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <mbedtls/md.h>

// ============================================================
//  Opal router client
//  V3.32 — adds pause/resume for sleep, log-once on failure
// ============================================================

static String   opal_sid;
static uint32_t opal_sid_time   = 0;
static bool     opal_paused     = false;
static bool     opal_was_down   = false;

// ------------------------------------------------------------
//  SHA-256 helpers (Opal uses salted SHA-256 for login)
// ------------------------------------------------------------
static String sha256_hex(const String& input) {
    uint8_t hash[32];
    mbedtls_md_context_t ctx;
    mbedtls_md_init(&ctx);
    mbedtls_md_setup(&ctx, mbedtls_md_info_from_type(MBEDTLS_MD_SHA256), 0);
    mbedtls_md_starts(&ctx);
    mbedtls_md_update(&ctx, (const uint8_t*)input.c_str(), input.length());
    mbedtls_md_finish(&ctx, hash);
    mbedtls_md_free(&ctx);

    char out[65];
    for (int i = 0; i < 32; i++) sprintf(out + i * 2, "%02x", hash[i]);
    out[64] = 0;
    return String(out);
}

// ------------------------------------------------------------
//  HTTP helpers
// ------------------------------------------------------------
static String opal_get(const String& path, int timeout_ms = 4000) {
    HTTPClient http;
    String url = String("http://") + OPAL_IP + path;
    http.begin(url);
    http.setTimeout(timeout_ms);
    if (opal_sid.length()) {
        http.addHeader("Cookie", "sysauth=" + opal_sid);
    }
    int code = http.GET();
    String body = (code > 0) ? http.getString() : "";
    http.end();
    if (code != 200) {
        Serial.printf("[OPAL] GET %s → %d\n", path.c_str(), code);
        return "";
    }
    return body;
}

static String opal_post(const String& path, const String& data, int timeout_ms = 4000) {
    HTTPClient http;
    String url = String("http://") + OPAL_IP + path;
    http.begin(url);
    http.setTimeout(timeout_ms);
    http.addHeader("Content-Type", "application/x-www-form-urlencoded");
    if (opal_sid.length()) {
        http.addHeader("Cookie", "sysauth=" + opal_sid);
    }
    int code = http.POST(data);
    String body = (code > 0) ? http.getString() : "";
    http.end();
    if (code != 200) {
        Serial.printf("[OPAL] POST %s → %d\n", path.c_str(), code);
        return "";
    }
    return body;
}

// ------------------------------------------------------------
//  Login
// ------------------------------------------------------------
static bool opal_login() {
    Serial.println("[OPAL] logging in...");

    // 1. Get challenge (salt + alg)
    String challenge = opal_get("/cgi-bin/luci");
    if (!challenge.length()) {
        Serial.println("[OPAL] challenge fetch failed");
        return false;
    }

    // Parse salt & alg from JSON response
    StaticJsonDocument<512> doc;
    if (deserializeJson(doc, challenge) != DeserializationError::Ok) {
        Serial.println("[OPAL] challenge JSON parse failed");
        return false;
    }

    String salt = doc["salt"] | "";
    String alg  = doc["alg"]  | "5";
    if (!salt.length()) {
        Serial.println("[OPAL] no salt in challenge");
        return false;
    }

    Serial.printf("[OPAL] salt=%s alg=%s\n", salt.c_str(), alg.c_str());

    // 2. Compute hash: SHA256(user:salt:pass)
    String pw_hash = sha256_hex(String(OPAL_USER) + ":" + salt + ":" + OPAL_PASS);

    // 3. POST login
    String body = "luci_username=" + String(OPAL_USER)
                + "&luci_password=" + pw_hash;

    String resp = opal_post("/cgi-bin/luci", body);
    if (!resp.length()) {
        Serial.println("[OPAL] login POST failed");
        return false;
    }

    // 4. Extract SID from response (json: {"sid":"..."})
    StaticJsonDocument<256> rdoc;
    if (deserializeJson(rdoc, resp) == DeserializationError::Ok) {
        String sid = rdoc["sid"] | "";
        if (sid.length()) {
            opal_sid = sid;
            opal_sid_time = millis();
            Serial.printf("[OPAL] login OK, sid=%s...\n", sid.substring(0, 12).c_str());
            return true;
        }
    }

    Serial.println("[OPAL] login response missing sid");
    return false;
}

// ------------------------------------------------------------
//  Public API
// ------------------------------------------------------------
void opal_init() {
    opal_sid = "";
    opal_sid_time = 0;
    opal_paused = false;
    opal_was_down = false;
    Serial.println("[OPAL] init");
}

bool opal_poll(uint64_t &rx_total) {
    if (opal_paused) return false;
    if (WiFi.status() != WL_CONNECTED) return false;

    // Re-login if session expired or never logged in
    if (!opal_logged_in()) {
        if (!opal_login()) {
            if (!opal_was_down) {
                Serial.println("[OPAL] unreachable");
                opal_was_down = true;
            }
            return false;
        }
    }

    // Poll total bytes on WAN
    String body = opal_get("/cgi-bin/luci/admin/status/wan");
    if (!body.length()) {
        // Session may have expired — force re-login next poll
        opal_sid = "";
        return false;
    }

    StaticJsonDocument<1024> doc;
    if (deserializeJson(doc, body) != DeserializationError::Ok) {
        return false;
    }

    // Parse total received bytes (rx_bytes)
    uint64_t rx = 0;
    if (doc.containsKey("rx_bytes")) {
        rx = doc["rx_bytes"].as<uint64_t>();
    } else if (doc.containsKey("stats") && doc["stats"].containsKey("rx_bytes")) {
        rx = doc["stats"]["rx_bytes"].as<uint64_t>();
    } else {
        return false;
    }

    rx_total = rx;

    if (opal_was_down) {
        Serial.println("[OPAL] back online");
        opal_was_down = false;
    }
    return true;
}

// ------------------------------------------------------------
void opal_force_relogin() {
    opal_sid = "";
    opal_sid_time = 0;
}

bool opal_logged_in() {
    if (!opal_sid.length()) return false;
    // Session valid for OPAL_LOGIN_REFRESH_MS
    if (millis() - opal_sid_time > OPAL_LOGIN_REFRESH_MS) return false;
    return true;
}

// ------------------------------------------------------------
//  Sleep / wake
// ------------------------------------------------------------
void opal_pause() {
    opal_paused = true;
    Serial.println("[OPAL] paused");
}

void opal_resume() {
    opal_paused = false;
    opal_sid = "";       // force fresh login on next poll
    opal_sid_time = 0;
    Serial.println("[OPAL] resumed");
}

bool opal_is_paused() {
    return opal_paused;
}