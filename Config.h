#ifndef CONFIG_H
#define CONFIG_H

#if __has_include("secrets.h")
    #include "secrets.h"
#else
    #warning "secrets.h not found - copy secrets.example.h to secrets.h"
    #include "secrets.example.h"
#endif

// v4.28 network resilience
#define OPAL_HTTP_TIMEOUT_MS 400
#define OPAL_RSSI_FLOOR -70
#define NTP_SYNC_COOLDOWN_MS 60000
#define CLOCK_SYNC_INTERVAL_MS  60000UL
#define CLOCK_HTTP_TIMEOUT_MS   3000

enum SystemState {
    STATE_ACTIVE      = 0,
    STATE_LIGHT_SLEEP = 1,
};
extern SystemState   sys_state;
extern unsigned long phone_absent_since;

#define FAN_MATE_VERSION "4.54"

#define DEBUG_VERBOSE 0

#define SDA_PIN          5
#define SCL_PIN          6
#define FAN_PWM_PIN      7
#define LED_PIN          8
#define BUZZER_PIN       10
#define BUZZER_TONE_HZ   2000
#define TACH_PIN         3
#define DS18B20_PIN      4
#define PHONE_SENSE_PIN  1
#define NTC_PIN          0

#define PWM_FREQ      25000
#define PWM_RES       8

#define FAN_STALL_ENABLED 1


#define WARNING_BEEPS       2
#define WARNING_BEEP_MS     150
#define WARNING_GAP_MS      200
#define WARNING_INTERVAL_MS 120000

#define PANIC_BEEPS       5
#define PANIC_BEEP_MS     200
#define PANIC_GAP_MS      200
#define PANIC_INTERVAL_MS 120000

#define KILL_BEEPS       3
#define KILL_BEEP_MS     200
#define KILL_GAP_MS      200
#define KILL_INTERVAL_MS 30000

#define HTTP_PORT                80
#define WIFI_CONNECT_TIMEOUT_MS  15000
#define WIFI_RETRY_INTERVAL_MS   30000

#define SERIAL_BUF_LINES        50
#define PHONE_SLEEP_DELAY_MS    30000UL
#define PHONE_WAKE_DELAY_MS      5000UL
#define OPAL_LOGIN_REFRESH_MS   3000000

#define LOG_SEAL_MIN_ROWS        3
#define LOG_PAUSE_FREE_BYTES     (100 * 1024)
#define LOG_FILENAME_PREFIX      "log-"
#define CONFIG_FILENAME_PREFIX   "config-"
#define CONFIG_HEADER            "timestamp,key,value"
#define LOG_HEADER               "timestamp,temp_c,net_kbps,boost,fan,rpm,event,outdoor_c,room_c"
#define LOG_FILE_LIVE            "/log.csv"
#define LOG_MAX_SEALED           64
#define LOG_KEEP_MIN             8

#define DRIVE_UPLOAD_TIMEOUT_MS  15000

#define NVS_LOG_NS               "log"
#define NVS_LOG_START_KEY        "live_start"

#endif
