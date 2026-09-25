#include "Settings.h"
#include "Config.h"

#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>

FanMateConfig config;
static Preferences prefs;

static void set_defaults() {
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

    config.boostEnabled   = true;
    config.boostThreshold = BOOST_DEFAULT_THRESHOLD_KBPS;
    config.boostHold      = BOOST_DEFAULT_HOLD_SEC;

    config.benchMode    = false;
}

void settings_load() {
    set_defaults();

    prefs.begin("fanmate", true);

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

    config.boostEnabled   = prefs.getBool("boost.enabled",   config.boostEnabled);
    config.boostThreshold = prefs.getInt ("boost.threshold", config.boostThreshold);
    config.boostHold      = prefs.getInt ("boost.hold",      config.boostHold);

    config.benchMode      = prefs.getBool("bench.mode",      config.benchMode);

    prefs.end();

    Serial.println("[CFG] loaded:");
    Serial.printf("  fan tempOn=%.1f tempFull=%.1f nightMax=%d%%\n",
                  config.tempOn, config.tempFull, config.nightMax);
    Serial.printf("  alarm.mode=%s warn=%.1f panic=%.1f\n",
                  config.alarmMode.c_str(),
                  config.alarmWarning, config.alarmPanic);
    Serial.printf("  night.mode=%s %02d:00-%02d:00\n",
                  config.nightMode.c_str(),
                  config.nightStart, config.nightEnd);
    Serial.printf("  phone.mode=%s bench=%d\n",
                  config.phoneMode.c_str(), config.benchMode ? 1 : 0);
    Serial.printf("  boost=%d threshold=%d hold=%d\n",
                  config.boostEnabled ? 1 : 0,
                  config.boostThreshold, config.boostHold);
}

void settings_save() {
    prefs.begin("fanmate", false);

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

    prefs.putBool  ("boost.enabled",   config.boostEnabled);
    prefs.putInt   ("boost.threshold", config.boostThreshold);
    prefs.putInt   ("boost.hold",      config.boostHold);

    prefs.putBool  ("bench.mode",      config.benchMode);

    prefs.end();
    Serial.println("[CFG] saved to NVS");
}

void settings_reset() {
    prefs.begin("fanmate", false);
    prefs.clear();
    prefs.end();

    set_defaults();
    Serial.println("[CFG] reset to defaults");
}

void settings_apply_json(const char* json) {
    StaticJsonDocument<1024> doc;
    DeserializationError err = deserializeJson(doc, json);
    if (err) {
        Serial.printf("[CFG] JSON parse failed: %s\n", err.c_str());
        return;
    }

    if (doc.containsKey("reset") && doc["reset"].as<bool>()) {
        settings_reset();
        return;
    }

    if (doc.containsKey("fan")) {
        JsonObject fan = doc["fan"];
        if (fan.containsKey("tempOn"))   config.tempOn   = fan["tempOn"].as<float>();
        if (fan.containsKey("tempFull")) config.tempFull = fan["tempFull"].as<float>();
        if (fan.containsKey("nightMax")) config.nightMax = fan["nightMax"].as<int>();
    }

    if (doc.containsKey("alarm")) {
        JsonObject a = doc["alarm"];
        if (a.containsKey("mode"))    config.alarmMode    = a["mode"].as<String>();
        if (a.containsKey("warning")) config.alarmWarning = a["warning"].as<float>();
        if (a.containsKey("panic"))   config.alarmPanic   = a["panic"].as<float>();
    }

    if (doc.containsKey("night")) {
        JsonObject n = doc["night"];
        if (n.containsKey("mode"))  config.nightMode  = n["mode"].as<String>();
        if (n.containsKey("start")) config.nightStart = n["start"].as<int>();
        if (n.containsKey("end"))   config.nightEnd   = n["end"].as<int>();
    }

    if (doc.containsKey("phone")) {
        JsonObject p = doc["phone"];
        if (p.containsKey("mode")) config.phoneMode = p["mode"].as<String>();
    }

    if (doc.containsKey("boost")) {
        JsonObject b = doc["boost"];
        if (b.containsKey("enabled"))   config.boostEnabled   = b["enabled"].as<bool>();
        if (b.containsKey("threshold")) config.boostThreshold = b["threshold"].as<int>();
        if (b.containsKey("hold"))      config.boostHold      = b["hold"].as<int>();
    }

    if (doc.containsKey("bench")) {
        JsonObject b = doc["bench"];
        if (b.containsKey("mode")) config.benchMode = b["mode"].as<bool>();
    }

    settings_save();
    Serial.println("[CFG] applied + saved");
}

bool settings_is_night() {
    if (config.nightMode == "off") return false;
    if (config.nightMode == "on")  return true;

    struct tm timeinfo;
    if (!getLocalTime(&timeinfo, 10)) return false;

    int hour  = timeinfo.tm_hour;
    int start = config.nightStart;
    int end   = config.nightEnd;

    if (start < end) {
        return (hour >= start && hour < end);
    } else {
        return (hour >= start || hour < end);
    }
}