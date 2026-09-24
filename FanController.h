#ifndef FAN_CONTROLLER_H
#define FAN_CONTROLLER_H

#include <Arduino.h>

void initHardware();

void updateFakeSensor(float &currentTemp);

void updatePhoneDetection(float currentTemp);

void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
);

void updateTach();

#endif