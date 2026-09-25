#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>

// ============================================================
//  Fan-Mate runtime configuration
//
//  V2.24 — fan.mode removed. Auto Boost is the mode.
// ============================================================

struct FanMateConfig {
    // Fan
    float   tempOn;         // °C
    float   tempFull;       // °C
    int     nightMax;       // % 0-100

    // Alarm
    String  alarmMode;      // "off" / "on" / "auto"
    float   alarmWarning;   // °C
    float   alarmPanic;     // °C

    // Night
    String  nightMode;      // "off" / "on" / "auto"
    int     nightStart;     // hour 0-23
    int     nightEnd;       // hour 0-23

    // Phone
    String  phoneMode;      // "off" / "auto"

    // Boost
    bool    boostEnabled;
    int     boostThreshold; // KB/s
    int     boostHold;      // ticks

    // Bench
    bool    benchMode;      // force phone = 1
};

extern FanMateConfig config;

void settings_load();
void settings_save();
void settings_reset();
void settings_apply_json(const char* json);
bool settings_is_night();

#endif