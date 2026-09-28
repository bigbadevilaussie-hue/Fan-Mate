#ifndef OPAL_CLIENT_H
#define OPAL_CLIENT_H

#include <Arduino.h>

void opal_init();
bool opal_poll(uint64_t &rx_total);
bool opal_set_repeater(bool enable);
void opal_force_relogin();
bool opal_logged_in();
void opal_pause();
void opal_resume();
bool opal_is_paused();
bool opal_ok_recently();   // true if poll succeeded in last ~45s

#endif