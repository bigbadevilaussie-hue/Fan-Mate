#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <Arduino.h>

void   wifi_setup();
void   wifi_loop();

bool   wifi_connected();
String wifi_ip();
int    wifi_rssi();
String wifi_ssid_connected();
String wifi_mdns_name();
unsigned long wifi_uptime_ms();



// v4.29: clock state (from Opal Date header)
bool ntp_synced();      // kept for compat, returns clock validity
bool clock_synced();
void clock_sync();      // one HEAD to WiFi.gatewayIP(), parse Date header

#endif