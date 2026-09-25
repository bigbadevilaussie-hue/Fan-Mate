#ifndef LOGGING_H
#define LOGGING_H

#include <Arduino.h>

void   log_init();
void   log_write(float temp, float net_kbps, int boost, int fan, int rpm);
void   log_write_event(const char* event);
void   log_write_reset_reason();

size_t log_get_size();
bool   log_is_full();
void   log_check_full();
void   log_clear();
String log_time_string();

#endif
