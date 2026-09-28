#ifndef FAN_CONTROLLER_H
#define FAN_CONTROLLER_H

#include <Arduino.h>

void initHardware();

void readDS18B20(float &currentTemp);
void updatePhoneDetection();
void updateTach();

void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
);

void silenceFanAndAlerts();

// Stall detection — true when fan commanded on but tach reads zero
bool fan_stall_active();


// Kill mode state (v4.00)
// 0 = AUTO (armed)
// 1 = ACTIVE (fired)
// 2 = OFF (user silenced)
int  kill_get_state();
void kill_request_clear();
void kill_request_auto();

#endif