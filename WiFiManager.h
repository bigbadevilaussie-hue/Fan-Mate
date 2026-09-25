#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>

// ============================================================
//  WiFi Manager — connect, reconnect, mDNS
//
//  V3.00 — WiFi client mode, connects to StarCabin
//          Publishes http://fan-mate.local via mDNS
// ============================================================

// Call in setup() — starts connection (non-blocking after first attempt)
void wifi_setup();

// Call in loop() — handles reconnection if link drops
void wifi_loop();

// Status queries — safe anytime
bool    wifi_connected();
String  wifi_ip();
int     wifi_rssi();              // dBm, -30 (great) to -90 (bad)
String  wifi_ssid_connected();
String  wifi_mdns_name();         // e.g. "fan-mate.local"

// Milliseconds since last successful connect (0 if never)
unsigned long wifi_uptime_ms();

#endif