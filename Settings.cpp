#include "Settings.h"
#include "Config.h"

#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>

// ============================================================
//  Fan-Mate settings — NVS load/save + JSON parsing
//
//  Defaults live in set_defaults(). NVS overrides them.
//  If NVS is empty, defaults apply.
// ============================================================

FanMateConfig config;
static Preferences prefs;

// ------------------------------------------------------------
//  Defaults (compiled into the .bin)
// ------------------------------------------------------------
static void set_defaults() {
    config.fanMode      = "auto";
    config.tempOn       = 34.0;
    config.tempFull     = 42.0;
    config.nightMax     = 75;

    config.alarmMode    = "auto";
    config.alarmWarning = 45.0;
    config.alarmPanic   = 50.0;

    config.nightMode    = "auto";
    config.nightStart   = 22;
    config.nightEnd     = 7;

    config.phoneMode    = "auto";
}

// ------------------------------------------------------------
//  Load from NVS (called in setup)
// ------------------------------------------------------------
void settings_load() {
    set_defaults();

    prefs.begin("fanmate", true);

    config.fanMode      = prefs.getString("fan.mode",      config.fanMode);
    config.tempOn       = prefs.getFloat ("fan.tempOn",    config.tempOn);
    config.tempFull     = prefs.getFloat ("fan.tempFull",  config.tempFull);
    config.nightMax     = prefs.getInt   ("fan.nightMax",  config.nightMax);

    config.alarmMode    = prefs.getString("alarm.mode",    config.alarmMode);
    config.alarmWarning = prefs.getFloat ("alarm.warning", config.alarmWarning);
    config.alarmPanic   = prefs.getFloat ("alarm.panic",   config.alarmPanic);

    config.nightMode    = prefs.getString("night.mode",    config.nightMode);
    config.nightStart   = prefs.getInt   ("night.start",   config.nightStart);
    config.nightEnd     = prefs.getInt   ("night.end",     config.nightEnd);

    config.phoneMode    = prefs.getString("phone.mode",    config.phoneMode);

    prefs.end();

    Serial.println("[CFG] loaded:");
    Serial.printf("  fan.mode=%s tempOn=%.1f tempFull=%.1f nightMax=%d%%\n",
                  config.fanMode.c_str(),
                  config.tempOn, config.tempFull, config.nightMax);
    Serial.printf("  alarm.mode=%s warn=%.1f panic=%.1f\n",
                  config.alarmMode.c_str(),
                  config.alarmWarning, config.alarmPanic);
    Serial.printf("  night.mode=%s %02d:00-%02d:00\n",
                  config.nightMode.c_str(),
                  config.nightStart, config.nightEnd);
    Serial.printf("  phone.mode=%s\n", config.phoneMode.c_str());
}

// ------------------------------------------------------------
//  Save all values to NVS
// ------------------------------------------------------------
void settings_save() {
    prefs.begin("fanmate", false);

    prefs.putString("fan.mode",      config.fanMode);
    prefs.putFloat ("fan.tempOn",    config.tempOn);
    prefs.putFloat ("fan.tempFull",  config.tempFull);
    prefs.putInt   ("fan.nightMax",  config.nightMax);

    prefs.putString("alarm.mode",    config.alarmMode);
    prefs.putFloat ("alarm.warning", config.alarmWarning);
    prefs.putFloat ("alarm.panic",   config.alarmPanic);

    prefs.putString("night.mode",    config.nightMode);
    prefs.putInt   ("night.start",   config.nightStart);
    prefs.putInt   ("night.end",     config.nightEnd);

    prefs.putString("phone.mode",    config.phoneMode);

    prefs.end();
    Serial.println("[CFG] saved to NVS");
}

// ------------------------------------------------------------
//  Wipe NVS + restore defaults
// ------------------------------------------------------------
void settings_reset() {
    prefs.begin("fanmate", false);
    prefs.clear();
    prefs.end();

    set_defaults();
    Serial.println("[CFG] reset to defaults");
}

// ------------------------------------------------------------
//  Parse JSON from BLE and apply
//
//  Only keys present in the JSON are updated.
//  Everything else keeps its current value.
// ------------------------------------------------------------
void settings_apply_json(const char* json) {
    StaticJsonDocument<512> doc;
    DeserializationError err = deserializeJson(doc, json);
    if (err) {
        Serial.printf("[CFG] JSON parse failed: %s\n", err.c_str());
        return;
    }

    // Special case — full reset
    if (doc.containsKey("reset") && doc["reset"].as<bool>()) {
        settings_reset();
        return;
    }

    // ---- Fan ----
    if (doc.containsKey("fan")) {
        JsonObject fan = doc["fan"];
        if (fan.containsKey("mode"))     config.fanMode  = fan["mode"].as<String>();
        if (fan.containsKey("tempOn"))   config.tempOn   = fan["tempOn"].as<float>();
        if (fan.containsKey("tempFull")) config.tempFull = fan["tempFull"].as<float>();
        if (fan.containsKey("nightMax")) config.nightMax = fan["nightMax"].as<int>();
    }

    // ---- Alarm ----
    if (doc.containsKey("alarm")) {
        JsonObject a = doc["alarm"];
        if (a.containsKey("mode"))    config.alarmMode    = a["mode"].as<String>();
        if (a.containsKey("warning")) config.alarmWarning = a["warning"].as<float>();
        if (a.containsKey("panic"))   config.alarmPanic   = a["panic"].as<float>();
    }

    // ---- Night ----
    if (doc.containsKey("night")) {
        JsonObject n = doc["night"];
        if (n.containsKey("mode"))  config.nightMode  = n["mode"].as<String>();
        if (n.containsKey("start")) config.nightStart = n["start"].as<int>();
        if (n.containsKey("end"))   config.nightEnd   = n["end"].as<int>();
    }

    // ---- Phone ----
    if (doc.containsKey("phone")) {
        JsonObject p = doc["phone"];
        if (p.containsKey("mode")) config.phoneMode = p["mode"].as<String>();
    }

    settings_save();
    Serial.println("[CFG] applied + saved");
}

// ------------------------------------------------------------
//  Is it currently night?
// ------------------------------------------------------------
bool settings_is_night() {
    if (config.nightMode == "off") return false;
    if (config.nightMode == "on")  return true;

    // auto — check hour
    struct tm timeinfo;
    if (!getLocalTime(&timeinfo, 10)) {
        // no time yet — assume day
        return false;
    }

    int hour = timeinfo.tm_hour;
    int start = config.nightStart;
    int end   = config.nightEnd;

    if (start < end) {
        // e.g. 2:00 → 7:00 — same day
        return (hour >= start && hour < end);
    } else {
        // e.g. 22:00 → 7:00 — wraps midnight
        return (hour >= start || hour < end);
    }
}