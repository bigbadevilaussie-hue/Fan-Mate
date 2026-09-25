#ifndef OPAL_CLIENT_H
#define OPAL_CLIENT_H

#include <Arduino.h>

// ============================================================
//  Opal router client
//
//  Logs into the GL.iNet Opal at OPAL_IP and polls the client
//  list for cumulative RX bytes. Used to compute network-wide
//  download rate for Auto Boost.
//
//  Auth: challenge → SHA256 crypt → login → SID
//  Poll: every 15s from tick_15s() in fanmate.ino
//  SID:  refreshed every ~50 minutes or on Access Denied
// ============================================================

// Call once in setup(), after WiFi is connected
void opal_init();

// Call every 15s from tick_15s()
// Returns true if the poll succeeded and rx_total is valid
// Returns false if WiFi down, login failed, HTTP failed, or JSON failed
bool opal_poll(uint64_t &rx_total);

// Force a fresh login on next poll
void opal_force_relogin();

// Status for logging / debug
bool opal_logged_in();

#endif