#ifndef AUTO_BOOST_H
#define AUTO_BOOST_H

#include <Arduino.h>

// Counter-based graduated boost ramp:
//   counter 0 → gear 0 (0%)
//   counter 1 → gear 1 (25%)
//   counter 2 → gear 2 (50%)
//   counter 3 → gear 3 (75%)
//   counter 4 → gear 4 (100%)
//
// Counter increments when net >= threshold.
// Counter decrements when net < threshold * 0.8.
// Between 80% and 100% of threshold → hold.

void     auto_boost_init();
void     auto_boost_update(float net_kbps);
void     auto_boost_release();       // force reset to 0

int      auto_boost_gear();          // 0-4
int      auto_boost_threshold();     // current mode's threshold

#endif
