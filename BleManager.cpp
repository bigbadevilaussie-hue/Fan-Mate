#include "BleManager.h"
#include "Config.h"
#include "DisplayManager.h"
#include "Settings.h"

#include <time.h>
#include <sys/time.h>
#include <cstring>
#include <Update.h>

// ============================================================
//  BLE server — V3.00 transitional (removed in V3.01)
//  DATA notify + TIME sync + PAUSE + OTA + CONFIG
// ============================================================

static BLEServer*         pServer     = nullptr;
static BLECharacteristic* pDataChar   = nullptr;
static BLECharacteristic* pTimeChar   = nullptr;
static BLECharacteristic* pOtaChar    = nullptr;
static BLECharacteristic* pPauseChar  = nullptr;
static BLECharacteristic* pConfigChar = nullptr;

static bool bleInited = false;

static uint32_t macEpochAtSync = 0;
static uint32_t millisAtSync   = 0;
static bool     timeSynced     = false;

volatile bool notificationsPaused = false;
volatile bool otaInProgress       = false;

static uint32_t otaExpectedSize  = 0;
static uint32_t otaBytesReceived = 0;
static char     otaExpectedMd5[33] = "";
static uint32_t otaLastPrintBytes = 0;
static uint32_t otaLastReadySent  = 0;

// ------------------------------------------------------------
class ServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* s) override {
        Serial.println("[BLE] client connected");
        delay(200);
        uint16_t mtu = s->getPeerMTU(s->getConnId());
        Serial.printf("[BLE] MTU negotiated: %u\n", mtu);
    }
    void onDisconnect(BLEServer* s) override {
        Serial.println("[BLE] client disconnected, re-advertising");
        if (pServer) pServer->getAdvertising()->start();
    }
};

// ------------------------------------------------------------
class TimeCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string value = c->getValue();
        if (value.length() < 4) return;
        uint32_t timestamp = 0;
        memcpy(&timestamp, value.data(), sizeof(timestamp));
        if (timestamp < 1700000000UL || timestamp > 4102444800UL) return;

        macEpochAtSync = timestamp;
        millisAtSync   = millis();
        timeSynced     = true;

        struct timeval tv;
        tv.tv_sec  = timestamp;
        tv.tv_usec = 0;
        settimeofday(&tv, nullptr);
        setenv("TZ", "AEST-10", 1);
        tzset();

        Serial.printf("[TIME] synced: %lu\n", (unsigned long)timestamp);
    }
};

// ------------------------------------------------------------
class PauseCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string v = c->getValue();
        if (v.length() < 1) return;
        notificationsPaused = (v[0] == 0x00);
        Serial.printf("[BLE] pause cmd: %s\n",
                      notificationsPaused ? "paused" : "resumed");
    }
};

// ------------------------------------------------------------
class ConfigCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string v = c->getValue();
        if (v.length() == 0) return;
        Serial.printf("[CFG] BLE recv: %s\n", v.c_str());
        settings_apply_json(v.c_str());
    }
};

// ------------------------------------------------------------
class OtaCallbacks : public BLECharacteristicCallbacks {
    void onWrite(BLECharacteristic* c) override {
        std::string v = c->getValue();
        if (v.length() == 0) return;

        uint8_t* data = (uint8_t*)v.data();
        size_t   len  = v.length();

        if (!otaInProgress) {
            if (len < 36) return;
            memcpy(&otaExpectedSize, data, 4);
            memcpy(otaExpectedMd5, data + 4, 32);
            otaExpectedMd5[32] = 0;

            Serial.printf("[OTA] header: size=%lu md5=%s\n",
                          (unsigned long)otaExpectedSize, otaExpectedMd5);

            if (!Update.begin(otaExpectedSize)) {
                Serial.printf("[OTA] begin FAILED: %s\n", Update.errorString());
                return;
            }
            Serial.println("[OTA] begin OK");

            otaBytesReceived  = 0;
            otaLastPrintBytes = 0;
            otaLastReadySent  = 0;
            otaInProgress     = true;
            drawFwStartScreen();
            return;
        }

        if (Update.write(data, len) != len) {
            Serial.printf("[OTA] write FAILED: %s\n", Update.errorString());
            Update.abort();
            otaInProgress = false;
            return;
        }

        otaBytesReceived += len;

        if (otaBytesReceived - otaLastPrintBytes >= 20480) {
            otaLastPrintBytes = otaBytesReceived;
            uint8_t pct = (uint8_t)((otaBytesReceived * 100ULL) / otaExpectedSize);
            Serial.printf("[OTA] %lu/%lu (%u%%)\n",
                          (unsigned long)otaBytesReceived,
                          (unsigned long)otaExpectedSize, pct);
            drawOtaScreen(pct, otaBytesReceived, otaExpectedSize);
        }

        if (otaBytesReceived - otaLastReadySent >= 2048) {
            otaLastReadySent = otaBytesReceived;
            uint8_t ready = 0x01;
            pOtaChar->setValue(&ready, 1);
            pOtaChar->notify();
        }

        if (otaBytesReceived >= otaExpectedSize) {
            if (!Update.end(true)) {
                Serial.printf("[OTA] end FAILED: %s\n", Update.errorString());
                otaInProgress = false;
                return;
            }

            String actualMd5 = Update.md5String();
            if (!actualMd5.equalsIgnoreCase(otaExpectedMd5)) {
                Serial.println("[OTA] md5 mismatch");
                otaInProgress = false;
                return;
            }

            Serial.println("[OTA] success");
            if (pServer) pServer->getAdvertising()->stop();

            for (int i = 5; i > 0; i--) {
                drawRebootScreen(i);
                delay(1000);
            }
            ESP.restart();
        }
    }
};

// ------------------------------------------------------------
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
        BLECharacteristic::PROPERTY_WRITE |
        BLECharacteristic::PROPERTY_WRITE_NR |
        BLECharacteristic::PROPERTY_NOTIFY);
    pOtaChar->addDescriptor(new BLE2902());
    pOtaChar->setCallbacks(new OtaCallbacks());

    pPauseChar = pService->createCharacteristic(
        PAUSE_UUID,
        BLECharacteristic::PROPERTY_WRITE);
    pPauseChar->setCallbacks(new PauseCallbacks());

    pConfigChar = pService->createCharacteristic(
        CONFIG_UUID,
        BLECharacteristic::PROPERTY_WRITE);
    pConfigChar->setCallbacks(new ConfigCallbacks());

    pService->start();
    Serial.println("[BLE] service started");

    BLEAdvertising* pAdv = BLEDevice::getAdvertising();
    pAdv->addServiceUUID(SERVICE_UUID);
    pAdv->setScanResponse(true);
    pAdv->start();
    Serial.println("[BLE] advertising started");

    bleInited = true;
}

// ------------------------------------------------------------
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