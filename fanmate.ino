// FAN-MATE - Main coordinator
// Requires Arduino ESP32 core 2.x (2.0.17)

#include "Config.h"
#include "BleManager.h"
#include "FanController.h"
#include "DisplayManager.h"
#include "Settings.h"

#include <esp_arduino_version.h>

#if ESP_ARDUINO_VERSION_MAJOR >= 3
#error "Fan-Mate requires Arduino ESP32 core 2.x (2.0.17)"
#endif

float currentTemp = 0.0;

void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("========================");
    Serial.printf("  Fan-Mate V%s\n", FAN_MATE_VERSION);
    Serial.printf("  Build: %s %s\n", __DATE__, __TIME__);
    Serial.println("  Chip:  ESP32-C3");
    Serial.println("========================");

    setenv("TZ", "AEST-10", 1);
    tzset();

    settings_load();

    initHardware();
    initDisplay();

    drawSplashScreen();
    Serial.println("[SPLASH] 5s...");
    delay(5000);

    initBLE();

    Serial.printf("[BOOT] Fan-Mate V%s ready\n", FAN_MATE_VERSION);
}

void loop() {
    static unsigned long lastPublish = 0;
    static unsigned long lastStatus = 0;
    static unsigned long lastOLED = 0;

    unsigned long now = millis();

    readDS18B20(currentTemp);
    updatePhoneDetection();
    updateTach();

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

    // ---- OLED update — SKIPPED during OTA ----
    if (now - lastOLED >= 500 && !otaInProgress) {
        lastOLED = now;
        updateDisplay(
            currentTemp,
            fanPct,
            fanRPM,
            alertState,
            phonePresent
        );
    }

    // ---- BLE notify every 2s ----
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

    // ---- Serial status every 10s ----
    if (now - lastStatus >= 10000) {
        lastStatus = now;
        Serial.printf("[STATUS] temp=%.1f fan=%d%% rpm=%d phone=%d alert=%d\n",
                      currentTemp, fanPct, fanRPM,
                      phonePresent ? 1 : 0, alertState);
    }
}