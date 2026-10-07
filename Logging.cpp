#include "Logging.h"
#include <mbedtls/base64.h>
#include "Config.h"
#include "DisplayManager.h"
#include "WiFiManager.h"
#include "SerialBuffer.h"
#include "AutoBoost.h"
#include "Settings.h"

#include <LittleFS.h>
#include <HTTPClient.h>
#include <Preferences.h>
#include <time.h>
#include <sys/time.h>
#include <esp_system.h>

extern float weather_get_temp();

// NTC on GPIO 0, MF52AT 10k. readNTC() returns -99 if unreadable.
static float room_get_temp() {
    extern float readNTC();
    return readNTC();
}
extern float currentTemp;

static unsigned long last_full_beep = 0;
static bool          warned_full    = false;
static const char* LOG_FILE = LOG_FILE_LIVE;

// Forward declarations
static void _invalidate_free_bytes_cache();

static time_t _live_file_start_epoch = 0;
static bool _logging_paused = false;

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
    f.println(LOG_HEADER);
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
    f.println(LOG_HEADER);
    f.close();
    _live_file_start_epoch = start_epoch;
    save_start_epoch(start_epoch);
}

// ------------------------------------------------------------
//  Google Drive upload — POST sealed log to Apps Script
//  HTTP 302 is treated as success (Apps Script redirect pattern).
// ------------------------------------------------------------
bool upload_to_github(const char* sealed_path, const char* name, const char* subdir) {
    File f = LittleFS.open(sealed_path, "r");
    if (!f) {
        log_print("[GH] cannot open %s\n", sealed_path);
        return false;
    }
    size_t fileSize = f.size();
    if (fileSize == 0) {
        log_print("[GH] %s empty, skipping\n", name);
        f.close();
        return true;
    }
    if (fileSize > 500000) {
        log_print("[GH] %s too big (%u), skipping\n", name, (unsigned)fileSize);
        f.close();
        return false;
    }

    uint8_t* buf = (uint8_t*)malloc(fileSize);
    if (!buf) { f.close(); return false; }
    f.read(buf, fileSize);
    f.close();

    size_t b64_len = 4 * ((fileSize + 2) / 3) + 1;
    char* b64 = (char*)malloc(b64_len);
    if (!b64) { free(buf); return false; }
    size_t olen = 0;
    mbedtls_base64_encode((unsigned char*)b64, b64_len, &olen, buf, fileSize);
    b64[olen] = 0;
    free(buf);

    struct tm ti;
    time_t now = time(nullptr);
    localtime_r(&now, &ti);
    char path[128];
    snprintf(path, sizeof(path), "%s/%04d-%02d/%s",
             subdir, ti.tm_year + 1900, ti.tm_mon + 1, name);

    String body;
    body.reserve(olen + 256);
    body = "{\"message\":\"seal ";
    body += name;
    body += "\",\"content\":\"";
    body += b64;
    body += "\",\"branch\":\"";
    body += GITHUB_BRANCH;
    body += "\"}";
    free(b64);

    char url[256];
    snprintf(url, sizeof(url),
             "https://api.github.com/repos/%s/%s/contents/%s",
             GITHUB_OWNER, GITHUB_REPO, path);

    log_print("[GH] PUT %s (%u bytes)\n", path, (unsigned)fileSize);

    HTTPClient http;
    http.setReuse(false);
    http.setTimeout(20000);
    http.setFollowRedirects(HTTPC_DISABLE_FOLLOW_REDIRECTS);

    int code = -1;
    for (int attempt = 1; attempt <= 2; attempt++) {
        if (!http.begin(url)) break;
        http.addHeader("Authorization", String("Bearer ") + GITHUB_TOKEN);
        http.addHeader("Accept", "application/vnd.github+json");
        http.addHeader("User-Agent", "Fan-Mate");
        http.addHeader("Content-Type", "application/json");
        code = http.PUT((uint8_t*)body.c_str(), body.length());
        if (code > 0) break;
        http.end();
        delay(500);
    }

    bool ok = (code == 201 || code == 200);
    log_print("[GH] %s %s http=%d\n", name, ok ? "OK" : "FAIL", code);
    if (!ok && code > 0) {
        String resp = http.getString();
        if (resp.length() > 0) {
            log_print("[GH] resp: %s\n", resp.substring(0, 200).c_str());
        }
    }
    http.end();
    return ok;
}
static bool seal_live(time_t name_epoch) {
    if (!LittleFS.exists(LOG_FILE)) return false;

    char sealed[64];
    if (!build_sealed_name(name_epoch, sealed, sizeof(sealed))) return false;

    char sealed_path[80];
    snprintf(sealed_path, sizeof(sealed_path), "/%s", sealed);

    if (LittleFS.exists(sealed_path)) {
        log_print("[LOG] seal collision: %s\n", sealed_path);
        return false;
    }

    if (!LittleFS.rename(LOG_FILE, sealed_path)) {
        log_print("[LOG] rename failed\n");
        return false;
    }

    log_print("[LOG] sealed %s\n", sealed_path);

    // Upload to Drive (best-effort, non-fatal)
    upload_to_github(sealed_path, sealed, "logs");

    time_t now = time(nullptr);
    open_fresh_live(now);

    {
        size_t total = LittleFS.totalBytes();
        size_t used  = LittleFS.usedBytes();
        if (total > 0) {
            log_print("[STORAGE] %u%% used (%u/%u KB, %u sealed)\n",
                      (unsigned)((used * 100) / total),
                      (unsigned)(used / 1024),
                      (unsigned)(total / 1024),
                      (unsigned)log_sealed_count());
        }
    }

    log_write_event("SEAL");
    return true;
}

void log_rotate_check() {
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
        log_print("[LOG] time jump > 24h — resetting start epoch\n");
        _live_file_start_epoch = now;
        save_start_epoch(now);
        return;
    }

    struct tm now_ti, start_ti;
    localtime_r(&now, &now_ti);
    localtime_r(&_live_file_start_epoch, &start_ti);

    if (now_ti.tm_hour != start_ti.tm_hour ||
        now_ti.tm_yday != start_ti.tm_yday ||
        now_ti.tm_year != start_ti.tm_year) {
        if (log_rotation_paused()) {
            log_print("[LOG] rotation paused, not sealing\n");
            return;
        }
        seal_live(_live_file_start_epoch);
    }
}

void log_boot_recovery() {
    if (!LittleFS.exists(LOG_FILE)) return;

    time_t now = time(nullptr);
    bool time_ok = (now > 1700000000UL && now < 4102444800UL);

    size_t rows = log_count_live_rows();
    if (rows < LOG_SEAL_MIN_ROWS) {
        log_print("[LOG] boot: %u rows (below min) — discarding\n", (unsigned)rows);
        LittleFS.remove(LOG_FILE);
        clear_start_epoch();
        write_header_if_new();
        _live_file_start_epoch = time_ok ? now : 0;
        if (time_ok) save_start_epoch(_live_file_start_epoch);
        return;
    }
    if (!time_ok) {
        // v4.29: preserve rows under recovery name; don't lose data
        char rec[48];
        snprintf(rec, sizeof(rec), "/recovered-%lu.csv", (unsigned long)(millis()/1000));
        LittleFS.rename(LOG_FILE, rec);
        log_print("[LOG] boot: %u rows, no clock — preserved as %s\n",
                  (unsigned)rows, rec);
        write_header_if_new();
        _live_file_start_epoch = 0;
        clear_start_epoch();
        return;
    }

    time_t stored = load_start_epoch();
    time_t name_epoch = (stored > 0) ? stored : now;

    log_print("[LOG] boot: sealing %u rows\n", (unsigned)rows);

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
    log_print("[LOG] mounted used=%u/%u\n",
              (unsigned)LittleFS.usedBytes(),
              (unsigned)LittleFS.totalBytes());
    write_header_if_new();
    _live_file_start_epoch = load_start_epoch();
    if (_live_file_start_epoch == 0) {
        _live_file_start_epoch = time(nullptr);
    }
}

void log_seal_now() {
    time_t now = time(nullptr);
    seal_live(now);
}

void log_write_config_snapshot() {
    time_t now = time(nullptr);
    struct tm ti;
    localtime_r(&now, &ti);
    char name[64];
    snprintf(name, sizeof(name), "%s%s-%04d%02d%02d-%02d%02d%02d.csv",
             CONFIG_FILENAME_PREFIX, FAN_MATE_VERSION,
             ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday,
             ti.tm_hour, ti.tm_min, ti.tm_sec);
    char path[80];
    snprintf(path, sizeof(path), "/%s", name);

    File f = LittleFS.open(path, "w");
    if (!f) {
        log_print("[CFG] snapshot open failed: %s\n", name);
        return;
    }
    f.println(CONFIG_HEADER);

    char ts[24];
    snprintf(ts, sizeof(ts), "%04d-%02d-%02d %02d:%02d:%02d",
             ti.tm_year + 1900, ti.tm_mon + 1, ti.tm_mday,
             ti.tm_hour, ti.tm_min, ti.tm_sec);

    f.printf("%s,temp.gear1,%.1f\n",          ts, config.tempGear1);
    f.printf("%s,temp.gear2,%.1f\n",          ts, config.tempGear2);
    f.printf("%s,temp.gear3,%.1f\n",          ts, config.tempGear3);
    f.printf("%s,temp.gear4,%.1f\n",          ts, config.tempGear4);
    f.printf("%s,temp.hysteresis,%.1f\n",     ts, config.tempHysteresis);
    f.printf("%s,night.start,%d\n",           ts, config.nightStart);
    f.printf("%s,night.end,%d\n",             ts, config.nightEnd);
    f.printf("%s,night.nightMax,%d\n",        ts, config.nightMax);
    f.printf("%s,boost.mode,%d\n",            ts, config.boostMode);
    f.printf("%s,boost.normal.threshold,%d\n", ts, config.boostNormal.threshold);
    f.printf("%s,boost.normal.on_hold,%d\n",   ts, config.boostNormal.on_hold);
    f.printf("%s,boost.normal.off_hold,%d\n",  ts, config.boostNormal.off_hold);
    f.printf("%s,boost.aggr.threshold,%d\n",   ts, config.boostAggr.threshold);
    f.printf("%s,boost.aggr.on_hold,%d\n",     ts, config.boostAggr.on_hold);
    f.printf("%s,boost.aggr.off_hold,%d\n",    ts, config.boostAggr.off_hold);
    f.close();

    log_print("[CFG] snapshot: %s\n", name);
    upload_to_github(path, name, "config");
}

void log_flush_seal() {
    if (!LittleFS.exists(LOG_FILE)) {
        _logging_paused = true;
        return;
    }
    time_t now = time(nullptr);
    seal_live(now);
    _logging_paused = true;
    log_print("[LOG] paused for sleep\n");
}

void log_resume() {
    _logging_paused = false;
    time_t now = time(nullptr);
    if (LittleFS.exists(LOG_FILE) && log_count_live_rows() > 0) {
        char rec[64];
        snprintf(rec, sizeof(rec), "/recovered-%lu.csv",
                 (unsigned long)(now ? now : millis()/1000));
        LittleFS.rename(LOG_FILE, rec);
        log_print("[LOG] preserved orphan as %s\n", rec);
    }
    open_fresh_live(now);
    log_print("[LOG] resumed\n");
}

void log_write(float temp, float net_kbps, int boost, int fan, int rpm) {
    if (_logging_paused) return;
    if (log_rotation_paused()) return;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    float rt = room_get_temp();
    float wt = weather_get_temp();
    if (rt < -90.0f) {
        if (wt < -90.0f)
            f.printf("%s,%.1f,%.1f,%d,%d,%d,,,\n",
                     t.c_str(), temp, net_kbps, boost, fan, rpm);
        else
            f.printf("%s,%.1f,%.1f,%d,%d,%d,,%.1f,\n",
                     t.c_str(), temp, net_kbps, boost, fan, rpm, wt);
    } else {
        f.printf("%s,%.1f,%.1f,%d,%d,%d,,%.1f,%.1f\n",
                 t.c_str(), temp, net_kbps, boost, fan, rpm,
                 weather_get_temp(), rt);
    }
    f.close();
    _invalidate_free_bytes_cache();
}

static void sanitize_event(char* dst, size_t n, const char* src) {
    size_t j = 0;
    for (size_t i = 0; src[i] && j + 1 < n; i++) {
        dst[j++] = (src[i] == ',') ? ';' : src[i];
    }
    dst[j] = 0;
}

extern float lastNetKbps;
extern int   fanPct;
extern int   fanRPM;

extern bool opal_ok_recently();   // from OpalClient

void log_write_event(const char* event) {
    if (_logging_paused) return;
    if (log_rotation_paused()) return;
    File f = LittleFS.open(LOG_FILE, "a");
    if (!f) return;
    String t = log_time_string();
    char safe[64];
    sanitize_event(safe, sizeof(safe), event);
    float rt = room_get_temp();
    bool net_ok = opal_ok_recently();
    if (rt < -90.0f) {
        if (net_ok) {
            f.printf("%s,%.1f,%.1f,%d,%d,%d,%s,%.1f,\n",
                     t.c_str(), currentTemp, lastNetKbps,
                     auto_boost_gear() > 0 ? 1 : 0,
                     fanPct, fanRPM,
                     safe, weather_get_temp());
        } else {
            f.printf("%s,%.1f,,%d,%d,%d,%s,%.1f,\n",
                     t.c_str(), currentTemp,
                     auto_boost_gear() > 0 ? 1 : 0,
                     fanPct, fanRPM,
                     safe, weather_get_temp());
        }
    } else {
        if (net_ok) {
            f.printf("%s,%.1f,%.1f,%d,%d,%d,%s,%.1f,%.1f\n",
                     t.c_str(), currentTemp, lastNetKbps,
                     auto_boost_gear() > 0 ? 1 : 0,
                     fanPct, fanRPM,
                     safe, weather_get_temp(), rt);
        } else {
            f.printf("%s,%.1f,,%d,%d,%d,%s,%.1f,%.1f\n",
                     t.c_str(), currentTemp,
                     auto_boost_gear() > 0 ? 1 : 0,
                     fanPct, fanRPM,
                     safe, weather_get_temp(), rt);
        }
    }
    f.close();
    _invalidate_free_bytes_cache();
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
    log_print("[BOOT] reset: %s\n", s);
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

static bool log_evict_oldest() {
    char all[LOG_MAX_SEALED][48];
    size_t total = log_list_sealed(all, LOG_MAX_SEALED);
    char names[LOG_MAX_SEALED][48];
    size_t n = 0;
    for (size_t i = 0; i < total; i++) {
        if (strncmp(all[i], LOG_FILENAME_PREFIX,
                    strlen(LOG_FILENAME_PREFIX)) == 0) {
            strncpy(names[n], all[i], 47);
            names[n][47] = 0;
            n++;
        }
    }
    if (n <= LOG_KEEP_MIN) {
        log_print("[LOG] evict: only %u log files, keeping all\n", (unsigned)n);
        return false;
    }
    // Sort by filename. Filenames are log-<fw>-<YYYYMMDD>-<HHMM>.csv;
    // lexicographic order is chronological within a firmware version.
    for (size_t i = 1; i < n; i++) {
        for (size_t j = i; j > 0 && strcmp(names[j-1], names[j]) > 0; j--) {
            char tmp[48];
            strncpy(tmp, names[j-1], 48);
            strncpy(names[j-1], names[j], 48);
            strncpy(names[j], tmp, 48);
        }
    }
    char p[80];
    snprintf(p, sizeof(p), "/%s", names[0]);
    bool ok = LittleFS.remove(p);
    log_print("[LOG] evict: removed %s (%s)\n", p, ok ? "OK" : "FAIL");
    return ok;
}

// Cached free bytes — refreshed once per tick, not on every call
static size_t _cached_free_bytes  = 0;
static unsigned long _cached_at_ms = 0;
static const unsigned long FREE_BYTES_TTL_MS = 14000;   // just under tick_15s

static size_t _get_free_bytes() {
    unsigned long now = millis();
    if (now - _cached_at_ms > FREE_BYTES_TTL_MS || _cached_at_ms == 0) {
        _cached_free_bytes = LittleFS.totalBytes() - LittleFS.usedBytes();
        _cached_at_ms = now;
    }
    return _cached_free_bytes;
}

static void _invalidate_free_bytes_cache() {
    _cached_at_ms = 0;
}

bool log_rotation_paused() {
    size_t free_bytes = _get_free_bytes();
    if (free_bytes >= LOG_PAUSE_FREE_BYTES) return false;

    // Try to evict oldest sealed file to reclaim space
    while (free_bytes < LOG_PAUSE_FREE_BYTES) {
        if (!log_evict_oldest()) break;
        _invalidate_free_bytes_cache();
        free_bytes = _get_free_bytes();
    }
    return free_bytes < LOG_PAUSE_FREE_BYTES;
}

void log_check_full() {
    if (!log_rotation_paused()) {
        if (warned_full) { warned_full = false; log_print("[LOG] resumed\n"); }
        return;
    }
    if (!warned_full) { warned_full = true; log_print("[LOG] PAUSED - FS nearly full\n"); }
    unsigned long now = millis();
    if (now - last_full_beep >= 60000) {
        last_full_beep = now;
        tone(BUZZER_PIN, BUZZER_TONE_HZ);
        delay(100);
        noTone(BUZZER_PIN);
        delay(100);
        tone(BUZZER_PIN, BUZZER_TONE_HZ);
        delay(100);
        noTone(BUZZER_PIN);
    }
}

void log_clear() {
    if (LittleFS.exists(LOG_FILE)) LittleFS.remove(LOG_FILE);
    write_header_if_new();
    warned_full = false;
    last_full_beep = 0;
    _live_file_start_epoch = time(nullptr);
    save_start_epoch(_live_file_start_epoch);
    log_write_event("CLEAR");
    log_print("[LOG] cleared\n");
}

static bool is_sealed_name(const char* name) {
    if (!name) return false;
    const char* n = (name[0] == '/') ? name + 1 : name;
    if (strcmp(n, "log.csv") == 0) return false;
    if (strncmp(n, LOG_FILENAME_PREFIX, strlen(LOG_FILENAME_PREFIX)) == 0) return true;
    if (strncmp(n, CONFIG_FILENAME_PREFIX, strlen(CONFIG_FILENAME_PREFIX)) == 0) return true;
    return false;
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
    char buf[LOG_MAX_SEALED][48];
    return log_list_sealed(buf, LOG_MAX_SEALED);
}

size_t log_sealed_bytes() {
    char names[LOG_MAX_SEALED][48];
    size_t n = log_list_sealed(names, LOG_MAX_SEALED);
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
    if (ok) log_print("[LOG] deleted %s\n", p);
    return ok;
}