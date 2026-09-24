#include "BleManager.h"
#include "Config.h"

#include <time.h>
#include <sys/time.h>
#include <cstring>

static BLEServer* pServer = nullptr;
static BLECharacteristic* pDataChar = nullptr;
static BLECharacteristic* pTimeChar = nullptr;

static bool bleInited = false;

static uint32_t macEpochAtSync = 0;
static uint32_t millisAtSync = 0;
static bool timeSynced = false;


// BLE connection callbacks
class ServerCallbacks : public BLEServerCallbacks {

    void onConnect(BLEServer* s) override {
        Serial.println("[BLE] connected");
    }

    void onDisconnect(BLEServer* s) override {
        Serial.println("[BLE] disconnected");

        if (pServer) {
            pServer->getAdvertising()->start();
        }
    }
};


// Time synchronisation
class TimeCallbacks : public BLECharacteristicCallbacks {

    void onWrite(BLECharacteristic* c) override {

        std::string value = c->getValue();

        if (value.length() < 4) {
            return;
        }

        uint32_t timestamp = 0;

        memcpy(
            &timestamp,
            value.data(),
            sizeof(timestamp)
        );

        if (
            timestamp < 1700000000UL ||
            timestamp > 4102444800UL
        ) {
            return;
        }

        macEpochAtSync = timestamp;
        millisAtSync = millis();
        timeSynced = true;

        struct timeval tv;
        tv.tv_sec = timestamp;
        tv.tv_usec = 0;

        settimeofday(&tv, nullptr);

        setenv("TZ", "AEST-10", 1);
        tzset();

        Serial.printf(
            "[TIME] synced: %lu\n",
            (unsigned long)timestamp
        );
    }
};


// BLE initialisation
void initBLE() {

    if (bleInited) {
        return;
    }

    BLEDevice::init(DEVICE_NAME);

    // Preserve V1.10
    BLEDevice::setMTU(185);

    pServer = BLEDevice::createServer();

    pServer->setCallbacks(
        new ServerCallbacks()
    );

    BLEService* pService =
        pServer->createService(SERVICE_UUID);

    pDataChar =
        pService->createCharacteristic(
            DATA_UUID,
            BLECharacteristic::PROPERTY_READ |
            BLECharacteristic::PROPERTY_NOTIFY
        );

    pDataChar->addDescriptor(
        new BLE2902()
    );

    pTimeChar =
        pService->createCharacteristic(
            TIME_UUID,
            BLECharacteristic::PROPERTY_WRITE
        );

    pTimeChar->setCallbacks(
        new TimeCallbacks()
    );

    pService->start();

    BLEAdvertising* pAdvertising =
        BLEDevice::getAdvertising();

    pAdvertising->addServiceUUID(
        SERVICE_UUID
    );

    pAdvertising->setScanResponse(true);

    pAdvertising->start();

    bleInited = true;

    Serial.println("[BLE] ready");
}


// BLE data publishing
void updateBLEData(
    float temp,
    int fanPct,
    int rpm,
    bool phoneConnected,
    int alertState
) {

    if (!pDataChar || !bleInited) {
        return;
    }

    if (
        !pServer ||
        pServer->getConnectedCount() <= 0
    ) {
        return;
    }

    char buf[140];

    snprintf(
        buf,
        sizeof(buf),
        "{\"temp\":%.1f,\"fan\":%d,\"rpm\":%d,\"phone\":%d,\"alert\":%d}",
        temp,
        fanPct,
        rpm,
        phoneConnected ? 1 : 0,
        alertState
    );

    pDataChar->setValue(
        (uint8_t*)buf,
        strlen(buf)
    );

    pDataChar->notify();
}