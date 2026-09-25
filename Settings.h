#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>

// ============================================================
//  Fan-Mate runtime configuration
//
//  Loaded from NVS on boot (falls back to defaults if NVS empty)
//  Updated over BLE via CONFIG_UUID characteristic
//  Saved to NVS on every change
// ============================================================

struct FanMateConfig {
    // Fan
    String  fanMode;        // "off" / "on" / "auto"
    float   tempOn;         // °C — fan starts here
    float   tempFull;       // °C — fan hits 100%
    int     nightMax;       // % 0–100 — fan cap during night

    // Alarm
    String  alarmMode;      // "off" / "on" / "auto"
    float   alarmWarning;   // °C
    float   alarmPanic;     // °C

    // Night
    String  nightMode;      // "off" / "on" / "auto"
    int     nightStart;     // hour 0–23
    int     nightEnd;       // hour 0–23

    // Phone
    String  phoneMode;      // "off" / "auto"
};

extern FanMateConfig config;

// Called in setup() — before initBLE()
void settings_load();

// Writes all config values to NVS
void settings_save();

// Wipes NVS + restores defaults
void settings_reset();

// Parses JSON from BLE and applies + saves
void settings_apply_json(const char* json);

// True if current time is within night window
bool settings_is_night();

#endif