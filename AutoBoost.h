#ifndef AUTO_BOOST_H
#define AUTO_BOOST_H

#include <Arduino.h>

// Boost = data-driven fan gears + thermal cooldown hold.
//
// DATA GEAR (ramped, with hysteresis) -- follows download rate only:
//   rate >= 1 x thr -> gear 1 (25%)
//   rate >= 2 x thr -> gear 2 (50%)
//   rate >= 3 x thr -> gear 3 (75%)
//   rate >= 4 x thr -> gear 4 (100%)
//   Up:   one gear per on_hold ticks while target > gear
//   Down: one gear per off_hold ticks, and only once rate has fallen
//         below 80% of the current gear's entry point (hysteresis)
//
// COOLDOWN HOLD -- follows phone temperature:
//   "Cold temp" is stored when a download starts (phone before it heats).
//   When data stops, the data gear ramps down to 0 but the fan is held
//   at gear 1 until phone temp <= cold temp (+ small margin), or a
//   safety timeout expires. A new download during cooldown keeps the
//   original cold temp.

void  auto_boost_init();
void  auto_boost_update(float net_kbps, float phone_temp, bool net_ok = true);
void  auto_boost_release();                 // reset everything (sleep / boost off)

int   auto_boost_gear();                    // 0-4, what the fan controller uses
int   auto_boost_threshold();               // current mode's threshold (KB/s)
void  auto_boost_force_gear(int n, float phone_temp);  // 0=release, 1-4=lock

bool  auto_boost_cooling();                 // true while holding for cooldown
float auto_boost_cold_temp();               // stored pre-boost phone temp

#endif
