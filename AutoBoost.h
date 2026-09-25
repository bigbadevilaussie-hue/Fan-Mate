#ifndef AUTO_BOOST_H
#define AUTO_BOOST_H

#include <Arduino.h>

// ============================================================
//  Auto Boost
//
//  Watches network download rate. When it exceeds threshold
//  for N consecutive ticks, forces the fan to 100%. When rate
//  drops and stays low, releases the fan back to normal.
// ============================================================

void     auto_boost_init();
void     auto_boost_update(float net_kbps);
bool     auto_boost_is_active();
void     auto_boost_release();
uint32_t auto_boost_counter();

#endif