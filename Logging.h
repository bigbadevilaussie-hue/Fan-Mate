#ifndef LOGGING_H
#define LOGGING_H

#include <Arduino.h>

void   log_init();
void   log_write(float temp, float net_kbps, int boost, int fan, int rpm);
void   log_write_event(const char* event);
void   log_write_reset_reason();

size_t log_get_size();
void   log_check_full();
void   log_clear();
String log_time_string();


void   log_rotate_check();
void   log_boot_recovery();
size_t log_count_live_rows();
size_t log_list_sealed(char names[][48], size_t max);
bool   log_delete_sealed(const char* name);
size_t log_sealed_count();
size_t log_sealed_bytes();
bool   log_rotation_paused();

#endif
