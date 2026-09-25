#include "WiFiManager.h"
#include "Config.h"

#include <WiFi.h>
#include <ESPmDNS.h>
#include <time.h>
#include <sys/time.h>

// ============================================================
//  WiFi Manager — implementation
//  V3.30 — NTP time sync at boot
// ============================================================

static bool          wifi_inited        = false;
static unsigned long wifi_connect_start = 0;
static unsigned long wifi_last_attempt  = 0;
static unsigned long wifi_connected_at  = 0;
static bool          mdns_started       = false;
static bool          ntp_started        = false;

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
    WiFi.setSleep(true);

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    wifi_connect_start = millis();
    wifi_last_attempt  = millis();
    wifi_inited        = true;

    Serial.printf("[WIFI] connecting...\n");
}

// ------------------------------------------------------------
static void start_mdns() {
    if (mdns_started) return;
    if (!MDNS.begin(MDNS_HOSTNAME)) {
        Serial.println("[MDNS] ERROR");
        return;
    }
    MDNS.addService("http", "tcp", HTTP_PORT);
    Serial.printf("[MDNS] http://%s.local\n", MDNS_HOSTNAME);
    mdns_started = true;
}

// ------------------------------------------------------------
//  NTP — one-shot at first connection
// ------------------------------------------------------------
static void start_ntp() {
    if (ntp_started) return;

    setenv("TZ", "AEST-10", 1);
    tzset();

    configTime(0, 0, "pool.ntp.org", "time.nist.gov", "time.google.com");

    Serial.println("[NTP] sync requested");
    ntp_started = true;
}

// ------------------------------------------------------------
void wifi_loop() {
    if (!wifi_inited) return;

    wl_status_t status = WiFi.status();

    if (status == WL_CONNECTED) {
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
            start_ntp();
        }
        return;
    }

    wifi_connected_at = 0;

    unsigned long now = millis();

    if (wifi_connect_start > 0 &&
        now - wifi_connect_start < WIFI_CONNECT_TIMEOUT_MS) {
        return;
    }

    if (now - wifi_last_attempt >= WIFI_RETRY_INTERVAL_MS) {
        Serial.printf("[WIFI] retry (status=%d)\n", status);
        WiFi.disconnect();
        delay(100);
        WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
        wifi_last_attempt = now;
    }
}

// ------------------------------------------------------------
bool wifi_connected()           { return WiFi.status() == WL_CONNECTED; }
String wifi_ip()                { return wifi_connected() ? WiFi.localIP().toString() : "0.0.0.0"; }
int wifi_rssi()                 { return wifi_connected() ? WiFi.RSSI() : 0; }
String wifi_ssid_connected()    { return wifi_connected() ? WiFi.SSID() : ""; }
String wifi_mdns_name()         { return String(MDNS_HOSTNAME) + ".local"; }
unsigned long wifi_uptime_ms()  { return wifi_connected() ? millis() - wifi_connected_at : 0; }