#include "WiFiManager.h"
#include "Config.h"
#include "SerialBuffer.h"

#include <WiFi.h>
#include <ESPmDNS.h>
#include <time.h>
#include <HTTPClient.h>
#include <sys/time.h>

static bool          wifi_inited        = false;
static unsigned long wifi_connect_start = 0;
static unsigned long wifi_last_attempt  = 0;
static unsigned long wifi_connected_at  = 0;
static bool          mdns_started       = false;
static bool          ntp_started        = false;

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

static void start_mdns() {
    if (mdns_started) return;
    if (!MDNS.begin(MDNS_HOSTNAME)) {
        Serial.println("[MDNS] ERROR");
        return;
    }
    MDNS.addService("http", "tcp", HTTP_PORT);
    log_print("[MDNS] http://%s.local\n", MDNS_HOSTNAME);
    mdns_started = true;
}

static bool          _clock_synced_flag = false;
static unsigned long _last_clock_sync   = (unsigned long)-CLOCK_SYNC_INTERVAL_MS;
static const char* MONTHS[] = {"Jan","Feb","Mar","Apr","May","Jun",
                               "Jul","Aug","Sep","Oct","Nov","Dec"};

// Howard Hinnant days_from_civil
static long _days_from_civil(int y, int m, int d) {
    y -= m <= 2;
    long era = (y >= 0 ? y : y - 399) / 400;
    unsigned yoe = (unsigned)(y - era * 400);
    unsigned doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1;
    unsigned doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    return era * 146097 + (long)doe - 719468;
}

// Parse "Tue, 06 Oct 2026 08:00:25 GMT" -> epoch, or 0 on failure
static time_t _parse_http_date(const char* s) {
    if (!s) return 0;
    int day, year, hh, mm, ss;
    char mon[4] = {0};
    // skip weekday
    const char* p = strchr(s, ',');
    if (!p) return 0;
    p++;
    while (*p == ' ') p++;
    if (sscanf(p, "%d %3s %d %d:%d:%d", &day, mon, &year, &hh, &mm, &ss) != 6)
        return 0;
    int m = 0;
    for (int i = 0; i < 12; i++) {
        if (strncmp(mon, MONTHS[i], 3) == 0) { m = i + 1; break; }
    }
    if (m == 0) return 0;
    long days = _days_from_civil(year, m, day);
    return (time_t)days * 86400L + hh * 3600L + mm * 60L + ss;
}

void clock_sync() {
    if (WiFi.status() != WL_CONNECTED) return;
    if (millis() - _last_clock_sync < CLOCK_SYNC_INTERVAL_MS) return;
    _last_clock_sync = millis();

    IPAddress gw = WiFi.gatewayIP();
    char url[32];
    snprintf(url, sizeof(url), "http://%u.%u.%u.%u/",
             gw[0], gw[1], gw[2], gw[3]);

    log_print("[CLOCK] querying %s\n", url);

    HTTPClient http;
    http.setTimeout(CLOCK_HTTP_TIMEOUT_MS);
    if (!http.begin(url)) {
        log_print("[CLOCK] http.begin failed\n");
        return;
    }
    const char* hdrs[] = {"Date"};
    http.collectHeaders(hdrs, 1);
    int code = http.GET();
    log_print("[CLOCK] HTTP %d\n", code);
    if (code != 200) {
        http.end();
        return;
    }
    String dateHdr = http.header("Date");
    http.end();

    time_t epoch = _parse_http_date(dateHdr.c_str());
    if (epoch < 1700000000UL) {
        log_print("[CLOCK] bad Date: %s\n", dateHdr.c_str());
        return;
    }

    struct timeval tv;
    tv.tv_sec  = epoch;
    tv.tv_usec = 0;
    settimeofday(&tv, nullptr);
    setenv("TZ", "AEST-10", 1);
    tzset();

    _clock_synced_flag = true;
    log_print("[CLOCK] %s -> %lu\n", dateHdr.c_str(), (unsigned long)epoch);
}

bool clock_synced() { return _clock_synced_flag; }
bool ntp_synced()   { return _clock_synced_flag; }

void wifi_loop() {
    if (!wifi_inited) return;

    wl_status_t status = WiFi.status();

    if (status == WL_CONNECTED) {
        if (wifi_connected_at == 0) {
            wifi_connected_at = millis();
            log_print("[WIFI] CONNECTED\n");
            log_print("[WIFI] IP:   %s\n", WiFi.localIP().toString().c_str());
            log_print("[WIFI] RSSI: %d dBm\n", WiFi.RSSI());
            start_mdns();
            clock_sync();
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

bool wifi_connected()           { return WiFi.status() == WL_CONNECTED; }
String wifi_ip()                { return wifi_connected() ? WiFi.localIP().toString() : "0.0.0.0"; }
int wifi_rssi()                 { return wifi_connected() ? WiFi.RSSI() : 0; }
String wifi_ssid_connected()    { return wifi_connected() ? WiFi.SSID() : ""; }
String wifi_mdns_name()         { return String(MDNS_HOSTNAME) + ".local"; }
unsigned long wifi_uptime_ms()  { return wifi_connected() ? millis() - wifi_connected_at : 0; }