#include "WebServer.h"
#include "WiFiManager.h"
#include "FanController.h"
#include "Logging.h"
#include "Settings.h"
#include "OpalClient.h"
#include "AutoBoost.h"
#include "Config.h"

#include <WebServer.h>
#include <ESPmDNS.h>
#include <LittleFS.h>
#include <Update.h>
#include <ArduinoJson.h>
#include <time.h>
#include <sys/time.h>

// ============================================================
//  Web Server — HTTP interface
//  V3.20 — adds /time and /ota
// ============================================================

static WebServer server(HTTP_PORT);

extern volatile bool otaInProgress;
static bool otaStarted = false;
static unsigned long host_last_ms = 0;

static void note_host() { host_last_ms = millis(); }

// ------------------------------------------------------------

static void handle_serial_page() {
    String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Fan-Mate Serial</title>
<style>
body{font-family:ui-monospace,monospace;background:#181825;color:#cdd6f4;padding:20px;font-size:13px}
h1{color:#89b4fa}
#log{background:#232334;padding:14px;border-radius:8px;height:80vh;overflow-y:auto;white-space:pre-wrap;word-break:break-all}
a{color:#89b4fa}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
</style>
<script>
function refresh(){
  fetch('/serial-raw')
    .then(r=>r.text())
    .then(t=>{
      const el=document.getElementById('log');
      const at_bottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
      el.textContent = t;
      if(at_bottom) el.scrollTop = el.scrollHeight;
    });
}
setInterval(refresh, 2000);
window.onload = refresh;
</script>
</head><body>
<div class="top"><h1>Fan-Mate Serial</h1><a href="/">dashboard</a></div>
<div id="log">loading...</div>
</body></html>
)rawliteral";
    server.send(200, "text/html", html);
}

static void handle_serial_raw() {
    extern String get_serial_dump();
    server.send(200, "text/plain", get_serial_dump());
}

static void handle_root() {
    note_host();
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;
    extern float lastNetKbps;

    String html = R"rawliteral(
<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Fan-Mate</title>
<style>
body{font-family:-apple-system,sans-serif;background:#181825;color:#cdd6f4;margin:0;padding:20px}
h1{color:#89b4fa}.c{background:#232334;padding:14px;margin:10px 0;border-radius:8px}
.l{color:#9399b2;font-size:11px;text-transform:uppercase}.v{font-size:22px;font-weight:bold}
a{color:#89b4fa}
</style></head><body>
<h1>🌀 Fan-Mate V{{VERSION}}</h1>
<div class="c"><div class="l">WiFi</div><div class="v">{{SSID}} {{IP}}</div>
<div class="l">RSSI</div><div class="v">{{RSSI}} dBm</div></div>
<div class="c"><div class="l">Temp</div><div class="v">{{TEMP}} °C</div>
<div class="l">Fan</div><div class="v">{{FAN}} %</div>
<div class="l">RPM</div><div class="v">{{RPM}}</div></div>
<div class="c"><div class="l">Phone</div><div class="v">{{PHONE}}</div>
<div class="l">Alert</div><div class="v">{{ALERT}}</div></div>
<div class="c"><a href="/status">status</a> | <a href="/serial">serial</a> | <a href="/log.csv">log.csv</a> | <a href="/reboot">reboot</a></div>
</body></html>
)rawliteral";

    html.replace("{{SSID}}",  wifi_ssid_connected());
    html.replace("{{IP}}",    wifi_ip());
    html.replace("{{RSSI}}",  String(wifi_rssi()));
    html.replace("{{TEMP}}",  String(currentTemp, 1));
    html.replace("{{FAN}}",   String(fanPct));
    html.replace("{{RPM}}",   String(fanRPM));
    html.replace("{{PHONE}}", phonePresent ? "YES" : "NO");
    html.replace("{{ALERT}}", String(alertState));
    html.replace("{{VERSION}}", FAN_MATE_VERSION);

    server.send(200, "text/html", html);
}

// ------------------------------------------------------------
static void handle_status() {
    note_host();
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;
    extern float lastNetKbps;

    String json = "{";
    json += "\"fw\":\"" + String(FAN_MATE_VERSION) + "\",";
    json += "\"uptime\":" + String(millis() / 1000) + ",";
    json += "\"ip\":\"" + wifi_ip() + "\",";
    json += "\"rssi\":" + String(wifi_rssi()) + ",";
    json += "\"ssid\":\"" + wifi_ssid_connected() + "\",";
    json += "\"temp\":" + String(currentTemp, 2) + ",";
    json += "\"fan\":" + String(fanPct) + ",";
    json += "\"rpm\":" + String(fanRPM) + ",";
    json += "\"phone\":" + String(phonePresent ? 1 : 0) + ",";
    json += "\"alert\":" + String(alertState) + ",";
    json += "\"boost\":" + String(auto_boost_is_active() ? 1 : 0) + ",";
    json += "\"net_kbps\":" + String(lastNetKbps, 1) + ",";
    json += "\"opal\":" + String(opal_logged_in() ? 1 : 0) + ",";
    unsigned long since_host = (host_last_ms > 0) ? (millis() - host_last_ms) : 999999;
    int host_alive = (since_host < 60000) ? 1 : 0;
    json += "\"host\":" + String(host_alive) + ",";
    json += "\"host_last_seen\":" + String(since_host / 1000) + ",";
    int sleep_countdown = 0;
    if (sys_state == STATE_ACTIVE && phone_absent_since > 0) {
        unsigned long elapsed = (millis() - phone_absent_since) / 1000;
        int remaining = config.phoneTestDelay - (int)elapsed;
        if (remaining < 0) remaining = 0;
        sleep_countdown = remaining;
    }
    json += "\"sleep\":" + String(sys_state == STATE_LIGHT_SLEEP ? 1 : 0) + ",";
    json += "\"sleep_countdown\":" + String(sleep_countdown) + ",";
    json += "\"log_size\":" + String(log_get_size()) + ",";
    json += "\"log_full\":" + String(log_is_full() ? 1 : 0);
    json += "}";

    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_config_get() {
    note_host();
    String json = "{";

    json += "\"fan\":{";
    json += "\"tempOn\":" + String(config.tempOn, 1) + ",";
    json += "\"tempFull\":" + String(config.tempFull, 1) + ",";
    json += "\"nightMax\":" + String(config.nightMax);
    json += "},";

    json += "\"alarm\":{";
    json += "\"mode\":\"" + config.alarmMode + "\",";
    json += "\"warning\":" + String(config.alarmWarning, 1) + ",";
    json += "\"panic\":" + String(config.alarmPanic, 1);
    json += "},";

    json += "\"night\":{";
    json += "\"mode\":\"" + config.nightMode + "\",";
    json += "\"start\":" + String(config.nightStart) + ",";
    json += "\"end\":" + String(config.nightEnd);
    json += "},";

    json += "\"phone\":{";
    json += "\"mode\":\"" + config.phoneMode + "\"";
    json += "},";

    json += "\"boost\":{";
    json += "\"enabled\":" + String(config.boostEnabled ? 1 : 0) + ",";
    json += "\"threshold\":" + String(config.boostThreshold) + ",";
    json += "\"hold\":" + String(config.boostHold);
    json += "},";

    json += "\"bench\":{";
    json += "\"mode\":" + String(config.benchMode ? 1 : 0);
    json += "}";

    json += "}";
    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_config_post() {
    note_host();
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "no body");
        return;
    }

    String body = server.arg("plain");
    Serial.printf("[HTTP] POST /config: %s\n", body.c_str());

    settings_apply_json(body.c_str());
    server.send(200, "text/plain", "OK");
}

// ------------------------------------------------------------
static void handle_time_post() {
    note_host();
    if (!server.hasArg("plain")) {
        server.send(400, "text/plain", "no body");
        return;
    }

    String body = server.arg("plain");
    StaticJsonDocument<128> doc;
    DeserializationError err = deserializeJson(doc, body);
    if (err) {
        server.send(400, "text/plain", "bad json");
        return;
    }

    uint32_t epoch = doc["epoch"] | 0;
    if (epoch < 1700000000UL || epoch > 4102444800UL) {
        server.send(400, "text/plain", "bad epoch");
        return;
    }

    struct timeval tv;
    tv.tv_sec  = epoch;
    tv.tv_usec = 0;
    settimeofday(&tv, nullptr);
    setenv("TZ", "AEST-10", 1);
    tzset();

    Serial.printf("[TIME] synced: %lu\n", (unsigned long)epoch);
    server.send(200, "text/plain", "OK");
}

// ------------------------------------------------------------
static void handle_log_download() {
    note_host();
    if (!LittleFS.exists("/log.csv")) {
        server.send(404, "text/plain", "no log");
        return;
    }

    File f = LittleFS.open("/log.csv", "r");
    if (!f) {
        server.send(500, "text/plain", "open failed");
        return;
    }

    server.streamFile(f, "text/csv");
    f.close();
}

// ------------------------------------------------------------
static void handle_log_info() {
    note_host();
    String json = "{";
    json += "\"size\":" + String(log_get_size()) + ",";
    json += "\"max\":" + String(LOG_MAX_SIZE) + ",";
    json += "\"full\":" + String(log_is_full() ? 1 : 0);
    json += "}";
    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_log_clear() {
    note_host();
    log_clear();
    server.send(200, "text/plain", "cleared");
}

// ------------------------------------------------------------
static void handle_ota_upload() {
    HTTPUpload& upload = server.upload();

    if (upload.status == UPLOAD_FILE_START) {
        Serial.printf("[OTA] start: %s\n", upload.filename.c_str());
        otaInProgress = true;
        otaStarted = true;

        if (!Update.begin(UPDATE_SIZE_UNKNOWN)) {
            Serial.printf("[OTA] begin FAILED: %s\n", Update.errorString());
            otaStarted = false;
        }
    } else if (upload.status == UPLOAD_FILE_WRITE) {
        if (otaStarted) {
            if (Update.write(upload.buf, upload.currentSize) != upload.currentSize) {
                Serial.printf("[OTA] write FAILED: %s\n", Update.errorString());
                otaStarted = false;
            }
        }
    } else if (upload.status == UPLOAD_FILE_END) {
        if (otaStarted) {
            if (Update.end(true)) {
                Serial.printf("[OTA] OK: %u bytes\n", upload.totalSize);
            } else {
                Serial.printf("[OTA] end FAILED: %s\n", Update.errorString());
            }
        }
    }
}

static void handle_ota_done() {
    if (Update.hasError()) {
        otaInProgress = false;
        server.send(500, "text/plain",
                    "FAIL: " + String(Update.errorString()));
    } else {
        log_write_event("OTA");
        server.send(200, "text/plain", "OK, rebooting");
        delay(500);
        ESP.restart();
    }
}

// ------------------------------------------------------------
static void handle_reboot() {
    note_host();
    log_write_event("REBOOT");
    server.send(200, "text/plain", "Rebooting...");
    delay(500);
    ESP.restart();
}

// ------------------------------------------------------------
void server_setup() {
    if (!wifi_connected()) {
        Serial.println("[HTTP] WiFi not connected — server not started");
        return;
    }

    server.on("/",           HTTP_GET,  handle_root);
    server.on("/status",     HTTP_GET,  handle_status);
    server.on("/config",     HTTP_GET,  handle_config_get);
    server.on("/config",     HTTP_POST, handle_config_post);
    server.on("/time",       HTTP_POST, handle_time_post);
    server.on("/log.csv",    HTTP_GET,  handle_log_download);
    server.on("/log/info",   HTTP_GET,  handle_log_info);
    server.on("/log/clear",  HTTP_POST, handle_log_clear);
    server.on("/serial",     HTTP_GET,  handle_serial_page);
    server.on("/serial-raw", HTTP_GET,  handle_serial_raw);
    server.on("/reboot",     HTTP_GET,  handle_reboot);
    server.on("/ota",        HTTP_POST, handle_ota_done, handle_ota_upload);

    server.onNotFound([]() {
        server.send(404, "text/plain", "404");
    });

    server.begin();

    Serial.printf("[HTTP] server started on port %d\n", HTTP_PORT);
    Serial.printf("[HTTP] http://%s/\n", wifi_mdns_name().c_str());
    Serial.printf("[HTTP] http://%s/\n", wifi_ip().c_str());
    Serial.println("[HTTP] endpoints: /, /status, /config, /time, /log.csv, /log/info, /log/clear, /ota, /reboot");
}

void server_loop() {
    server.handleClient();
}

String server_version() {
    return String(FAN_MATE_VERSION);
}