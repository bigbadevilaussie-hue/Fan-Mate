#ifndef CONFIG_H
#define CONFIG_H

#define FAN_MATE_VERSION "2.20"

// Pins
#define SDA_PIN        5
#define SCL_PIN        6
#define FAN_PWM_PIN    7
#define BUZZER_PIN     10
#define TACH_PIN       3
#define DS18B20_PIN    4
#define PHONE_SENSE_PIN 1

// Temperature thresholds (defaults — overridden by NVS)
#define TEMP_ON       34.0
#define TEMP_FULL     42.0
#define TEMP_WARNING  45.0
#define TEMP_PANIC    50.0

#define FAN_MAX_WARN  191
#define FAN_MAX_PANIC 255

// Fan PWM
#define PWM_FREQ      25000
#define PWM_RES       8
#define PWM_MIN       40

// Buzzer
#define BUZZER_CHANNEL 1
#define BUZZER_FREQ    2000
#define BUZZER_RES     8
#define BUZZER_QUIET   64
#define BUZZER_LOUD    255

// Warning
#define WARNING_BEEPS       2
#define WARNING_BEEP_MS     150
#define WARNING_GAP_MS      200
#define WARNING_INTERVAL_MS 120000

// Panic
#define PANIC_BEEPS       5
#define PANIC_BEEP_MS     200
#define PANIC_GAP_MS      200
#define PANIC_INTERVAL_MS 120000

// BLE
#define DEVICE_NAME "Fan-Mate"

#define SERVICE_UUID \
    "4fafc201-1fb5-459e-8fcc-c5c9c331914b"

#define DATA_UUID \
    "beb5483e-36e1-4688-b7f5-ea07361b26a8"

#define TIME_UUID \
    "beb5483e-36e1-4688-b7f5-ea07361b26a9"

#define OTA_DATA_UUID \
    "beb5483e-36e1-4688-b7f5-ea07361b26ac"

#define PAUSE_UUID \
    "beb5483e-36e1-4688-b7f5-ea07361b26af"

#define CONFIG_UUID \
    "beb5483e-36e1-4688-b7f5-ea07361b26b0"

#endif