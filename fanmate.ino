// FAN-MATE V3.00 — Main coordinator
// WiFi + HTTP server alongside BLE (BLE removed in V3.01)
// Requires Arduino ESP32 core 2.x (2.0.17)

#include "Config.h"
#include "Settings.h"
#include "FanController.h"
#include "DisplayManager.h"
#include "BleManager.h"
#include "WiFiManager.h"
#include "WebServer.h"
#include "OpalClient.h"
#include "AutoBoost.h"
#include "Logging.h"

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

    // ---- LittleFS (must be before logging) ----
    log_init();

    // ---- Splash ----
    drawSplashScreen();
    Serial.println("[SPLASH] 5s...");
    delay(5000);

    // ---- BLE first (claims radio before WiFi) ----
    initBLE();

    // ---- WiFi + HTTP ----
    wifi_setup();

    // ---- Boot complete ----
    Serial.printf("[BOOT] Fan-Mate V%s ready\n", FAN_MATE_VERSION);
}

// ============================================================
//  15-second tick — all decisions
// ============================================================
static unsigned long last_tick     = 0;
static uint64_t      last_rx       = 0;
static bool          have_baseline = false;

static void tick_15s() {
    // 1. Read temp (uses lastGoodTemp if conversion not ready)
    readDS18B20(currentTemp);

    // 2. Poll Opal
    uint64_t rx_now = 0;
    bool opal_ok = opal_poll(rx_now);

    if (!opal_ok) {
        Serial.println("[TICK] Opal failed — skipping log");
        return;
    }

    // 3. Compute rate
    float mb       = rx_now / 1048576.0f;
    float kbps     = 0.0f;

    if (have_baseline && rx_now >= last_rx) {
        uint64_t delta = rx_now - last_rx;
        kbps = (delta / 15.0f) / 1024.0f;
    } else {
        have_baseline = true;
    }
    last_rx = rx_now;

    // 4. Auto boost decision
    auto_boost_update(kbps);

    // 5. Log
    int alarm_flag = (alertState > 0) ? 1 : 0;
    log_write(
        currentTemp,
        mb,
        auto_boost_is_active() ? 1 : 0,
        fanRPM,
        alarm_flag,
        config.benchMode ? 1 : 0
    );

    // 6. Check if log full → beep
    log_check_full();

    // 7. Serial
    Serial.printf("[TICK] temp=%.1f fan=%d%% net=%.1f KB/s boost=%d rpm=%d\n",
                  currentTemp, fanPct, kbps,
                  auto_boost_is_active() ? 1 : 0, fanRPM);
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
        // Also init Opal now that WiFi is up
        opal_init();
        auto_boost_init();
        server_ready = true;
    }
    if (server_ready) {
        server_loop();
    }

    // ---- Sensors ----
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

    // ---- OLED ----
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

    // ---- 15s tick ----
    if (server_ready && now - last_tick >= 15000) {
        last_tick = now;
        tick_15s();
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