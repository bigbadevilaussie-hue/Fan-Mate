#ifndef AUTO_BOOST_H
#define AUTO_BOOST_H

#include <Arduino.h>

void     auto_boost_init();
void     auto_boost_update(float net_kbps);
bool     auto_boost_is_active();
void     auto_boost_release();
uint32_t auto_boost_counter();

int      auto_boost_threshold();
int      auto_boost_on_hold();
int      auto_boost_off_hold();

#endif
