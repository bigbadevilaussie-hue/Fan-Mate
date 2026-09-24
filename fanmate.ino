// FAN-MATE V2.02
// Modular version of known-good FAN-MATE V1.10
// Requires Arduino ESP32 core 2.x (2.0.17)

#include "Config.h"
#include "BleManager.h"
#include "FanController.h"
#include "DisplayManager.h"

#include <esp_arduino_version.h>

#if ESP_ARDUINO_VERSION_MAJOR >= 3
#error "Fan-Mate requires Arduino ESP32 core 2.x (2.0.17)"
#endif

float currentTemp = 0.0;

void setup() {
    Serial.begin(115200);
    delay(500);

    setenv("TZ", "AEST-10", 1);
    tzset();

    initHardware();
    initDisplay();
    initBLE();

    Serial.println("[BOOT] Fan-Mate V2.02 ready");
}

void loop() {
    static unsigned long lastPublish = 0;
    static unsigned long lastStatus = 0;
    static unsigned long lastOLED = 0;

    unsigned long now = millis();

    readDS18B20(currentTemp);
    updatePhoneDetection();

    int fanPct = 0;
    int fanRPM = 0;
    int alertState = 0;
    bool phonePresent = false;

    updateFanAndAlerts(
        currentTemp,
        fanPct,
        fanRPM,
        alertState,
        phonePresent
    );

    updateTach();

    if (now - lastOLED >= 500) {
        lastOLED = now;

        updateDisplay(
            currentTemp,
            fanPct,
            fanRPM,
            alertState,
            phonePresent
        );
    }

    if (now - lastPublish >= 2000) {
        lastPublish = now;

        updateBLEData(
            currentTemp,
            fanPct,
            fanRPM,
            phonePresent,
            alertState
        );
    }

    if (now - lastStatus >= 10000) {
        lastStatus = now;

        Serial.printf(
            "[STATUS] temp=%.1f fan=%d%% rpm=%d phone=%d alert=%d\n",
            currentTemp,
            fanPct,
            fanRPM,
            phonePresent ? 1 : 0,
            alertState
        );
    }

    delay(50);
}