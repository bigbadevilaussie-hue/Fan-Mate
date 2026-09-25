// FAN-MATE V3.00 — Main coordinator
// WiFi Edition — WiFi + HTTP server alongside BLE
// Requires Arduino ESP32 core 2.x (2.0.17)

#include "Config.h"
#include "Settings.h"
#include "FanController.h"
#include "DisplayManager.h"
#include "BleManager.h"
#include "WiFiManager.h"
#include "WebServer.h"

#include <esp_arduino_version.h>

#if ESP_ARDUINO_VERSION_MAJOR >= 3
#error "Fan-Mate requires Arduino ESP32 core 2.x (2.0.17)"
#endif

// ============================================================
//  Global state — visible to WebServer.cpp via extern
// ============================================================
float currentTemp  = 0.0;
int   fanPct       = 0;
int   fanRPM       = 0;
int   alertState   = 0;
bool  phonePresent = false;

// ============================================================
//  Setup
// ============================================================
void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println();
    Serial.println("================================");
    Serial.printf ("  Fan-Mate V%s\n", FAN_MATE_VERSION);
    Serial.printf ("  Build: %s %s\n", __DATE__, __TIME__);
    Serial.println("  Chip:  ESP32-C3");
    Serial.println("  Mode:  WiFi + BLE (transition)");
    Serial.println("================================");

    setenv("TZ", "AEST-10", 1);
    tzset();

    // ---- Settings from NVS ----
    settings_load();

    // ---- Hardware ----
    initHardware();
    initDisplay();

    // ---- Splash ----
    drawSplashScreen();
    Serial.println("[SPLASH] 5s...");
    delay(5000);

    // ---- BLE first (claims radio before WiFi) ----
    initBLE();

    // ---- WiFi + HTTP (V3.00) ----
    wifi_setup();
    // server_setup() is called from wifi_loop() once connected

    Serial.printf("[BOOT] Fan-Mate V%s ready\n", FAN_MATE_VERSION);
}

// ============================================================
//  Loop
// ============================================================
void loop() {
    static unsigned long lastPublish  = 0;
    static unsigned long lastStatus   = 0;
    static unsigned long lastOLED     = 0;
    static bool          server_ready = false;

    unsigned long now = millis();

    // ---- WiFi + HTTP ----
    wifi_loop();
    if (wifi_connected() && !server_ready) {
        server_setup();
        server_ready = true;
    }
    if (server_ready) {
        server_loop();
    }

    // ---- Sensors ----
    readDS18B20(currentTemp);
    updatePhoneDetection();
    updateTach();

    // ---- Fan + alerts ----
    updateFanAndAlerts(
        currentTemp,
        fanPct,
        fanRPM,
        alertState,
        phonePresent
    );

    // ---- OLED (skipped during OTA) ----
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
        Serial.printf("[STATUS] temp=%.1f fan=%d%% rpm=%d phone=%d alert=%d",
                      currentTemp, fanPct, fanRPM,
                      phonePresent ? 1 : 0, alertState);
        if (wifi_connected()) {
            Serial.printf(" ip=%s rssi=%d\n",
                          wifi_ip().c_str(), wifi_rssi());
        } else {
            Serial.printf(" wifi=disconnected\n");
        }
    }
}