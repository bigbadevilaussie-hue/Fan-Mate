// FAN-MATE V3.32 — HTTP Edition
// Boost-driven fan. Sleep state machine. No BLE.

#include "Config.h"
#include "Settings.h"
#include "FanController.h"
#include "DisplayManager.h"
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
//  Global state
// ============================================================
float currentTemp  = 0.0;
int   fanPct       = 0;
int   fanRPM       = 0;
int   alertState   = 0;
bool  phonePresent = false;

float lastNetKbps  = 0.0;
int   lastNetMB    = 0;

volatile bool otaInProgress = false;

// Sleep state machine — shared with WebServer via Config.h
SystemState   sys_state = STATE_ACTIVE;
unsigned long phone_absent_since = 0;
static unsigned long sleep_start_ms = 0;

// Tick state
static unsigned long last_tick     = 0;
static uint64_t      last_rx       = 0;
static bool          have_baseline = false;

// ============================================================
//  Sleep / wake
// ============================================================
void enter_sleep() {
    Serial.println("[SLEEP] phone absent - entering sleep");
    sys_state = STATE_LIGHT_SLEEP;
    sleep_start_ms = millis();
    phone_absent_since = 0;

    silenceFanAndAlerts();
    auto_boost_release();
    opal_pause();

    log_write_event("SLEEP");
    clearDisplay();

    digitalWrite(LED_PIN, LOW);
    Serial.println("[SLEEP] entered");
}

void exit_sleep() {
    Serial.println("[SLEEP] phone detected - waking");
    sys_state = STATE_ACTIVE;
    phone_absent_since = 0;

    time_t now = time(nullptr);
    if (now >= 1700000000UL) {
        struct tm tm;
        localtime_r(&now, &tm);
        Serial.printf("[SLEEP] rtc: %04d-%02d-%02d %02d:%02d:%02d\n",
                      tm.tm_year + 1900, tm.tm_mon + 1, tm.tm_mday,
                      tm.tm_hour, tm.tm_min, tm.tm_sec);
    }

    log_write_event("WAKE");

    have_baseline = false;
    last_rx = 0;
    last_tick = millis() - 15000;

    opal_resume();
    wakeDisplay();

    digitalWrite(LED_PIN, HIGH);
    Serial.println("[SLEEP] awake");
}

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
    Serial.println("  Mode:  HTTP only");
    Serial.println("================================");

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);

    setenv("TZ", "AEST-10", 1);
    tzset();

    settings_load();
    initHardware();

    // DS18B20 warmup
    Serial.println("[BOOT] waiting for first DS18B20 reading...");
    for (int i = 0; i < 20; i++) {
        float t = 0.0f;
        readDS18B20(t);
        if (t > -50.0f && t < 100.0f && t != 0.0f) {
            currentTemp = t;
            Serial.printf("[BOOT] DS18B20 first: %.1fC\n", t);
            break;
        }
        delay(500);
    }

    initDisplay();
    log_init();
    log_write_reset_reason();

    drawSplashScreen();
    Serial.println("[SPLASH] 5s...");
    delay(5000);

    wifi_setup();

    Serial.printf("[BOOT] Fan-Mate V%s ready\n", FAN_MATE_VERSION);
}

// ============================================================
//  15-second tick
// ============================================================
static void tick_15s() {
    readDS18B20(currentTemp);

    uint64_t rx_now = 0;
    bool opal_ok = opal_poll(rx_now);

    float kbps_raw = 0.0f;

    if (opal_ok) {
        float mb = rx_now / 1048576.0f;
        if (have_baseline && rx_now >= last_rx) {
            uint64_t delta = rx_now - last_rx;
            kbps_raw = (delta / 15.0f) / 1024.0f;
        } else {
            have_baseline = true;
        }
        last_rx = rx_now;
        lastNetMB = (int)mb;
    } else {
        have_baseline = false;
    }

    // Peak-hold smoothing (3-tick)
    static float recent[3] = {0, 0, 0};
    static int   idx = 0;
    recent[idx] = kbps_raw;
    idx = (idx + 1) % 3;
    float kbps = recent[0];
    if (recent[1] > kbps) kbps = recent[1];
    if (recent[2] > kbps) kbps = recent[2];

    lastNetKbps = kbps;
    auto_boost_update(kbps);

    // Adaptive logging
    static unsigned long last_log = 0;
    bool active_traffic = (kbps > 50.0f);
    unsigned long interval = active_traffic ? 15000UL : 60000UL;
    if (millis() - last_log >= interval) {
        last_log = millis();
        log_write(currentTemp, kbps,
                  auto_boost_is_active() ? 1 : 0,
                  fanPct, fanRPM);
    }

    log_check_full();

    Serial.printf("[TICK] temp=%.1f fan=%d%% net=%.1f (raw=%.1f) boost=%d rpm=%d\n",
                  currentTemp, fanPct, kbps, kbps_raw,
                  auto_boost_is_active() ? 1 : 0, fanRPM);
}

// ============================================================
//  Main loop
// ============================================================
void loop() {
    static unsigned long lastStatus   = 0;
    static unsigned long lastOLED     = 0;
    static bool          server_ready = false;

    unsigned long now = millis();

    wifi_loop();
    if (wifi_connected() && !server_ready) {
        server_setup();
        opal_init();
        auto_boost_init();
        server_ready = true;
    }
    if (server_ready) server_loop();

    updatePhoneDetection();
    updateTach();

    // ── Sleep state machine ─────────────────────────────
    bool phone_now;
    if (config.phoneMode == "auto") {
        phone_now = phonePresent;
    } else {
        phone_now = true;   // "off" mode = always active
    }

    if (!phone_now && sys_state == STATE_ACTIVE) {
        if (phone_absent_since == 0) {
            phone_absent_since = now;
            Serial.printf("[SLEEP] phone absent - delay %d s\n", config.phoneTestDelay);
        }
        unsigned long delay_ms = (unsigned long)config.phoneTestDelay * 1000UL;
        if (now - phone_absent_since >= delay_ms) {
            enter_sleep();
        }
    } else if (phone_now && sys_state == STATE_LIGHT_SLEEP) {
        exit_sleep();
    } else if (phone_now) {
        phone_absent_since = 0;
    }

    // ── Active-only work ────────────────────────────────
    if (sys_state == STATE_ACTIVE) {
        updateFanAndAlerts(currentTemp, fanPct, fanRPM, alertState, phonePresent);

        if (now - lastOLED >= 500 && !otaInProgress) {
            lastOLED = now;
            updateDisplay(currentTemp, fanPct, fanRPM, alertState, phonePresent);
        }

        if (server_ready && now - last_tick >= 15000) {
            last_tick = now;
            tick_15s();
        }

        if (now - lastStatus >= 10000) {
            lastStatus = now;
            Serial.printf("[STATUS] temp=%.1f fan=%d%% rpm=%d phone=%d alert=%d net=%.1f",
                          currentTemp, fanPct, fanRPM,
                          phonePresent ? 1 : 0, alertState, lastNetKbps);
            if (wifi_connected()) {
                Serial.printf(" ip=%s rssi=%d\n", wifi_ip().c_str(), wifi_rssi());
            } else {
                Serial.printf(" wifi=disconnected\n");
            }
        }
    } else {
        // Sleep — quiet status every 30s
        if (now - lastStatus >= 30000) {
            lastStatus = now;
            Serial.printf("[SLEEP] temp=%.1f waiting\n", currentTemp);
        }
    }
}