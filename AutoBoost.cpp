#include "AutoBoost.h"
#include "Settings.h"
#include "Config.h"

static int gear = 0;

static int current_threshold() {
    if (config.boostMode == 2) return config.boostAggr.threshold;
    if (config.boostMode == 1) return config.boostNormal.threshold;
    return 999999;   // off
}

void auto_boost_init() {
    gear = 0;
    Serial.printf("[BOOST] init (mode=%d thr=%d)\n",
                  config.boostMode, current_threshold());
}

void auto_boost_update(float net_kbps) {
    int thr = current_threshold();

    if (config.boostMode == 0) {
        if (gear != 0) { gear = 0; }
        return;
    }

    if (net_kbps >= thr) {
        if (gear < 4) gear++;
    } else if (net_kbps < (float)thr * 0.8f) {
        if (gear > 0) gear--;
    }

    Serial.printf("[BOOST] net=%.1f thr=%d gear=%d\n",
                  net_kbps, thr, gear);
}

void auto_boost_release() {
    gear = 0;
}

int auto_boost_gear() {
    return gear;
}

int auto_boost_threshold() {
    return current_threshold();
}
