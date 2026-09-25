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
//  V3.32 — sleep field, sleep_countdown, new boost structure
// ============================================================

static WebServer server(HTTP_PORT);

extern volatile bool otaInProgress;
static bool otaStarted = false;


// ------------------------------------------------------------
static void handle_root() {
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;

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
<h1>🌀 Fan-Mate V3.32</h1>
<div class="c"><div class="l">WiFi</div><div class="v">{{SSID}} {{IP}}</div>
<div class="l">RSSI</div><div class="v">{{RSSI}} dBm</div></div>
<div class="c"><div class="l">Temp</div><div class="v">{{TEMP}} °C</div>
<div class="l">Fan</div><div class="v">{{FAN}} %</div>
<div class="l">RPM</div><div class="v">{{RPM}}</div></div>
<div class="c"><div class="l">Phone</div><div class="v">{{PHONE}}</div>
<div class="l">Alert</div><div class="v">{{ALERT}}</div></div>
<div class="c"><a href="/status">status</a> | <a href="/log.csv">log.csv</a> | <a href="/reboot">reboot</a></div>
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

    server.send(200, "text/html", html);
}

// ------------------------------------------------------------
static void handle_status() {
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;
    extern float lastNetKbps;

    int sleep_countdown = 0;
    if (sys_state == 0 && phone_absent_since > 0) {
        unsigned long elapsed = (millis() - phone_absent_since) / 1000;
        int remaining = config.phoneTestDelay - (int)elapsed;
        if (remaining < 0) remaining = 0;
        sleep_countdown = remaining;
    }

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
    json += "\"opal\":" + String(opal_logged_in() ? 1 : 0) + ",";
    json += "\"net_kbps\":" + String(lastNetKbps, 1) + ",";
    json += "\"sleep\":" + String(sys_state == 1 ? 1 : 0) + ",";
    json += "\"sleep_countdown\":" + String(sleep_countdown) + ",";
    json += "\"log_size\":" + String(log_get_size()) + ",";
    json += "\"log_full\":" + String(log_is_full() ? 1 : 0);
    json += "}";

    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_config_get() {
    String json = "{";

    // Boost — new nested structure
    json += "\"boost\":{";
    json += "\"mode\":" + String(config.boostMode) + ",";

    json += "\"normal\":{";
    json += "\"threshold\":" + String(config.boostNormal.threshold) + ",";
    json += "\"on_hold\":"   + String(config.boostNormal.on_hold)   + ",";
    json += "\"off_hold\":"  + String(config.boostNormal.off_hold);
    json += "},";

    json += "\"aggr\":{";
    json += "\"threshold\":" + String(config.boostAggr.threshold) + ",";
    json += "\"on_hold\":"   + String(config.boostAggr.on_hold)   + ",";
    json += "\"off_hold\":"  + String(config.boostAggr.off_hold);
    json += "},";

    // Convenience fields — active mode's current values
    json += "\"threshold\":" + String(auto_boost_threshold()) + ",";
    json += "\"on_hold\":"   + String(auto_boost_on_hold())   + ",";
    json += "\"off_hold\":"  + String(auto_boost_off_hold());
    json += "},";

    // Alarm — 3 levels
    json += "\"alarm\":{";
    json += "\"mode\":\"" + config.alarmMode + "\",";
    json += "\"warning\":" + String(config.alarmWarning, 1) + ",";
    json += "\"panic\":"   + String(config.alarmPanic, 1)   + ",";
    json += "\"kill\":"    + String(config.alarmKill, 1);
    json += "},";

    // Night
    json += "\"night\":{";
    json += "\"mode\":\"" + config.nightMode + "\",";
    json += "\"start\":" + String(config.nightStart) + ",";
    json += "\"end\":"   + String(config.nightEnd)   + ",";
    json += "\"nightMax\":" + String(config.nightMax);
    json += "},";

    // Phone
    json += "\"phone\":{";
    json += "\"mode\":\"" + config.phoneMode + "\",";
    json += "\"test_delay\":" + String(config.phoneTestDelay);
    json += "}";

    json += "}";
    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_config_post() {
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
    String json = "{";
    json += "\"size\":" + String(log_get_size()) + ",";
    json += "\"max\":" + String(LOG_MAX_SIZE) + ",";
    json += "\"full\":" + String(log_is_full() ? 1 : 0);
    json += "}";
    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
static void handle_log_clear() {
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
        server.send(200, "text/plain", "OK, rebooting");
        delay(500);
        ESP.restart();
    }
}

// ------------------------------------------------------------
static void handle_reboot() {
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