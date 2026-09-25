#include "Logging.h"
#include "Config.h"
#include "DisplayManager.h"

#include <LittleFS.h>
#include <time.h>
#include <sys/time.h>

// ============================================================
//  Logging — implementation
// ============================================================

static unsigned long last_full_beep = 0;
static bool          warned_full    = false;

// ------------------------------------------------------------
//  Time string — uses RTC directly, no getLocalTime() timeout
// ------------------------------------------------------------
String log_time_string() {
    time_t now = time(nullptr);
    if (now < 1700000000UL) {
        // No valid time yet — fallback to uptime
        char buf[24];
        snprintf(buf, sizeof(buf), "uptime:%lu", millis() / 1000);
        return String(buf);
    }

    struct tm timeinfo;
    localtime_r(&now, &timeinfo);

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

// ------------------------------------------------------------
void log_init() {
    if (!LittleFS.begin(true)) {
        Serial.println("[LOG] LittleFS mount FAILED");
        return;
    }

    Serial.printf("[LOG] LittleFS mounted  used=%u/%u bytes\n",
                  (unsigned)LittleFS.usedBytes(),
                  (unsigned)LittleFS.totalBytes());

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
void log_write(float temp, float mb, int boost, int rpm, int alarm, int bench) {
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
size_t log_get_size() {
    if (!LittleFS.exists("/log.csv")) return 0;
    File f = LittleFS.open("/log.csv", "r");
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
    if (!log_is_full()) {
        if (warned_full) {
            Serial.println("[LOG] cleared — logging resumed");
            warned_full = false;
        }
        return;
    }

    if (!warned_full) {
        warned_full = true;
        Serial.println("[LOG] FULL — waiting for operator");
    }

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

        Serial.println("[LOG] FULL — beep beep");
    }
}

// ------------------------------------------------------------
void log_clear() {
    if (LittleFS.exists("/log.csv")) {
        LittleFS.remove("/log.csv");
    }

    File f = LittleFS.open("/log.csv", "w");
    if (f) {
        f.println("time,mb,temp,boost,rpm,alarm,bench");
        f.close();
    }

    warned_full    = false;
    last_full_beep = 0;

    Serial.println("[LOG] cleared by operator");
}