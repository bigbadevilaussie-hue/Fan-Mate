#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>

// ============================================================
//  Fan-Mate runtime configuration
//  V3.73 — schema:
//    temp  : warning/panic/kill/hysteresis
//    boost : mode + normal/aggr profiles (nested)
//    night : start/end/nightMax
//    phone : mode
// ============================================================

struct BoostProfile {
    int threshold;   // KB/s
    int on_hold;     // ticks over threshold to bump gear
    int off_hold;    // ticks under threshold to drop gear
};

struct FanMateConfig {
    // Heat control (four gear thresholds, 30/32/34/36 by default)
    float   tempGear1;   // Warm     -> gear 1
    float   tempGear2;   // Hot      -> gear 2
    float   tempGear3;   // Hotter   -> gear 3
    float   tempGear4;   // Critical -> gear 4 + kill
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