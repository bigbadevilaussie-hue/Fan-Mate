#ifndef SETTINGS_H
#define SETTINGS_H

#include <Arduino.h>

struct BoostProfile {
    int threshold;
    int on_hold;
    int off_hold;
};

struct FanMateConfig {
    String alarmMode;
    float  alarmWarning;
    float  alarmPanic;
    float  alarmKill;

    String nightMode;
    int    nightStart;
    int    nightEnd;
    int    nightMax;

    String phoneMode;
    int    phoneTestDelay;

    int    boostMode;
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
