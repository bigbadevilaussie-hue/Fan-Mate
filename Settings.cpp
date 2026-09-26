#include "Settings.h"
#include "Config.h"

#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>

FanMateConfig config;
static Preferences prefs;

static void set_defaults() {
    config.tempWarning    = 32.0;
    config.tempPanic      = 34.0;
    config.tempKill       = 36.0;
    config.tempHysteresis = 1.0;

    config.nightStart   = 22;
    config.nightEnd     = 7;
    config.nightMax     = 75;

    config.phoneMode    = "off";

    config.boostMode = 1;   // Normal

    config.boostNormal.threshold = 700;
    config.boostNormal.on_hold   = 4;
    config.boostNormal.off_hold  = 4;

    config.boostAggr.threshold = 400;
    config.boostAggr.on_hold   = 2;
    config.boostAggr.off_hold  = 8;
}

void settings_load() {
    set_defaults();
    prefs.begin("fanmate", true);

    config.tempWarning    = prefs.getFloat("temp.warning",     config.tempWarning);
    config.tempPanic      = prefs.getFloat("temp.panic",       config.tempPanic);
    config.tempKill       = prefs.getFloat("temp.kill",        config.tempKill);
    config.tempHysteresis = prefs.getFloat("temp.hysteresis",  config.tempHysteresis);

    config.nightStart     = prefs.getInt  ("night.start",      config.nightStart);
    config.nightEnd       = prefs.getInt  ("night.end",        config.nightEnd);
    config.nightMax       = prefs.getInt  ("night.max",        config.nightMax);

    config.phoneMode      = prefs.getString("phone.mode",      config.phoneMode);

    config.boostMode      = prefs.getInt("boost.mode",         config.boostMode);

    config.boostNormal.threshold = prefs.getInt("boost.normal.threshold", config.boostNormal.threshold);
    config.boostNormal.on_hold   = prefs.getInt("boost.normal.on_hold",   config.boostNormal.on_hold);
    config.boostNormal.off_hold  = prefs.getInt("boost.normal.off_hold",  config.boostNormal.off_hold);

    config.boostAggr.threshold = prefs.getInt("boost.aggr.threshold", config.boostAggr.threshold);
    config.boostAggr.on_hold   = prefs.getInt("boost.aggr.on_hold",   config.boostAggr.on_hold);
    config.boostAggr.off_hold  = prefs.getInt("boost.aggr.off_hold",  config.boostAggr.off_hold);

    prefs.end();

    Serial.println("[CFG] loaded:");
    Serial.printf("  temp warn=%.1f panic=%.1f kill=%.1f hyst=%.1f\n",
                  config.tempWarning, config.tempPanic, config.tempKill, config.tempHysteresis);
    Serial.printf("  night %02d:00-%02d:00 max=%d%%\n",
                  config.nightStart, config.nightEnd, config.nightMax);
    Serial.printf("  phone.mode=%s\n", config.phoneMode.c_str());
    const char* bm = (config.boostMode == 0) ? "off"
                   : (config.boostMode == 2) ? "aggr" : "normal";
    Serial.printf("  boost.mode=%s normal(%d/%d) aggr(%d/%d)\n", bm,
                  config.boostNormal.threshold, config.boostNormal.on_hold,
                  config.boostAggr.threshold, config.boostAggr.on_hold);
}

void settings_save() {
    prefs.begin("fanmate", false);

    prefs.putFloat("temp.warning",     config.tempWarning);
    prefs.putFloat("temp.panic",       config.tempPanic);
    prefs.putFloat("temp.kill",        config.tempKill);
    prefs.putFloat("temp.hysteresis",  config.tempHysteresis);

    prefs.putInt  ("night.start",      config.nightStart);
    prefs.putInt  ("night.end",        config.nightEnd);
    prefs.putInt  ("night.max",        config.nightMax);

    prefs.putString("phone.mode",      config.phoneMode);

    prefs.putInt("boost.mode",             config.boostMode);
    prefs.putInt("boost.normal.threshold", config.boostNormal.threshold);
    prefs.putInt("boost.normal.on_hold",   config.boostNormal.on_hold);
    prefs.putInt("boost.normal.off_hold",  config.boostNormal.off_hold);
    prefs.putInt("boost.aggr.threshold",   config.boostAggr.threshold);
    prefs.putInt("boost.aggr.on_hold",     config.boostAggr.on_hold);
    prefs.putInt("boost.aggr.off_hold",    config.boostAggr.off_hold);

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

    if (doc.containsKey("temp")) {
        JsonObject t = doc["temp"];
        if (t.containsKey("warning"))    config.tempWarning    = t["warning"].as<float>();
        if (t.containsKey("panic"))      config.tempPanic      = t["panic"].as<float>();
        if (t.containsKey("kill"))       config.tempKill       = t["kill"].as<float>();
        if (t.containsKey("hysteresis")) config.tempHysteresis = t["hysteresis"].as<float>();
    }

    if (doc.containsKey("night")) {
        JsonObject n = doc["night"];
        if (n.containsKey("start"))    config.nightStart = n["start"].as<int>();
        if (n.containsKey("end"))      config.nightEnd   = n["end"].as<int>();
        if (n.containsKey("nightMax")) config.nightMax   = n["nightMax"].as<int>();
    }

    if (doc.containsKey("phone")) {
        JsonObject p = doc["phone"];
        if (p.containsKey("mode")) config.phoneMode = p["mode"].as<String>();
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
    Serial.println("[CFG] applied + saved");
}

bool settings_is_night() {
    struct tm ti;
    if (!getLocalTime(&ti, 10)) return false;
    int h = ti.tm_hour;
    if (config.nightStart < config.nightEnd)
        return (h >= config.nightStart && h < config.nightEnd);
    return (h >= config.nightStart || h < config.nightEnd);
}
