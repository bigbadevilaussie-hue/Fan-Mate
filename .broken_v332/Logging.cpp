#include "Logging.h"
#include "Config.h"

#include <LittleFS.h>
#include <time.h>

// ============================================================
//  Logging — LittleFS CSV log
//  V3.32 — 7 columns + events + flush + 1 MB cap
// ============================================================

static const char* LOG_FILE = "/log.csv";

// ------------------------------------------------------------
static void write_header_if_new() {
    if (LittleFS.exists(LOG_FILE)) return;
    File f = LittleFS.open(LOG_FILE, "w");
    if (!f) return;
    f.println("timestamp,temp_c,net_kbps,boost,fan,rpm,event");
    f.flush();
    f.close();
}

// ------------------------------------------------------------
static void timestamp_str(char* buf, size_t len) {
    time_t now = time(nullptr);
    if (now < 1700000000UL) {
        snprintf(buf, len, "uptime:%lu", (unsigned long)(millis() / 1000));
        return;
    }
    struct tm tm;
    localtime_r(&now, &tm);
    snprintf(buf, len, "%04d-%02d-%02d %02d:%02d:%02d",
             tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
             tm.tm_hour, tm.tm_min, tm.tm_sec);
}

// ------------------------------------------------------------
void log_init() {
    if (!LittleFS.begin(true)) {
        Serial.println("[LOG] LittleFS mount FAILED");
        return;
    }
    write_header_if_new();
    size_t used = LittleFS.usedBytes();
    size_t total = LittleFS.totalBytes();
    Serial.printf("[LOG] LittleFS mounted  used=%u/%u bytes\n",
                  (unsigned)used, (unsigned)total);
}

// ------------------------------------------------------------
void log_write(float temp, float net_kbps, int boost, int fan, int rpm) {
    if (log_is_full()) return;

    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;

    char ts[32];
    timestamp_str(ts, sizeof(ts));

    char line[160];
    snprintf(line, sizeof(line), "%s,%.1f,%.1f,%d,%d,%d,\n",
             ts, temp, net_kbps, boost, fan, rpm);

    f.print(line);
    f.flush();
    f.close();
}

// ------------------------------------------------------------
void log_write_event(const char* event) {
    extern float currentTemp;

    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;

    char ts[32];
    timestamp_str(ts, sizeof(ts));

    char line[160];
    snprintf(line, sizeof(line), "%s,%.1f,0.0,0,0,0,%s\n",
             ts, currentTemp, event);

    f.print(line);
    f.flush();
    f.close();
}

// ------------------------------------------------------------
void log_write_reset_reason() {
    esp_reset_reason_t reason = esp_reset_reason();
    const char* s;
    switch (reason) {
        case ESP_RST_POWERON:  s = "POWERON";  break;
        case ESP_RST_SW:       s = "SOFTWARE"; break;
        case ESP_RST_PANIC:    s = "PANIC";    break;
        case ESP_RST_INT_WDT:  s = "WDT";      break;
        case ESP_RST_TASK_WDT: s = "WDT";      break;
        case ESP_RST_WDT:      s = "WDT";      break;
        case ESP_RST_BROWNOUT: s = "BROWNOUT"; break;
        case ESP_RST_DEEPSLEEP:s = "DEEPSLEEP";break;
        case ESP_RST_SDIO:     s = "SDIO";     break;
        default:               s = "UNKNOWN";  break;
    }
    Serial.printf("[BOOT] reset reason: %s\n", s);
    log_write_event(s);
}

// ------------------------------------------------------------
size_t log_get_size() {
    if (!LittleFS.exists(LOG_FILE)) return 0;
    File f = LittleFS.open(LOG_FILE, "r");
    if (!f) return 0;
    size_t sz = f.size();
    f.close();
    return sz;
}

// ------------------------------------------------------------
bool log_is_full() {
    return log_get_size() >= LOG_MAX_SIZE;
}

// ------------------------------------------------------------
void log_check_full() {
    if (!log_is_full()) return;

    static bool announced = false;
    if (!announced) {
        announced = true;
        log_write_event("LOG_FULL");
        Serial.println("[LOG] FULL — logging stopped");
    }
}

// ------------------------------------------------------------
void log_clear() {
    LittleFS.remove(LOG_FILE);
    write_header_if_new();
    Serial.println("[LOG] cleared");
}

// ------------------------------------------------------------
String log_time_string() {
    char ts[32];
    timestamp_str(ts, sizeof(ts));
    return String(ts);
}