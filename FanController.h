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

#endif