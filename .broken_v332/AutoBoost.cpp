#include "AutoBoost.h"
#include "Settings.h"
#include "Config.h"

#include <Arduino.h>

// ============================================================
//  Auto Boost — mode-based
//
//  Reads config.boostMode:
//    0 = off       (no boost logic runs)
//    1 = normal    (config.boostNormal)
//    2 = aggressive(config.boostAggr)
//
//  Each tick (15s) from tick_15s():
//    - if net_kbps >= threshold → over_count++, under_count = 0
//    - if net_kbps <  threshold → under_count++, over_count = 0
//
//  If over_count  >= on_hold  → boost active
//  If under_count >= off_hold → boost released
// ============================================================

static bool     boost_active   = false;
static uint32_t over_count     = 0;
static uint32_t under_count    = 0;

// ------------------------------------------------------------
static BoostProfile current_profile() {
    if (config.boostMode == 2) return config.boostAggr;
    return config.boostNormal;  // mode 0 or 1 both return normal
}

// ------------------------------------------------------------
void auto_boost_init() {
    boost_active = false;
    over_count   = 0;
    under_count  = 0;

    const char* mode_str =
        (config.boostMode == 0) ? "off" :
        (config.boostMode == 2) ? "aggressive" : "normal";

    Serial.printf("[BOOST] init mode=%s\n", mode_str);
}

// ------------------------------------------------------------
void auto_boost_update(float net_kbps) {
    // Mode 0 = off → always released
    if (config.boostMode == 0) {
        if (boost_active) {
            boost_active = false;
            Serial.println("[BOOST] mode=off, releasing");
        }
        over_count  = 0;
        under_count = 0;
        return;
    }

    BoostProfile p = current_profile();

    // ---- Classify current tick ----
    if (net_kbps >= (float)p.threshold) {
        over_count++;
        under_count = 0;
    } else {
        under_count++;
        over_count = 0;
    }

    // ---- Activate ----
    if (!boost_active && over_count >= (uint32_t)p.on_hold) {
        boost_active = true;
        Serial.printf("[BOOST] ACTIVE (rate=%.1f thr=%d over=%u)\n",
                      net_kbps, p.threshold, over_count);
    }

    // ---- Release ----
    if (boost_active && under_count >= (uint32_t)p.off_hold) {
        boost_active = false;
        Serial.printf("[BOOST] released (rate=%.1f thr=%d under=%u)\n",
                      net_kbps, p.threshold, under_count);
    }
}

// ------------------------------------------------------------
bool auto_boost_is_active() {
    return boost_active;
}

// ------------------------------------------------------------
void auto_boost_release() {
    boost_active = false;
    over_count   = 0;
    under_count  = 0;
}

// ------------------------------------------------------------
uint32_t auto_boost_counter() {
    return over_count;
}

// ------------------------------------------------------------
//  Accessors — used by /status and /config GET
// ------------------------------------------------------------
int auto_boost_threshold() {
    if (config.boostMode == 0) return 0;
    return current_profile().threshold;
}

int auto_boost_on_hold() {
    if (config.boostMode == 0) return 0;
    return current_profile().on_hold;
}

int auto_boost_off_hold() {
    if (config.boostMode == 0) return 0;
    return current_profile().off_hold;
}