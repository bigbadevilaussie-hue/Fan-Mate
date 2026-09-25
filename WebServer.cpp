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

// ============================================================
//  Web Server — HTTP interface
//  V2.24 — fan.mode removed
// ============================================================

static WebServer server(HTTP_PORT);

// ------------------------------------------------------------
//  GET / — dashboard
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
<h1>🌀 Fan-Mate V2.24</h1>
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
//  GET /status
// ------------------------------------------------------------
static void handle_status() {
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;

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
    json += "\"log_size\":" + String(log_get_size()) + ",";
    json += "\"log_full\":" + String(log_is_full() ? 1 : 0);
    json += "}";

    server.send(200, "application/json", json);
}

// ------------------------------------------------------------
//  GET /config — no fan.mode
// ------------------------------------------------------------
static void handle_config_get() {
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
//  POST /config
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
//  GET /log.csv
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
//  GET /log/info
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
//  POST /log/clear
// ------------------------------------------------------------
static void handle_log_clear() {
    log_clear();
    server.send(200, "text/plain", "cleared");
}

// ------------------------------------------------------------
//  GET /reboot
// ------------------------------------------------------------
static void handle_reboot() {
    server.send(200, "text/plain", "Rebooting...");
    delay(500);
    ESP.restart();
}

// ------------------------------------------------------------
//  Setup
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
    server.on("/log.csv",    HTTP_GET,  handle_log_download);
    server.on("/log/info",   HTTP_GET,  handle_log_info);
    server.on("/log/clear",  HTTP_POST, handle_log_clear);
    server.on("/reboot",     HTTP_GET,  handle_reboot);

    server.onNotFound([]() {
        server.send(404, "text/plain", "404");
    });

    server.begin();

    Serial.printf("[HTTP] server started on port %d\n", HTTP_PORT);
    Serial.printf("[HTTP] http://%s/\n", wifi_mdns_name().c_str());
    Serial.printf("[HTTP] http://%s/\n", wifi_ip().c_str());
}

void server_loop() {
    server.handleClient();
}

String server_version() {
    return String(FAN_MATE_VERSION);
}