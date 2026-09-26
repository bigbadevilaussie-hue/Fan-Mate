#include "Logging.h"
#include "Config.h"
#include "DisplayManager.h"

#include <LittleFS.h>
#include <time.h>
#include <sys/time.h>
#include <esp_system.h>

extern float weather_get_temp();

static unsigned long last_full_beep = 0;
static bool          warned_full    = false;
static const char* LOG_FILE = "/log.csv";

String log_time_string() {
    setenv("TZ", "AEST-10", 1);
    tzset();

    time_t now = time(nullptr);
    if (now < 1700000000UL) {
        char buf[24];
        snprintf(buf, sizeof(buf), "uptime:%lu", millis() / 1000);
        return String(buf);
    }
    struct tm ti;
    localtime_r(&now, &ti);
    char buf[24];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d",
             ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday,
             ti.tm_hour, ti.tm_min, ti.tm_sec);
    return String(buf);
}

static void write_header_if_new() {
    if (LittleFS.exists(LOG_FILE)) return;
    File f = LittleFS.open(LOG_FILE, "w");
    if (!f) return;
    f.println("timestamp,temp_c,net_kbps,boost,fan,rpm,event,outdoor_c");
    f.close();
}

void log_init() {
    if (!LittleFS.begin(true)) {
        Serial.println("[LOG] LittleFS mount FAILED");
        return;
    }
    Serial.printf("[LOG] mounted used=%u/%u\n",
                  (unsigned)LittleFS.usedBytes(),
                  (unsigned)LittleFS.totalBytes());
    write_header_if_new();
}

void log_write(float temp, float net_kbps, int boost, int fan, int rpm) {
    if (log_is_full()) return;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    f.printf("%s,%.1f,%.1f,%d,%d,%d,,%.1f\n",
             t.c_str(), temp, net_kbps, boost, fan, rpm,
             weather_get_temp());
    f.close();
}

void log_write_event(const char* event) {
    extern float currentTemp;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    f.printf("%s,%.1f,0.0,0,0,0,%s,\n", t.c_str(), currentTemp, event);
    f.close();
}

void log_write_reset_reason() {
    esp_reset_reason_t r = esp_reset_reason();
    const char* s;
    switch (r) {
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
    Serial.printf("[BOOT] reset: %s\n", s);
    log_write_event(s);
}

size_t log_get_size() {
    if (!LittleFS.exists(LOG_FILE)) return 0;
    File f = LittleFS.open(LOG_FILE, "r");
    if (!f) return 0;
    size_t sz = f.size();
    f.close();
    return sz;
}

bool log_is_full() { return log_get_size() >= LOG_MAX_SIZE; }

void log_check_full() {
    if (!log_is_full()) {
        if (warned_full) { warned_full = false; Serial.println("[LOG] resumed"); }
        return;
    }
    if (!warned_full) { warned_full = true; Serial.println("[LOG] FULL"); }
    unsigned long now = millis();
    if (now - last_full_beep >= 60000) {
        last_full_beep = now;
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
    }
}

void log_clear() {
    if (LittleFS.exists(LOG_FILE)) LittleFS.remove(LOG_FILE);
    write_header_if_new();
    warned_full = false;
    last_full_beep = 0;
    Serial.println("[LOG] cleared");
}
