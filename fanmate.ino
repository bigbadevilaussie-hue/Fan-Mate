// FAN-MATE V3.73 - HTTP Edition
// WiFi only. No BLE. OTA over HTTP.
// Requires Arduino ESP32 core 2.x (2.0.17)

#include "Config.h"
#include "Settings.h"
#include "FanController.h"
#include "DisplayManager.h"
#include "WiFiManager.h"
#include "WebServer.h"
#include "OpalClient.h"
#include "AutoBoost.h"
#include "Logging.h"
#include "WeatherClient.h"
#include "SerialBuffer.h"

extern void ntp_loop();

#include <esp_arduino_version.h>

#if ESP_ARDUINO_VERSION_MAJOR >= 3
#error "Fan-Mate requires Arduino ESP32 core 2.x (2.0.17)"
#endif

float currentTemp  = 0.0;
int   fanPct       = 0;
int   fanRPM       = 0;
int   alertState   = 0;
bool  phonePresent = false;

volatile bool otaInProgress = false;

SystemState   sys_state = STATE_ACTIVE;
unsigned long phone_absent_since = 0;
static unsigned long sleep_start_ms = 0;
bool          have_baseline = false;
uint64_t      last_rx       = 0;
unsigned long last_tick     = 0;

// ── Sleep state machine ────────────────────────────────
void enter_sleep() {
    log_print("[SLEEP] phone absent — entering sleep\n");
    sys_state = STATE_LIGHT_SLEEP;
    sleep_start_ms = millis();
    phone_absent_since = 0;
    silenceFanAndAlerts();
    auto_boost_release();
    opal_pause();
    log_write_event("SLEEP");
    clearDisplay();
    digitalWrite(LED_PIN, LOW);
    log_print("[SLEEP] entered\n");
}

void exit_sleep() {
    log_print("[SLEEP] phone detected — waking\n");
    sys_state = STATE_ACTIVE;
    phone_absent_since = 0;
    log_write_event("WAKE");
    have_baseline = false;
    last_rx = 0;
    last_tick = millis() - 15000;
    opal_resume();
    wakeDisplay();
    digitalWrite(LED_PIN, HIGH);
    log_print("[SLEEP] awake\n");
}

// ============================================================
//  Setup
// ============================================================
void setup() {
    Serial.begin(115200);
    delay(500);

    serial_buf_init();

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
    weather_init();
    initHardware();

    Serial.println("[BOOT] waiting for DS18B20...");
    for (int i = 0; i < 20; i++) {
        float t = 0.0f;
        readDS18B20(t);
        if (t > -50.0f && t < 100.0f && t != 0.0f) {
            currentTemp = t;
            log_print("[BOOT] DS18B20 first: %.1f C\n", t);
            break;
        }
        delay(500);
    }
    initDisplay();
    log_init();
    log_boot_recovery();
    log_write_reset_reason();

    drawSplashScreen();
    delay(5000);

    wifi_setup();

    log_print("[BOOT] Fan-Mate V%s ready\n", FAN_MATE_VERSION);
}

// ============================================================
//  15-second tick
// ============================================================
float lastNetKbps = 0.0;

static void tick_15s() {
    readDS18B20(currentTemp);

    uint64_t rx_now = 0;
    bool opal_ok = opal_poll(rx_now);

    if (!opal_ok) {
        return;
    }

    float kbps = 0.0f;
    if (have_baseline && rx_now >= last_rx) {
        uint64_t delta = rx_now - last_rx;
        kbps = (delta / 15.0f) / 1024.0f;
    } else {
        have_baseline = true;
    }
    last_rx = rx_now;

    static float peak_hist[3] = {0, 0, 0};
    static int   peak_idx = 0;
    peak_hist[peak_idx] = kbps;
    peak_idx = (peak_idx + 1) % 3;

    float kbps_smooth = peak_hist[0];
    if (peak_hist[1] > kbps_smooth) kbps_smooth = peak_hist[1];
    if (peak_hist[2] > kbps_smooth) kbps_smooth = peak_hist[2];

    lastNetKbps = kbps_smooth;

    auto_boost_update(kbps_smooth);

    if (currentTemp > 0.0) {
        log_write(currentTemp, kbps_smooth,
                  auto_boost_gear() > 0 ? 1 : 0,
                  fanPct, fanRPM);
    }

    log_rotate_check();
    log_check_full();

#if DEBUG_VERBOSE
    log_print("[TICK] temp=%.1f fan=%d%% net=%.1f KB/s boost=%d rpm=%d\n",
              currentTemp, fanPct, kbps_smooth,
              auto_boost_gear() > 0 ? 1 : 0, fanRPM);
#endif
}

// ============================================================
//  Loop
// ============================================================
void loop() {
    static unsigned long lastOLED     = 0;
    static bool          server_ready = false;

    unsigned long now = millis();

    wifi_loop();
    ntp_loop();
    weather_loop();
    if (wifi_connected() && !server_ready) {
        server_setup();
        opal_init();
        auto_boost_init();
        server_ready = true;
    }
    if (server_ready) {
        server_loop();
    }

    updatePhoneDetection();
    updateTach();

    bool phone_now;
    if (config.phoneMode == "off") {
        phone_now = true;
    } else {
        phone_now = phonePresent;
    }

    if (!phone_now && sys_state == STATE_ACTIVE) {
        enter_sleep();
    } else if (phone_now && sys_state == STATE_LIGHT_SLEEP) {
        exit_sleep();
    }

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
    }
}