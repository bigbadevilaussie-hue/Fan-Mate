#ifndef SERIAL_BUFFER_H
#define SERIAL_BUFFER_H

#include <Arduino.h>

void   serial_buf_init();
void   log_print(const char* fmt, ...);
String get_serial_dump();

#endif