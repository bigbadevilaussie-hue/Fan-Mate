#include "BleManager.h"
#include "Config.h"
#include "DisplayManager.h"

#include <time.h>
#include <sys/time.h>
#include <cstring>
#include <Update.h>

static BLEServer* pServer = nullptr;
static BLECharacteristic* pDataChar = nullptr;
static BLECharacteristic* pTimeChar = nullptr;
static BLECharacteristic* pOtaChar = nullptr;
static BLECharacteristic* pPauseChar = nullptr;

static bool bleInited = false;

static uint32_t macEpochAtSync = 0;
static uint32_t millisAtSync = 0;
static bool timeSynced = false;

volatile bool notificationsPaused = false;

static uint32_t otaExpectedSize = 0;
static uint32_t otaBytesReceived = 0;
static char otaExpectedMd5[33] = "";
static bool otaInProgress = false;
static uint32_t otaLastPrintBytes = 0;

class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* s) override {
        Serial.printf("[BLE] client connected (count=%d)\n",
                      s->getConnectedCount());
        uint16_t mtu = s->getPeerMTU(s->getConnId());
        Serial.printf("[BLE] MTU negotiated: %u\n", mtu);
    }

    void onDisconnect(BLEServer* s) override {
        Serial.println("[BLE] client disconnected, re-advertising");
        if (pServer) pServer->getAdvertising()->start();
    }
};

class TimeCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string value = c->getValue();
        if (value.length() < 4) return;

        uint32_t timestamp = 0;
        memcpy(&timestamp, value.data(), sizeof(timestamp));

        if (timestamp < 1700000000UL || timestamp > 4102444800UL) return;

        macEpochAtSync = timestamp;
        millisAtSync = millis();
        timeSynced = true;

        struct timeval tv;
        tv.tv_sec = timestamp;
        tv.tv_usec = 0;
        settimeofday(&tv, nullptr);
        setenv("TZ", "AEST-10", 1);
        tzset();

        Serial.printf("[TIME] synced: %lu\n", (unsigned long)timestamp);
    }
};

class PauseCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string v = c->getValue();
        if (v.length() < 1) return;
        notificationsPaused = (v[0] == 0x00);
        Serial.printf("[BLE] pause cmd: %s\n",
                      notificationsPaused ? "paused" : "resumed");
    }
};

class OtaCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string v = c->getValue();
        if (v.length() == 0) return;

        uint8_t* data = (uint8_t*)v.data();
        size_t len = v.length();

        if (!otaInProgress) {
            if (len < 36) {
                Serial.printf("[OTA] header too short (%u)\n", (unsigned)len);
                return;
            }
            memcpy(&otaExpectedSize, data, 4);
            memcpy(otaExpectedMd5, data + 4, 32);
            otaExpectedMd5[32] = 0;

            Serial.printf("[OTA] header recv: size=%lu md5=%s\n",
                          (unsigned long)otaExpectedSize, otaExpectedMd5);

            if (!Update.begin(otaExpectedSize)) {
                Serial.printf("[OTA] Update.begin FAILED: %s\n",
                              Update.errorString());
                return;
            }
            Serial.println("[OTA] Update.begin OK");

            otaBytesReceived = 0;
            otaLastPrintBytes = 0;
            otaInProgress = true;
            drawFwStartScreen();
            return;
        }

        if (Update.write(data, len) != len) {
            Serial.printf("[OTA] Update.write FAILED at %lu: %s\n",
                          (unsigned long)otaBytesReceived,
                          Update.errorString());
            Update.abort();
            otaInProgress = false;
            drawOtaScreen(0, 0, 0);
            return;
        }

        otaBytesReceived += len;

        if (otaBytesReceived - otaLastPrintBytes >= 20480) {
            otaLastPrintBytes = otaBytesReceived;
            uint8_t pct = (uint8_t)((otaBytesReceived * 100ULL) / otaExpectedSize);
            Serial.printf("[OTA] chunk recv: %lu/%lu (%u%%)\n",
                          (unsigned long)otaBytesReceived,
                          (unsigned long)otaExpectedSize, pct);
            drawOtaScreen(pct, otaBytesReceived, otaExpectedSize);
        }

        if (otaBytesReceived >= otaExpectedSize) {
            Serial.printf("[OTA] all chunks recv: %lu bytes\n",
                          (unsigned long)otaBytesReceived);

            if (!Update.end(true)) {
                Serial.printf("[OTA] Update.end FAILED: %s\n",
                              Update.errorString());
                otaInProgress = false;
                drawOtaScreen(0, 0, 0);
                return;
            }
            Serial.println("[OTA] Update.end OK");

            String actualMd5 = Update.md5String();
            if (!actualMd5.equalsIgnoreCase(otaExpectedMd5)) {
                Serial.printf("[OTA] md5 mismatch: expected=%s got=%s\n",
                              otaExpectedMd5, actualMd5.c_str());
                otaInProgress = false;
                return;
            }
            Serial.println("[OTA] md5 verify OK");

            if (pServer) pServer->getAdvertising()->stop();

            for (int i = 5; i > 0; i--) {
                drawRebootScreen(i);
                Serial.printf("[OTA] rebooting in %d...\n", i);
                delay(1000);
            }
            ESP.restart();
        }
    }
};

void initBLE() {
    if (bleInited) return;

    Serial.printf("[BLE] init: name=%s mtu=247\n", DEVICE_NAME);
    BLEDevice::init(DEVICE_NAME);
    BLEDevice::setMTU(247);

    pServer = BLEDevice::createServer();
    pServer->setCallbacks(new ServerCallbacks());

    BLEService* pService = pServer->createService(SERVICE_UUID);
    Serial.println("[BLE] service created");

    pDataChar = pService->createCharacteristic(
        DATA_UUID,
        BLECharacteristic::PROPERTY_READ |
        BLECharacteristic::PROPERTY_NOTIFY);
    pDataChar->addDescriptor(new BLE2902());

    pTimeChar = pService->createCharacteristic(
        TIME_UUID,
        BLECharacteristic::PROPERTY_WRITE);
    pTimeChar->setCallbacks(new TimeCallbacks());

    pOtaChar = pService->createCharacteristic(
        OTA_DATA_UUID,
        BLECharacteristic::PROPERTY_WRITE | BLECharacteristic::PROPERTY_WRITE_NR);
    pOtaChar->setCallbacks(new OtaCallbacks());

    pPauseChar = pService->createCharacteristic(
        PAUSE_UUID,
        BLECharacteristic::PROPERTY_WRITE);
    pPauseChar->setCallbacks(new PauseCallbacks());

    pService->start();
    Serial.println("[BLE] service started");

    BLEAdvertising* pAdv = BLEDevice::getAdvertising();
    pAdv->addServiceUUID(SERVICE_UUID);
    pAdv->setScanResponse(true);
    pAdv->start();
    Serial.println("[BLE] advertising started");

    bleInited = true;
}

void updateBLEData(float temp, int fanPct, int rpm,
                   bool phoneConnected, int alertState) {
    if (!pDataChar || !bleInited) return;
    if (!pServer || pServer->getConnectedCount() <= 0) return;
    if (notificationsPaused) return;

    char buf[160];
    snprintf(buf, sizeof(buf),
        "{\"temp\":%.1f,\"fan\":%d,\"rpm\":%d,\"phone\":%d,\"alert\":%d,\"fv\":\"" FAN_MATE_VERSION "\"}",
        temp, fanPct, rpm, phoneConnected ? 1 : 0, alertState);

    pDataChar->setValue((uint8_t*)buf, strlen(buf));
    pDataChar->notify();
}
