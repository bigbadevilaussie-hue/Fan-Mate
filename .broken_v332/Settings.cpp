#include "Settings.h"
#include "Config.h"

#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>

FanMateConfig config;
static Preferences prefs;

static void set_defaults() {
    config.alarmMode    = "auto";
    config.alarmWarning = 45.0;
    config.alarmPanic   = 50.0;
    config.alarmKill    = 55.0;

    config.nightMode    = "auto";
    config.nightStart   = 22;
    config.nightEnd     = 7;
    config.nightMax     = 75;

    config.phoneMode       = "off";
    config.phoneTestDelay  = 0;

    config.boostMode = 1;
    config.boostNormal.threshold = 768;
    config.boostNormal.on_hold   = 4;
    config.boostNormal.off_hold  = 4;
    config.boostAggr.threshold = 256;
    config.boostAggr.on_hold   = 2;
    config.boostAggr.off_hold  = 8;
}

void settings_load() {
    set_defaults();
    prefs.begin("fanmate", true);

    config.alarmMode    = prefs.getString("alarm.mode",    config.alarmMode);
    config.alarmWarning = prefs.getFloat ("alarm.warning", config.alarmWarning);
    config.alarmPanic   = prefs.getFloat ("alarm.panic",   config.alarmPanic);
    config.alarmKill    = prefs.getFloat ("alarm.kill",    config.alarmKill);

    config.nightMode    = prefs.getString("night.mode",    config.nightMode);
    config.nightStart   = prefs.getInt   ("night.start",   config.nightStart);
    config.nightEnd     = prefs.getInt   ("night.end",     config.nightEnd);
    config.nightMax     = prefs.getInt   ("night.max",     config.nightMax);

    config.phoneMode      = prefs.getString("phone.mode",       config.phoneMode);
    config.phoneTestDelay = prefs.getInt   ("phone.test_delay", config.phoneTestDelay);

    config.boostMode = prefs.getInt("boost.mode", config.boostMode);

    config.boostNormal.threshold = prefs.getInt("boost.normal.threshold", config.boostNormal.threshold);
    config.boostNormal.on_hold   = prefs.getInt("boost.normal.on_hold",   config.boostNormal.on_hold);
    config.boostNormal.off_hold  = prefs.getInt("boost.normal.off_hold",  config.boostNormal.off_hold);

    config.boostAggr.threshold = prefs.getInt("boost.aggr.threshold", config.boostAggr.threshold);
    config.boostAggr.on_hold   = prefs.getInt("boost.aggr.on_hold",   config.boostAggr.on_hold);
    config.boostAggr.off_hold  = prefs.getInt("boost.aggr.off_hold",  config.boostAggr.off_hold);

    prefs.end();

    Serial.println("[CFG] loaded:");
    Serial.printf("  alarm warn=%.1f panic=%.1f kill=%.1f\n",
                  config.alarmWarning, config.alarmPanic, config.alarmKill);
    Serial.printf("  phone.mode=%s test_delay=%d\n",
                  config.phoneMode.c_str(), config.phoneTestDelay);
    Serial.printf("  boost.mode=%d normal(%d/%d/%d) aggr(%d/%d/%d)\n",
                  config.boostMode,
                  config.boostNormal.threshold, config.boostNormal.on_hold, config.boostNormal.off_hold,
                  config.boostAggr.threshold, config.boostAggr.on_hold, config.boostAggr.off_hold);
}

void settings_save() {
    prefs.begin("fanmate", false);

    prefs.putString("alarm.mode",    config.alarmMode);
    prefs.putFloat ("alarm.warning", config.alarmWarning);
    prefs.putFloat ("alarm.panic",   config.alarmPanic);
    prefs.putFloat ("alarm.kill",    config.alarmKill);

    prefs.putString("night.mode",    config.nightMode);
    prefs.putInt   ("night.start",   config.nightStart);
    prefs.putInt   ("night.end",     config.nightEnd);
    prefs.putInt   ("night.max",     config.nightMax);

    prefs.putString("phone.mode",       config.phoneMode);
    prefs.putInt   ("phone.test_delay", config.phoneTestDelay);

    prefs.putInt("boost.mode", config.boostMode);
    prefs.putInt("boost.normal.threshold", config.boostNormal.threshold);
    prefs.putInt("boost.normal.on_hold",   config.boostNormal.on_hold);
    prefs.putInt("boost.normal.off_hold",  config.boostNormal.off_hold);
    prefs.putInt("boost.aggr.threshold", config.boostAggr.threshold);
    prefs.putInt("boost.aggr.on_hold",   config.boostAggr.on_hold);
    prefs.putInt("boost.aggr.off_hold",  config.boostAggr.off_hold);

    prefs.end();
    Serial.println("[CFG] saved");
}

void settings_reset() {
    prefs.begin("fanmate", false);
    prefs.clear();
    prefs.end();
    set_defaults();
    Serial.println("[CFG] reset");
}

void settings_apply_json(const char* json) {
    StaticJsonDocument<2048> doc;
    DeserializationError err = deserializeJson(doc, json);
    if (err) { Serial.printf("[CFG] JSON fail: %s\n", err.c_str()); return; }

    if (doc.containsKey("reset")) { settings_reset(); return; }

    if (doc.containsKey("alarm")) {
        JsonObject a = doc["alarm"];
        if (a.containsKey("mode"))    config.alarmMode    = a["mode"].as<String>();
        if (a.containsKey("warning")) config.alarmWarning = a["warning"].as<float>();
        if (a.containsKey("panic"))   config.alarmPanic   = a["panic"].as<float>();
        if (a.containsKey("kill"))    config.alarmKill    = a["kill"].as<float>();
    }

    if (doc.containsKey("night")) {
        JsonObject n = doc["night"];
        if (n.containsKey("mode"))     config.nightMode  = n["mode"].as<String>();
        if (n.containsKey("start"))    config.nightStart = n["start"].as<int>();
        if (n.containsKey("end"))      config.nightEnd   = n["end"].as<int>();
        if (n.containsKey("nightMax")) config.nightMax   = n["nightMax"].as<int>();
    }

    if (doc.containsKey("phone")) {
        JsonObject p = doc["phone"];
        if (p.containsKey("mode"))       config.phoneMode      = p["mode"].as<String>();
        if (p.containsKey("test_delay")) config.phoneTestDelay = p["test_delay"].as<int>();
    }

    if (doc.containsKey("boost")) {
        JsonObject b = doc["boost"];
        if (b.containsKey("mode")) config.boostMode = b["mode"].as<int>();
        if (b.containsKey("normal")) {
            JsonObject n = b["normal"];
            if (n.containsKey("threshold")) config.boostNormal.threshold = n["threshold"].as<int>();
            if (n.containsKey("on_hold"))   config.boostNormal.on_hold   = n["on_hold"].as<int>();
            if (n.containsKey("off_hold"))  config.boostNormal.off_hold  = n["off_hold"].as<int>();
        }
        if (b.containsKey("aggr")) {
            JsonObject a = b["aggr"];
            if (a.containsKey("threshold")) config.boostAggr.threshold = a["threshold"].as<int>();
            if (a.containsKey("on_hold"))   config.boostAggr.on_hold   = a["on_hold"].as<int>();
            if (a.containsKey("off_hold"))  config.boostAggr.off_hold  = a["off_hold"].as<int>();
        }
    }

    settings_save();
}

bool settings_is_night() {
    if (config.nightMode == "off") return false;
    if (config.nightMode == "on")  return true;
    struct tm ti;
    if (!getLocalTime(&ti, 10)) return false;
    int h = ti.tm_hour;
    if (config.nightStart < config.nightEnd)
        return (h >= config.nightStart && h < config.nightEnd);
    return (h >= config.nightStart || h < config.nightEnd);
}
