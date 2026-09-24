#ifndef BLE_MANAGER_H
#define BLE_MANAGER_H

#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

void initBLE();

void updateBLEData(
    float temp,
    int fanPct,
    int rpm,
    bool phoneConnected,
    int alertState
);

#endif