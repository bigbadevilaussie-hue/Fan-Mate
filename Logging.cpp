#include "Logging.h"
#include "Config.h"
#include "DisplayManager.h"
#include "WiFiManager.h"

#include <LittleFS.h>
#include <Preferences.h>
#include <time.h>
#include <sys/time.h>
#include <esp_system.h>

extern float weather_get_temp();
extern float currentTemp;

static unsigned long last_full_beep = 0;
static bool          warned_full    = false;
static const char* LOG_FILE = LOG_FILE_LIVE;

static time_t _live_file_start_epoch = 0;

String log_time_string() {
    setenv("TZ", "AEST-10", 1);
    tzset();
    time_t now = time(nullptr);
    if (now < 1700000000UL) {
        char buf[24];
        snprintf(buf, sizeof(buf), "uptime:%lu", millis() / 1000);
        return String(buf);
    }
    struct tm ti;
    localtime_r(&now, &ti);
    char buf[24];
    snprintf(buf, sizeof(buf), "%04d-%02d-%02d %02d:%02d:%02d",
             ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday,
             ti.tm_hour, ti.tm_min, ti.tm_sec);
    return String(buf);
}

static void write_header_if_new() {
    if (LittleFS.exists(LOG_FILE)) return;
    File f = LittleFS.open(LOG_FILE, "w");
    if (!f) return;
    f.println("timestamp,temp_c,net_kbps,boost,fan,rpm,event,outdoor_c");
    f.close();
}

static void save_start_epoch(time_t t) {
    Preferences p;
    p.begin(NVS_LOG_NS, false);
    p.putULong(NVS_LOG_START_KEY, (unsigned long)t);
    p.end();
}

static time_t load_start_epoch() {
    Preferences p;
    p.begin(NVS_LOG_NS, true);
    unsigned long v = p.getULong(NVS_LOG_START_KEY, 0);
    p.end();
    time_t t = (time_t)v;
    if (t < 1700000000UL || t > 4102444800UL) return 0;
    return t;
}

static void clear_start_epoch() {
    Preferences p;
    p.begin(NVS_LOG_NS, false);
    p.remove(NVS_LOG_START_KEY);
    p.end();
}

size_t log_count_live_rows() {
    if (!LittleFS.exists(LOG_FILE)) return 0;
    File f = LittleFS.open(LOG_FILE, "r");
    if (!f) return 0;
    size_t count = 0;
    while (f.available()) {
        String line = f.readStringUntil('\n');
        if (line.length() < 5) continue;
        if (line.startsWith("timestamp,")) continue;
        if (line.startsWith("#")) continue;
        count++;
    }
    f.close();
    return count;
}

static bool build_sealed_name(time_t name_epoch, char* out, size_t n) {
    struct tm ti;
    localtime_r(&name_epoch, &ti);
    int written = snprintf(out, n, "%s%s-%04d%02d%02d-%02d%02d.csv",
             LOG_FILENAME_PREFIX, FAN_MATE_VERSION,
             ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday,
             ti.tm_hour, ti.tm_min);
    return written > 0 && (size_t)written < n;
}

static void open_fresh_live(time_t start_epoch) {
    File f = LittleFS.open(LOG_FILE, "w");
    if (!f) return;
    f.println("timestamp,temp_c,net_kbps,boost,fan,rpm,event,outdoor_c");
    f.close();
    _live_file_start_epoch = start_epoch;
    save_start_epoch(start_epoch);
}

static bool seal_live(time_t name_epoch) {
    if (!LittleFS.exists(LOG_FILE)) return false;

    char sealed[64];
    if (!build_sealed_name(name_epoch, sealed, sizeof(sealed))) return false;

    char sealed_path[80];
    snprintf(sealed_path, sizeof(sealed_path), "/%s", sealed);

    if (LittleFS.exists(sealed_path)) {
        Serial.printf("[LOG] seal collision: %s\n", sealed_path);
        return false;
    }

    if (!LittleFS.rename(LOG_FILE, sealed_path)) {
        Serial.printf("[LOG] rename failed\n");
        return false;
    }

    Serial.printf("[LOG] sealed %s\n", sealed_path);

    time_t now = time(nullptr);
    open_fresh_live(now);
    log_write_event("SEAL");
    return true;
}

void log_rotate_check() {
    if (!ntp_synced()) return;
    time_t now = time(nullptr);
    if (now < 1700000000UL || now > 4102444800UL) return;

    if (_live_file_start_epoch == 0) {
        _live_file_start_epoch = load_start_epoch();
        if (_live_file_start_epoch == 0) {
            _live_file_start_epoch = now;
            save_start_epoch(now);
        }
    }

    if (now <= _live_file_start_epoch) return;
    if (now - _live_file_start_epoch > 24 * 3600UL) {
        Serial.println("[LOG] time jump > 24h, refusing to seal");
        return;
    }

    struct tm now_ti, start_ti;
    localtime_r(&now, &now_ti);
    localtime_r(&_live_file_start_epoch, &start_ti);

    if (now_ti.tm_hour != start_ti.tm_hour ||
        now_ti.tm_yday != start_ti.tm_yday ||
        now_ti.tm_year != start_ti.tm_year) {
        if (log_rotation_paused()) {
            Serial.println("[LOG] rotation paused, not sealing");
            return;
        }
        seal_live(_live_file_start_epoch);
    }
}

void log_boot_recovery() {
    if (!LittleFS.exists(LOG_FILE)) return;

    size_t rows = log_count_live_rows();
    if (rows < LOG_SEAL_MIN_ROWS) {
        Serial.printf("[LOG] boot: only %u rows, discarding\n", (unsigned)rows);
        LittleFS.remove(LOG_FILE);
        clear_start_epoch();
        write_header_if_new();
        _live_file_start_epoch = time(nullptr);
        save_start_epoch(_live_file_start_epoch);
        return;
    }

    time_t stored = load_start_epoch();
    time_t now = time(nullptr);
    time_t name_epoch = (stored > 0) ? stored : now;

    Serial.printf("[LOG] boot: sealing %u rows\n", (unsigned)rows);

    if (seal_live(name_epoch)) {
        log_write_event("BOOT");
    }
    clear_start_epoch();
}

void log_init() {
    if (!LittleFS.begin(true)) {
        Serial.println("[LOG] LittleFS mount FAILED");
        return;
    }
    Serial.printf("[LOG] mounted used=%u/%u\n",
                  (unsigned)LittleFS.usedBytes(),
                  (unsigned)LittleFS.totalBytes());
    write_header_if_new();
    _live_file_start_epoch = load_start_epoch();
    if (_live_file_start_epoch == 0) {
        _live_file_start_epoch = time(nullptr);
    }
}

void log_write(float temp, float net_kbps, int boost, int fan, int rpm) {
    if (log_rotation_paused()) return;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    f.printf("%s,%.1f,%.1f,%d,%d,%d,,%.1f\n",
             t.c_str(), temp, net_kbps, boost, fan, rpm,
             weather_get_temp());
    f.close();
}

void log_write_event(const char* event) {
    if (log_rotation_paused()) return;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    f.printf("%s,%.1f,0.0,0,0,0,%s,%.1f\n",
             t.c_str(), currentTemp, event, weather_get_temp());
    f.close();
}

void log_write_reset_reason() {
    esp_reset_reason_t r = esp_reset_reason();
    const char* s;
    switch (r) {
        case ESP_RST_POWERON:  s = "POWERON";  break;
        case ESP_RST_SW:       s = "SOFTWARE"; break;
        case ESP_RST_PANIC:    s = "PANIC";    break;
        case ESP_RST_INT_WDT:  s = "WDT";      break;
        case ESP_RST_TASK_WDT: s = "WDT";      break;
        case ESP_RST_WDT:      s = "WDT";      break;
        case ESP_RST_BROWNOUT: s = "BROWNOUT"; break;
        case ESP_RST_DEEPSLEEP:s = "DEEPSLEEP";break;
        case ESP_RST_SDIO:     s = "SDIO";     break;
        default:               s = "UNKNOWN";  break;
    }
    Serial.printf("[BOOT] reset: %s\n", s);
    log_write_event(s);
}

size_t log_get_size() {
    if (!LittleFS.exists(LOG_FILE)) return 0;
    File f = LittleFS.open(LOG_FILE, "r");
    if (!f) return 0;
    size_t sz = f.size();
    f.close();
    return sz;
}

bool log_rotation_paused() {
    size_t free_bytes = LittleFS.totalBytes() - LittleFS.usedBytes();
    return free_bytes < LOG_PAUSE_FREE_BYTES;
}

void log_check_full() {
    if (!log_rotation_paused()) {
        if (warned_full) { warned_full = false; Serial.println("[LOG] resumed"); }
        return;
    }
    if (!warned_full) { warned_full = true; Serial.println("[LOG] PAUSED - FS nearly full"); }
    unsigned long now = millis();
    if (now - last_full_beep >= 60000) {
        last_full_beep = now;
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, BUZZER_MEDIUM);
        delay(100);
        ledcWrite(BUZZER_CHANNEL, 0);
    }
}

void log_clear() {
    if (LittleFS.exists(LOG_FILE)) LittleFS.remove(LOG_FILE);
    write_header_if_new();
    warned_full = false;
    last_full_beep = 0;
    _live_file_start_epoch = time(nullptr);
    save_start_epoch(_live_file_start_epoch);
    Serial.println("[LOG] cleared");
}

static bool is_sealed_name(const char* name) {
    if (!name) return false;
    const char* n = (name[0] == '/') ? name + 1 : name;
    if (strcmp(n, "log.csv") == 0) return false;
    return strncmp(n, LOG_FILENAME_PREFIX, strlen(LOG_FILENAME_PREFIX)) == 0;
}

size_t log_list_sealed(char names[][48], size_t max) {
    size_t count = 0;
    File root = LittleFS.open("/");
    if (!root || !root.isDirectory()) return 0;

    File e = root.openNextFile();
    while (e && count < max) {
        const char* n = e.name();
        if (is_sealed_name(n)) {
            const char* clean = (n[0] == '/') ? n + 1 : n;
            strncpy(names[count], clean, 47);
            names[count][47] = 0;
            count++;
        }
        e = root.openNextFile();
    }
    root.close();
    return count;
}

size_t log_sealed_count() {
    char buf[32][48];
    return log_list_sealed(buf, 32);
}

size_t log_sealed_bytes() {
    char names[32][48];
    size_t n = log_list_sealed(names, 32);
    size_t total = 0;
    for (size_t i = 0; i < n; i++) {
        char p[80];
        snprintf(p, sizeof(p), "/%s", names[i]);
        File f = LittleFS.open(p, "r");
        if (f) { total += f.size(); f.close(); }
    }
    return total;
}

bool log_delete_sealed(const char* name) {
    if (!name || name[0] == 0) return false;
    char p[80];
    if (name[0] == '/') snprintf(p, sizeof(p), "%s", name);
    else                snprintf(p, sizeof(p), "/%s", name);
    if (!LittleFS.exists(p)) return false;
    bool ok = LittleFS.remove(p);
    if (ok) Serial.printf("[LOG] uploaded %s\n", p);
    return ok;
}