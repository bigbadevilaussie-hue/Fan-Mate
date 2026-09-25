#include "WebServer.h"
#include "WiFiManager.h"
#include "FanController.h"
#include "Config.h"

#include <WebServer.h>
#include <ESPmDNS.h>

// ============================================================
//  Web Server — HTTP interface
//
//  V3.00 — minimal: / and /status
// ============================================================

static WebServer server(HTTP_PORT);

// ------------------------------------------------------------
//  GET /
// ------------------------------------------------------------
static void handle_root() {
    String ip    = wifi_ip();
    String rssi  = String(wifi_rssi());
    String ssid  = wifi_ssid_connected();

    String html = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Fan-Mate V3.00</title>
  <style>
    body { font-family: -apple-system, sans-serif; background: #181825; color: #cdd6f4;
           margin: 0; padding: 20px; }
    h1   { color: #89b4fa; }
    .card { background: #232334; padding: 16px; margin: 12px 0; border-radius: 8px; }
    .label { color: #9399b2; font-size: 12px; text-transform: uppercase; }
    .value { font-size: 24px; font-weight: bold; }
    a { color: #89b4fa; }
  </style>
</head>
<body>
  <h1>🌀 Fan-Mate V3.00</h1>
  <div class="card">
    <div class="label">WiFi</div>
    <div class="value">{{SSID}}</div>
    <div class="label">IP</div>
    <div class="value">{{IP}}</div>
    <div class="label">RSSI</div>
    <div class="value">{{RSSI}} dBm</div>
  </div>
  <div class="card">
    <div class="label">Temperature</div>
    <div class="value">{{TEMP}} °C</div>
    <div class="label">Fan</div>
    <div class="value">{{FAN}} %</div>
    <div class="label">RPM</div>
    <div class="value">{{RPM}}</div>
  </div>
  <div class="card">
    <div class="label">Phone</div>
    <div class="value">{{PHONE}}</div>
    <div class="label">Alert</div>
    <div class="value">{{ALERT}}</div>
  </div>
  <div class="card">
    <div class="label">Uptime</div>
    <div class="value">{{UPTIME}} s</div>
  </div>
  <div class="card">
    <a href="/status">📊 /status</a> &nbsp; | &nbsp;
    <a href="/reboot">🔄 Reboot</a>
  </div>
</body>
</html>
)rawliteral";

    // Substitute placeholders with live values
    extern float currentTemp;
    extern int   fanPct;
    extern int   fanRPM;
    extern int   alertState;
    extern bool  phonePresent;

    html.replace("{{SSID}}",   ssid);
    html.replace("{{IP}}",     ip);
    html.replace("{{RSSI}}",   rssi);
    html.replace("{{TEMP}}",   String(currentTemp, 1));
    html.replace("{{FAN}}",    String(fanPct));
    html.replace("{{RPM}}",    String(fanRPM));
    html.replace("{{PHONE}}",  phonePresent ? "YES" : "NO");
    html.replace("{{ALERT}}",  String(alertState));
    html.replace("{{UPTIME}}", String(millis() / 1000));

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
    json += "\"alert\":" + String(alertState);
    json += "}";

    server.send(200, "application/json", json);
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

    server.on("/",        HTTP_GET, handle_root);
    server.on("/status",  HTTP_GET, handle_status);
    server.on("/reboot",  HTTP_GET, handle_reboot);

    // 404 handler
    server.onNotFound([]() {
        server.send(404, "text/plain", "404 Not Found");
    });

    server.begin();

    Serial.printf("[HTTP] server started on port %d\n", HTTP_PORT);
    Serial.printf("[HTTP] http://%s/\n", wifi_mdns_name().c_str());
    Serial.printf("[HTTP] http://%s/\n", wifi_ip().c_str());
}

// ------------------------------------------------------------
//  Loop
// ------------------------------------------------------------
void server_loop() {
    server.handleClient();
}

// ------------------------------------------------------------
//  Version
// ------------------------------------------------------------
String server_version() {
    return String(FAN_MATE_VERSION);
}