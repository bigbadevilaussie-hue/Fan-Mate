// FAN-MATE V3.20 — HTTP Edition
// WiFi only. No BLE. OTA over HTTP.
// Requires Arduino ESP32 core 2.x (2.0.17)

#ifndef CONFIG_H
#define CONFIG_H

#if __has_include("secrets.h")
    #include "secrets.h"
#else
    #warning "secrets.h not found — copy secrets.example.h to secrets.h"
    #include "secrets.example.h"
#endif

#define FAN_MATE_VERSION "3.43"

// ============================================================
//  Pins
// ============================================================
#define SDA_PIN          5
#define SCL_PIN          6
#define FAN_PWM_PIN      7
#define LED_PIN          8
#define BUZZER_PIN       10
#define TACH_PIN         3
#define DS18B20_PIN      4
#define PHONE_SENSE_PIN  1

// ============================================================
//  Temperature thresholds (defaults — overridden by NVS)
// ============================================================
#define TEMP_ON       34.0
#define TEMP_FULL     42.0
#define TEMP_WARNING  45.0
#define TEMP_PANIC    50.0

// ============================================================
//  Fan PWM
// ============================================================
#define PWM_FREQ      25000
#define PWM_RES       8
#define PWM_MIN       40

// ============================================================
//  Buzzer
// ============================================================
#define BUZZER_CHANNEL 1
#define BUZZER_FREQ    2000
#define BUZZER_RES     8
#define BUZZER_QUIET   64
#define BUZZER_MEDIUM  128
#define BUZZER_LOUD    255

#define WARNING_BEEPS       2
#define WARNING_BEEP_MS     150
#define WARNING_GAP_MS      200
#define WARNING_INTERVAL_MS 120000

#define PANIC_BEEPS       5
#define PANIC_BEEP_MS     200
#define PANIC_GAP_MS      200
#define PANIC_INTERVAL_MS 120000

// ============================================================
//  WiFi + HTTP
// ============================================================
#define HTTP_PORT                80
#define WIFI_CONNECT_TIMEOUT_MS  15000
#define WIFI_RETRY_INTERVAL_MS   30000

// ============================================================
//  Opal router API
// ============================================================
#define SERIAL_BUF_LINES      50
#define OPAL_POLL_INTERVAL_MS   15000
#define OPAL_LOGIN_REFRESH_MS   3000000

// ============================================================
//  Auto Boost
// ============================================================
#define BOOST_DEFAULT_THRESHOLD_KBPS  300
#define BOOST_DEFAULT_HOLD_SEC        4
#define BOOST_DEFAULT_ENABLED         1

// ============================================================
//  Logging
// ============================================================
#define LOG_MAX_SIZE   (800 * 1024)
#define LOG_TICK_MS    15000

#endif