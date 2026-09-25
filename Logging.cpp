#include "Logging.h"
#include "Config.h"
#include "DisplayManager.h"

#include <LittleFS.h>
#include <time.h>

// ============================================================
//  Logging — implementation
// ============================================================

static unsigned long last_full_beep = 0;
static bool          warned_full    = false;

// ------------------------------------------------------------
//  Time string — real time if synced, else uptime
// ------------------------------------------------------------
String log_time_string() {
    struct tm timeinfo;
    if (getLocalTime(&timeinfo, 10)) {
        char buf[24];
        snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d",
                 timeinfo.tm_year + 1900,
                 timeinfo.tm_mon + 1,
                 timeinfo.tm_mday,
                 timeinfo.tm_hour,
                 timeinfo.tm_min,
                 timeinfo.tm_sec);
        return String(buf);
    }

    // Fallback: uptime
    char buf[24];
    snprintf(buf, sizeof(buf), "uptime:%lu", millis() / 1000);
    return String(buf);
}

// ------------------------------------------------------------
//  Init — mount LittleFS
// ------------------------------------------------------------
void log_init() {
    if (!LittleFS.begin(true)) {
        Serial.println("[LOG] LittleFS mount FAILED");
        return;
    }

    Serial.printf("[LOG] LittleFS mounted  used=%u/%u bytes\n",
                  (unsigned)LittleFS.usedBytes(),
                  (unsigned)LittleFS.totalBytes());

    // Create file with header if missing
    if (!LittleFS.exists("/log.csv")) {
        File f = LittleFS.open("/log.csv", "w");
        if (f) {
            f.println("time,mb,temp,boost,rpm,alarm,bench");
            f.close();
            Serial.println("[LOG] created /log.csv with header");
        }
    }
}

// ------------------------------------------------------------
//  Write one line
// ------------------------------------------------------------
void log_write(float temp, float mb, int boost, int rpm, int alarm, int bench) {
    // Logging is permanent — never turned off.
    // If file is full, stop writing (beeps continue via log_check_full).

    if (log_is_full()) {
        return;
    }

    File f = LittleFS.open("/log.csv", "a");
    if (!f) {
        Serial.println("[LOG] open for append failed");
        return;
    }

    String t = log_time_string();
    f.printf("%s,%.2f,%.1f,%d,%d,%d,%d\n",
             t.c_str(),
             mb,
             temp,
             boost,
             rpm,
             alarm,
             bench);

    f.close();
}

// ------------------------------------------------------------
//  Size
// ------------------------------------------------------------
size_t log_get_size() {
    if (!LittleFS.exists("/log.csv")) return 0;
    File f = LittleFS.open("/log.csv", "r");
    if (!f) return 0;
    size_t sz = f.size();
    f.close();
    return sz;
}

// ------------------------------------------------------------
//  Full?
// ------------------------------------------------------------
bool log_is_full() {
    return log_get_size() >= LOG_MAX_SIZE;
}

// ------------------------------------------------------------
//  Full check — beeps every 60s, drives OLED warning
// ------------------------------------------------------------
void log_check_full() {
    if (!log_is_full()) {
        // Cleared? Reset warning state.
        if (warned_full) {
            Serial.println("[LOG] cleared — logging resumed");
            warned_full = false;
        }
        return;
    }

    // First time hitting full
    if (!warned_full) {
        warned_full = true;
        Serial.println("[LOG] FULL — waiting for operator");
    }

    // Beep beep every 60s
    unsigned long now = millis();
    if (now - last_full_beep >= 60000) {
        last_full_beep = now;
        // Two short beeps
        ledcWriteTone(BUZZER_CHANNEL, BUZZER_FREQ);
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
        Serial.println("[LOG] FULL — beep beep");
    }
}

// ------------------------------------------------------------
//  Clear — called from HTTP /log/clear
// ------------------------------------------------------------
void log_clear() {
    if (LittleFS.exists("/log.csv")) {
        LittleFS.remove("/log.csv");
    }

    // Recreate with header
    File f = LittleFS.open("/log.csv", "w");
    if (f) {
        f.println("time,mb,temp,boost,rpm,alarm,bench");
        f.close();
    }

    warned_full    = false;
    last_full_beep = 0;

    Serial.println("[LOG] cleared by operator");
}