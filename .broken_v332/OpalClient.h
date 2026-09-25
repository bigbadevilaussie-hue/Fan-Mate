#ifndef OPAL_CLIENT_H
#define OPAL_CLIENT_H

#include <Arduino.h>

void opal_init();
bool opal_poll(uint64_t &rx_total);
void opal_force_relogin();
bool opal_logged_in();

void opal_pause();
void opal_resume();
bool opal_is_paused();

#endif
