#include "AutoBoost.h"
#include "Settings.h"
#include "Config.h"

static int gear = 0;
static int over_ticks  = 0;
static int under_ticks = 0;

static int current_threshold() {
    if (config.boostMode == 2) return config.boostAggr.threshold;
    if (config.boostMode == 1) return config.boostNormal.threshold;
    return 999999;
}

static int current_on_hold() {
    if (config.boostMode == 2) return config.boostAggr.on_hold;
    if (config.boostMode == 1) return config.boostNormal.on_hold;
    return 4;
}

static int current_off_hold() {
    if (config.boostMode == 2) return config.boostAggr.off_hold;
    if (config.boostMode == 1) return config.boostNormal.off_hold;
    return 4;
}

void auto_boost_init() {
    gear = 0;
    over_ticks = 0;
    under_ticks = 0;
    Serial.printf("[BOOST] init (mode=%d thr=%d on=%d off=%d)\n",
                  config.boostMode, current_threshold(),
                  current_on_hold(), current_off_hold());
}

void auto_boost_update(float net_kbps) {
    int thr = current_threshold();
    int on_hold  = current_on_hold();
    int off_hold = current_off_hold();

    if (config.boostMode == 0) {
        gear = 0;
        over_ticks = 0;
        under_ticks = 0;
        return;
    }

    float low = (float)thr * 0.8f;

    if (net_kbps >= thr) {
        under_ticks = 0;
        over_ticks++;
        if (over_ticks >= on_hold && gear < 4) {
            gear++;
            over_ticks = 0;
            Serial.printf("[BOOST] gear+ net=%.1f thr=%d gear=%d\n",
                          net_kbps, thr, gear);
        }
    } else if (net_kbps < low) {
        over_ticks = 0;
        under_ticks++;
        if (under_ticks >= off_hold && gear > 0) {
            gear--;
            under_ticks = 0;
            Serial.printf("[BOOST] gear- net=%.1f thr=%d gear=%d\n",
                          net_kbps, thr, gear);
        }
    } else {
        over_ticks = 0;
        under_ticks = 0;
    }
}

void auto_boost_release() {
    gear = 0;
    over_ticks = 0;
    under_ticks = 0;
}

int auto_boost_gear() { return gear; }
int auto_boost_threshold() { return current_threshold(); }
