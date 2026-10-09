#include "AutoBoost.h"
#include "Settings.h"
#include "Config.h"
#include "SerialBuffer.h"

#define COOLDOWN_MARGIN_C   0.3f
#define COOLDOWN_MAX_MS     (20UL * 60UL * 1000UL)
#define GEAR_DOWN_BAND      0.8f
#define FORCE_MAX_MS        (30UL * 60UL * 1000UL)

enum Phase { PH_IDLE = 0, PH_RUNNING = 1, PH_COOLDOWN = 2 };

static Phase         phase          = PH_IDLE;
static int           data_gear      = 0;
static int           over_ticks     = 0;
static int           under_ticks    = 0;
static float         cold_temp      = 0.0f;
static unsigned long cooldown_start = 0;

static bool          force_active     = false;
static int           force_gear_value = 0;
static unsigned long force_start      = 0;

static int current_threshold() {
    int t = config.boostThreshold;
    return (t < 1) ? 1 : t;
}
static int current_on_hold() {
    int v = config.boostOnHold;
    return (v < 1) ? 1 : v;
}
static int current_off_hold() {
    int v = config.boostOffHold;
    return (v < 1) ? 1 : v;
}

static int target_gear(float kbps, int cur_gear, int thr) {
    int t = (int)(kbps / (float)thr);
    if (t > 4) t = 4;
    if (t < 0) t = 0;
    if (t < cur_gear && kbps >= (float)cur_gear * (float)thr * GEAR_DOWN_BAND) {
        t = cur_gear;
    }
    return t;
}

static void reset_all() {
    phase       = PH_IDLE;
    data_gear   = 0;
    over_ticks  = 0;
    under_ticks = 0;
}

void auto_boost_init() {
    reset_all();
    log_print("[BOOST] init (thr=%d on=%d off=%d)\n",
              current_threshold(),
              current_on_hold(), current_off_hold());
}

static void release_force() {
    force_active     = false;
    force_gear_value = 0;
    if (phase == PH_RUNNING) {
        data_gear      = 0;
        phase          = PH_COOLDOWN;
        cooldown_start = millis();
    }
}

void auto_boost_update(float net_kbps, float phone_temp, bool net_ok) {
    if (force_active) {
        if (millis() - force_start > FORCE_MAX_MS) {
            log_print("[BOOST] force expired after %lu min\n", FORCE_MAX_MS / 60000UL);
            release_force();
        } else {
            return;
        }
    }

    if (net_ok) {
        int thr      = current_threshold();
        int on_hold  = current_on_hold();
        int off_hold = current_off_hold();
        int tgt      = target_gear(net_kbps, data_gear, thr);

        if (tgt > data_gear) {
            under_ticks = 0;
            over_ticks++;
            if (phase == PH_IDLE && over_ticks == 1) {
                cold_temp = phone_temp;
            }
            if (over_ticks >= on_hold) {
                data_gear++;
                over_ticks = 0;
                log_print("[BOOST] gear+ net=%.1f thr=%d gear=%d\n",
                          net_kbps, thr, data_gear);
            }
        } else if (tgt < data_gear) {
            over_ticks = 0;
            under_ticks++;
            if (under_ticks >= off_hold) {
                data_gear--;
                under_ticks = 0;
                log_print("[BOOST] gear- net=%.1f thr=%d gear=%d\n",
                          net_kbps, thr, data_gear);
            }
        } else {
            over_ticks  = 0;
            under_ticks = 0;
        }

        if (data_gear > 0 && phase != PH_RUNNING) {
            if (phase == PH_IDLE) {
                log_print("[BOOST] start cold=%.1f\n", cold_temp);
            } else {
                log_print("[BOOST] resumed during cooldown (cold=%.1f kept)\n", cold_temp);
            }
            phase = PH_RUNNING;
        } else if (data_gear == 0 && phase == PH_RUNNING) {
            phase          = PH_COOLDOWN;
            cooldown_start = millis();
            log_print("[BOOST] data stopped, cooling to %.1f (now %.1f)\n",
                      cold_temp, phone_temp);
        }
    }

    if (phase == PH_COOLDOWN) {
        if (phone_temp <= cold_temp + COOLDOWN_MARGIN_C) {
            phase = PH_IDLE;
            log_print("[BOOST] cooled (%.1f <= %.1f) end\n",
                      phone_temp, cold_temp + COOLDOWN_MARGIN_C);
        } else if (millis() - cooldown_start > COOLDOWN_MAX_MS) {
            phase = PH_IDLE;
            log_print("[BOOST] cooldown timeout (phone %.1f, cold %.1f) end\n",
                      phone_temp, cold_temp);
        }
    }
}

void auto_boost_release() {
    reset_all();
}

int auto_boost_data_gear() {
    if (force_active) return force_gear_value;
    return data_gear;
}

int auto_boost_gear() {
    if (force_active) return force_gear_value;
    if (phase == PH_COOLDOWN) return 1;
    return data_gear;
}

int   auto_boost_threshold()  { return current_threshold(); }
bool  auto_boost_cooling()    { return phase == PH_COOLDOWN; }
float auto_boost_cold_temp()  { return cold_temp; }

void auto_boost_force_gear(int n, float phone_temp) {
    if (n <= 0) {
        release_force();
        log_print("[BOOST] force released\n");
    } else {
        if (n > 4) n = 4;
        if (phase == PH_IDLE) {
            cold_temp = phone_temp;
            log_print("[BOOST] start cold=%.1f (forced)\n", cold_temp);
        }
        if (phase != PH_RUNNING) phase = PH_RUNNING;
        force_active     = true;
        force_gear_value = n;
        force_start      = millis();
        log_print("[BOOST] force gear=%d\n", n);
    }
}
