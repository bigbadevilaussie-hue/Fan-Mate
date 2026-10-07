#include "Settings.h"
#include "Config.h"
#include "SerialBuffer.h"
#include "Logging.h"

#include <Preferences.h>
#include <ArduinoJson.h>
#include <time.h>

FanMateConfig config;
static Preferences prefs;

static void set_defaults() {
    config.tempGear1      = 30.0;
    config.tempGear2      = 32.0;
    config.tempGear3      = 34.0;
    config.tempGear4      = 36.0;
    config.tempHysteresis = 1.0;
    config.deltaTrigger   = 5.1;

    config.nightStart   = 22;
    config.nightEnd     = 7;
    config.nightMax     = 75;


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

    config.tempGear1 = prefs.getFloat("temp.gear1",
                        prefs.getFloat("temp.warning", config.tempGear1));
    config.tempGear2 = prefs.getFloat("temp.gear2",
                        prefs.getFloat("temp.panic",   config.tempGear2));
    config.tempGear3 = prefs.getFloat("temp.gear3",
                        prefs.getFloat("temp.kill",    config.tempGear3));
    config.tempGear4 = prefs.getFloat("temp.gear4",
                        prefs.getFloat("temp.kill",    config.tempGear4));
    config.tempHysteresis = prefs.getFloat("t.hyst", config.tempHysteresis);
    config.deltaTrigger   = prefs.getFloat("delta.trigger", config.deltaTrigger);

    config.nightStart     = prefs.getInt  ("night.start",      config.nightStart);
    config.nightEnd       = prefs.getInt  ("night.end",        config.nightEnd);
    config.nightMax       = prefs.getInt  ("night.max",        config.nightMax);


    config.boostMode      = prefs.getInt("boost.mode",         config.boostMode);

    config.boostNormal.threshold = prefs.getInt("b.n.thr", config.boostNormal.threshold);
    config.boostNormal.on_hold   = prefs.getInt("b.n.on",   config.boostNormal.on_hold);
    config.boostNormal.off_hold  = prefs.getInt("b.n.off",  config.boostNormal.off_hold);

    config.boostAggr.threshold = prefs.getInt("b.a.thr", config.boostAggr.threshold);
    config.boostAggr.on_hold   = prefs.getInt("b.a.on",   config.boostAggr.on_hold);
    config.boostAggr.off_hold  = prefs.getInt("b.a.off",  config.boostAggr.off_hold);

    prefs.end();

    Serial.println("[CFG] loaded:");
    Serial.printf("  temp warm=%.1f hot=%.1f hotter=%.1f crit=%.1f hyst=%.1f\n",
                  config.tempGear1, config.tempGear2, config.tempGear3,
                  config.tempGear4, config.tempHysteresis);
    Serial.printf("  night %02d:00-%02d:00 max=%d%%\n",
                  config.nightStart, config.nightEnd, config.nightMax);
    const char* bm = (config.boostMode == 0) ? "off"
                   : (config.boostMode == 2) ? "aggr" : "normal";
    Serial.printf("  boost.mode=%s normal(%d/%d) aggr(%d/%d)\n", bm,
                  config.boostNormal.threshold, config.boostNormal.on_hold,
                  config.boostAggr.threshold, config.boostAggr.on_hold);
}

void settings_save() {
    prefs.begin("fanmate", false);

    prefs.putFloat("temp.gear1",       config.tempGear1);
    prefs.putFloat("temp.gear2",       config.tempGear2);
    prefs.putFloat("temp.gear3",       config.tempGear3);
    prefs.putFloat("temp.gear4",       config.tempGear4);
    prefs.putFloat("t.hyst",  config.tempHysteresis);
    prefs.putFloat("delta.trigger", config.deltaTrigger);

    prefs.putInt  ("night.start",      config.nightStart);
    prefs.putInt  ("night.end",        config.nightEnd);
    prefs.putInt  ("night.max",        config.nightMax);


    prefs.putInt("boost.mode",             config.boostMode);
    prefs.putInt("b.n.thr", config.boostNormal.threshold);
    prefs.putInt("b.n.on",   config.boostNormal.on_hold);
    prefs.putInt("b.n.off",  config.boostNormal.off_hold);
    prefs.putInt("b.a.thr",   config.boostAggr.threshold);
    prefs.putInt("b.a.on",     config.boostAggr.on_hold);
    prefs.putInt("b.a.off",    config.boostAggr.off_hold);

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
        if (t.containsKey("gear1"))      config.tempGear1 = t["gear1"].as<float>();
        else if (t.containsKey("warning")) config.tempGear1 = t["warning"].as<float>();
        if (t.containsKey("gear2"))      config.tempGear2 = t["gear2"].as<float>();
        else if (t.containsKey("panic"))   config.tempGear2 = t["panic"].as<float>();
        if (t.containsKey("gear3"))      config.tempGear3 = t["gear3"].as<float>();
        if (t.containsKey("gear4"))      config.tempGear4 = t["gear4"].as<float>();
        else if (t.containsKey("kill"))    config.tempGear4 = t["kill"].as<float>();
        if (t.containsKey("hysteresis")) config.tempHysteresis = t["hysteresis"].as<float>();
        if (t.containsKey("delta_trigger")) config.deltaTrigger = t["delta_trigger"].as<float>();
    }

    if (doc.containsKey("night")) {
        JsonObject n = doc["night"];
        if (n.containsKey("start"))    config.nightStart = n["start"].as<int>();
        if (n.containsKey("end"))      config.nightEnd   = n["end"].as<int>();
        if (n.containsKey("nightMax")) config.nightMax   = n["nightMax"].as<int>();
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

    log_seal_now();
    log_write_config_snapshot();
    log_write_event("CFG_APPLIED");

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