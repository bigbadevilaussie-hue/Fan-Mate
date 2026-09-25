#include "WiFiManager.h"
#include "Config.h"

#include <WiFi.h>
#include <ESPmDNS.h>

// ============================================================
//  WiFi Manager — implementation
//
//  V3.00 — connects to WIFI_SSID, publishes MDNS_HOSTNAME.local
// ============================================================

static bool          wifi_inited        = false;
static unsigned long wifi_connect_start = 0;
static unsigned long wifi_last_attempt  = 0;
static unsigned long wifi_connected_at  = 0;
static bool          mdns_started       = false;

// ------------------------------------------------------------
//  setup — call once from fanmate.ino setup()
// ------------------------------------------------------------
void wifi_setup() {
    if (wifi_inited) return;

    Serial.println();
    Serial.println("[WIFI] ================================");
    Serial.printf ("[WIFI] SSID: %s\n", WIFI_SSID);
    Serial.printf ("[WIFI] mDNS: %s.local\n", MDNS_HOSTNAME);
    Serial.println("[WIFI] ================================");

    WiFi.mode(WIFI_STA);
    WiFi.setHostname(MDNS_HOSTNAME);
    WiFi.setAutoReconnect(true);
    WiFi.setSleep(true);            // REQUIRED when BLE coexists       // full power for HTTP responsiveness

    // Start connection (non-blocking)
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    wifi_connect_start = millis();
    wifi_last_attempt  = millis();
    wifi_inited        = true;

    Serial.printf("[WIFI] connecting...\n");
}

// ------------------------------------------------------------
//  Start mDNS once we have an IP
// ------------------------------------------------------------
static void start_mdns() {
    if (mdns_started) return;

    if (!MDNS.begin(MDNS_HOSTNAME)) {
        Serial.println("[MDNS] ERROR: could not start mDNS");
        return;
    }

    MDNS.addService("http", "tcp", HTTP_PORT);

    Serial.printf("[MDNS] http://%s.local\n", MDNS_HOSTNAME);
    mdns_started = true;
}

// ------------------------------------------------------------
//  loop — call every iteration from fanmate.ino loop()
// ------------------------------------------------------------
void wifi_loop() {
    if (!wifi_inited) return;

    wl_status_t status = WiFi.status();

    if (status == WL_CONNECTED) {
        // Just connected?
        if (wifi_connected_at == 0) {
            wifi_connected_at = millis();

            Serial.println();
            Serial.println("[WIFI] ================================");
            Serial.printf ("[WIFI] CONNECTED\n");
            Serial.printf ("[WIFI] IP:   %s\n", WiFi.localIP().toString().c_str());
            Serial.printf ("[WIFI] RSSI: %d dBm\n", WiFi.RSSI());
            Serial.printf ("[WIFI] GW:   %s\n", WiFi.gatewayIP().toString().c_str());
            Serial.println("[WIFI] ================================");
            Serial.println();

            start_mdns();
        }
        return;
    }

    // Not connected — check if we need to retry
    wifi_connected_at = 0;

    unsigned long now = millis();

    // Initial connection still in progress?
    if (wifi_connect_start > 0 &&
        now - wifi_connect_start < WIFI_CONNECT_TIMEOUT_MS) {
        return;   // still waiting on first attempt
    }

    // Time to retry
    if (now - wifi_last_attempt >= WIFI_RETRY_INTERVAL_MS) {
        Serial.printf("[WIFI] retry (status=%d)\n", status);
        WiFi.disconnect();
        delay(100);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        wifi_last_attempt = now;
    }
}

// ------------------------------------------------------------
//  Status queries
// ------------------------------------------------------------
bool wifi_connected() {
    return WiFi.status() == WL_CONNECTED;
}

String wifi_ip() {
    if (!wifi_connected()) return "0.0.0.0";
    return WiFi.localIP().toString();
}

int wifi_rssi() {
    if (!wifi_connected()) return 0;
    return WiFi.RSSI();
}

String wifi_ssid_connected() {
    if (!wifi_connected()) return "";
    return WiFi.SSID();
}

String wifi_mdns_name() {
    return String(MDNS_HOSTNAME) + ".local";
}

unsigned long wifi_uptime_ms() {
    if (!wifi_connected() || wifi_connected_at == 0) return 0;
    return millis() - wifi_connected_at;
}