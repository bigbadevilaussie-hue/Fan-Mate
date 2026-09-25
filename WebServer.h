#ifndef WEB_SERVER_H
#define WEB_SERVER_H

#include <Arduino.h>

// ============================================================
//  Web Server — HTTP interface
//
//  V3.00 — minimal: / and /status
// ============================================================

// Call in setup() after wifi_setup()
void server_setup();

// Call in loop() every iteration
void server_loop();

// Version string served at /status
String server_version();

#endif