#include "SerialBuffer.h"
#include "Config.h"

#include <stdarg.h>

static String serial_buf[SERIAL_BUF_LINES];
static int    serial_idx = 0;

void serial_buf_init() {
    for (int i = 0; i < SERIAL_BUF_LINES; i++) serial_buf[i] = "";
    serial_idx = 0;
}

void log_print(const char* fmt, ...) {
    char buf[200];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    Serial.print(buf);
    serial_buf[serial_idx] = String(buf);
    serial_idx = (serial_idx + 1) % SERIAL_BUF_LINES;
}

String get_serial_dump() {
    String out;
    for (int i = 0; i < SERIAL_BUF_LINES; i++) {
        int idx = (serial_idx + i) % SERIAL_BUF_LINES;
        if (serial_buf[idx].length() > 0) out += serial_buf[idx];
    }
    return out;
}