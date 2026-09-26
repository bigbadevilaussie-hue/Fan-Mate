#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>

// ============================================================
//  Fan-Mate runtime configuration
//  V3.46 — new schema:
//    temp  : warning/panic/kill (no mode, always on)
//    boost : mode + normal/aggr profiles (nested)
//    night : always on, start/end/nightMax
//    phone : mode only (no test_delay)
// ============================================================

struct BoostProfile {
    int threshold;   // KB/s
    int on_hold;     // ticks over threshold to bump gear
    int off_hold;    // unused now; kept for compat
};

struct FanMateConfig {
    // Heat control
    float   tempWarning;
    float   tempPanic;
    float   tempKill;
    float   tempHysteresis;

    // Night
    int     nightStart;
    int     nightEnd;
    int     nightMax;

    // Phone
    String  phoneMode;      // "off" / "auto"

    // Boost
    int     boostMode;      // 0=off, 1=normal, 2=aggr
    BoostProfile boostNormal;
    BoostProfile boostAggr;
};

extern FanMateConfig config;

void settings_load();
void settings_save();
void settings_reset();
void settings_apply_json(const char* json);
bool settings_is_night();

#endif
