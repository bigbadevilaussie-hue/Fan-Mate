#include "AutoBoost.h"
#include "Config.h"
#include "Settings.h"

// ============================================================
//  Auto Boost — implementation
//
//  Counts consecutive high-rate ticks. When threshold reached,
//  forces fan to 100%. Counter decays when rate is low.
// ============================================================

static bool     boost_active     = false;
static uint32_t boost_counter    = 0;
static int      saved_fan_mode   = 0;   // for restore (0=off,1=on,2=auto)

// ------------------------------------------------------------
//  Init
// ------------------------------------------------------------
void auto_boost_init() {
    boost_active  = false;
    boost_counter = 0;
    Serial.println("[BOOST] init");
}

// ------------------------------------------------------------
//  Update — called every 15s from tick_15s()
// ------------------------------------------------------------
void auto_boost_update(float net_kbps) {
    // Boost disabled? Force off.
    if (!config.boostEnabled) {
        if (boost_active) {
            boost_active = false;
            Serial.println("[BOOST] disabled — released");
        }
        boost_counter = 0;
        return;
    }

    // Threshold check with hysteresis
    if (net_kbps >= config.boostThreshold) {
        boost_counter++;
    } else {
        // Decay by 2 (faster release than acquire)
        if (boost_counter >= 2) {
            boost_counter -= 2;
        } else {
            boost_counter = 0;
        }
    }

    // Activate when counter exceeds hold time
    if (!boost_active && boost_counter >= config.boostHold) {
        boost_active = true;
        Serial.printf("[BOOST] ACTIVE — rate=%.1f KB/s counter=%lu\n",
                      net_kbps, (unsigned long)boost_counter);
    }

    // Release when counter drops to zero
    if (boost_active && boost_counter == 0) {
        boost_active = false;
        Serial.printf("[BOOST] released — rate=%.1f KB/s\n", net_kbps);
    }
}

// ------------------------------------------------------------
//  Status
// ------------------------------------------------------------
bool auto_boost_is_active() {
    return boost_active;
}

// ------------------------------------------------------------
//  Force release
// ------------------------------------------------------------
void auto_boost_release() {
    if (boost_active) {
        Serial.println("[BOOST] manual release");
    }
    boost_active  = false;
    boost_counter = 0;
}

// ------------------------------------------------------------
//  Counter (for debug/display)
// ------------------------------------------------------------
uint32_t auto_boost_counter() {
    return boost_counter;
}