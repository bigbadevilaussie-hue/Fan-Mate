#ifndef LOGGING_H
#define LOGGING_H

#include <Arduino.h>

// ============================================================
//  Logging — LittleFS CSV log
//
//  One line every 15s from tick_15s():
//    time,mb,temp,boost,rpm,alarm,bench
//
//  File: /log.csv
//  Max: 800 KB
//  When full: beep beep every 60s + OLED shows "Logfile Full"
//  Cleared manually via GUI menu (POST /log/clear)
// ============================================================

void   log_init();
void   log_write(float temp, float mb, int boost, int rpm, int alarm, int bench);
size_t log_get_size();
bool   log_is_full();
void   log_check_full();        // beeps if full (called every tick)
void   log_clear();              // wipes file, called from HTTP
String log_time_string();        // "YYYY-MM-DD HH:MM:SS" or "uptime:NNN"

#endif