#include "FanController.h"
#include "Config.h"
#include "Settings.h"
#include "AutoBoost.h"
#include "Logging.h"
#include "SerialBuffer.h"
#include "Songs.h"
#include "OpalClient.h"

#include <OneWire.h>
#include <DallasTemperature.h>

static OneWire oneWire(DS18B20_PIN);
static DallasTemperature ds18b20(&oneWire);

static int  fanPWM       = 0;
static int  fanPctLocal  = 0;
static int  fanRPMLocal  = 0;
static int  alertLevel   = 0;
extern bool phonePresent;

static volatile unsigned long tachPulses   = 0;
static unsigned long          lastTachRead = 0;

static unsigned long lastAlertStart = 0;
static int           beepIndex      = 0;
static bool          beepActive     = false;
static unsigned long beepTimer      = 0;

static bool          tempConversionRunning = false;
static unsigned long tempConversionStart   = 0;

// Boost/heat state
static int lastFanGear  = -1;

// Delta guard state — enter at 5.0, exit at 4.0 (hysteresis)
static bool delta_guard_active = false;

// Heat gear state — stateful so each gear has entry/exit hysteresis
static int heat_gear_state = 0;

// Stall detection
static unsigned long fan_stall_since = 0;
static bool          fan_stall_alarm = false;

// Phone presence timestamps (v4.06)
unsigned long phone_absent_since  = 0;
unsigned long phone_present_since = 0;

// Kill mode (v4.00)
enum KillState { KILL_AUTO = 0, KILL_ACTIVE = 1, KILL_OFF = 2 };
static KillState killState = KILL_AUTO;
static volatile bool kill_clear_requested = false;
static volatile bool kill_auto_requested  = false;

// ------------------------------------------------------------
//  Forward declarations
// ------------------------------------------------------------
static void kill_state_machine(float currentTemp);
static void runBeepSequence(int beeps, int beepMs, int gapMs, int intervalMs);
static void beep_once();
void beep_once_update();
static bool quiet_hours();

// ------------------------------------------------------------
void readDS18B20(float &currentTemp) {
    unsigned long now = millis();
    static unsigned long lastStart = 0;
    if (!tempConversionRunning && now - lastStart >= 2000) {
        lastStart = now;
        ds18b20.requestTemperatures();
        tempConversionRunning = true;
        tempConversionStart = now;
        return;
    }
    if (tempConversionRunning && now - tempConversionStart >= 750) {
        float t = ds18b20.getTempCByIndex(0);
        tempConversionRunning = false;
        if (t == DEVICE_DISCONNECTED_C || t == 0.0 || t < -50.0f || t > 100.0f) {
            Serial.printf("[DS18B20] bad read: %.1f - keeping last\n", t);
            return;
        }
        currentTemp  = t;
    }
}

float readNTC() {
    long sum = 0;
    for (int i = 0; i < 4; i++) {
        sum += analogRead(NTC_PIN);
        delayMicroseconds(50);
    }
    int raw = sum / 4;
    if (raw <= 0 || raw >= 4095) return -99.0f;
    float v_out = raw * (3.3f / 4095.0f);
    float r_ntc = 10000.0f * (v_out / (3.3f - v_out));
    float steinhart = log(r_ntc / 10000.0f) / 3950.0f;
    steinhart += 1.0f / 298.15f;
    float temp_c = (1.0f / steinhart) - 273.15f;
    return temp_c + 6.0f;  // calibration offset
}

void updatePhoneDetection() {
    static bool lastState = false;
    static unsigned long lastChange = 0;
    static bool initialized = false;
    bool present = (digitalRead(PHONE_SENSE_PIN) == LOW);

    if (!initialized) {
        initialized = true;
        lastState = present;
        phonePresent = present;
        if (present) {
            phone_present_since = millis();
        } else {
            phone_absent_since = millis();
        }
        log_print("[PHONE] initial: %s\n", present ? "present" : "absent");
        return;
    }

    if (present != lastState) {
        unsigned long now = millis();
        if (now - lastChange > 500) {
            lastState = present;
            lastChange = now;
            phonePresent = present;
            if (present) {
                phone_present_since = now;
                phone_absent_since  = 0;
            } else {
                phone_absent_since  = now;
                phone_present_since = 0;
            }
            log_print("[PHONE] %s\n", present ? "detected" : "removed");
        }
    }
}

// ------------------------------------------------------------
static int compute_temp_gear(float t) {
    // Stateful ladder with hysteresis on both entry and exit.
    // Entry at each threshold; exit at threshold - tempHysteresis.
    float h = config.tempHysteresis;

    if (heat_gear_state >= 4) {
        if (t >= config.tempGear4 - h) return 4;
    } else if (t >= config.tempGear4) return 4;

    if (heat_gear_state >= 3) {
        if (t >= config.tempGear3 - h) return 3;
    } else if (t >= config.tempGear3) return 3;

    if (heat_gear_state >= 2) {
        if (t >= config.tempGear2 - h) return 2;
    } else if (t >= config.tempGear2) return 2;

    if (heat_gear_state >= 1) {
        if (t >= config.tempGear1 - h) return 1;
    } else if (t >= config.tempGear1) return 1;

    heat_gear_state = 0;
    return 0;
}

// ------------------------------------------------------------
static bool quiet_hours() {
    struct tm ti;
    if (!getLocalTime(&ti, 10)) return false;
    int h = ti.tm_hour;
    if (QUIET_START_HOUR < QUIET_END_HOUR) {
        return h >= QUIET_START_HOUR && h < QUIET_END_HOUR;
    }
    return h >= QUIET_START_HOUR || h < QUIET_END_HOUR;
}

// ------------------------------------------------------------
static bool          short_beep_active = false;
static unsigned long short_beep_timer  = 0;

static void beep_once() {
    if (quiet_hours()) return;
    if (short_beep_active) return;
    tone(BUZZER_PIN, BUZZER_TONE_HZ);
    short_beep_active = true;
    short_beep_timer  = millis();
}

void beep_once_update() {
    if (short_beep_active && millis() - short_beep_timer >= 80) {
        noTone(BUZZER_PIN);
        short_beep_active = false;
    }
}

// ------------------------------------------------------------
static void runBeepSequence(int beeps, int beepMs, int gapMs, int intervalMs)
{
    unsigned long now = millis();

    if (!beepActive && beepIndex == 0) {
        if (now - lastAlertStart >= (unsigned long)intervalMs) {
            lastAlertStart = now;
            beepActive     = true;
            beepTimer      = now;
            beepIndex      = 0;
            tone(BUZZER_PIN, BUZZER_TONE_HZ);
        }
        return;
    }

    if (beepActive) {
        if (now - beepTimer >= (unsigned long)beepMs) {
            noTone(BUZZER_PIN);
            beepActive = false;
            beepTimer  = now;
            beepIndex++;
        }
        return;
    }

    if (now - beepTimer >= (unsigned long)gapMs) {
        if (beepIndex >= beeps) {
            beepIndex = 0;
        } else {
            tone(BUZZER_PIN, BUZZER_TONE_HZ);
            beepActive = true;
            beepTimer  = now;
        }
    }
}

// ------------------------------------------------------------
//  Kill mode state machine (v4.00)
//  AUTO   = armed, fires on tempKill
//  ACTIVE = fired, beeping, repeater off
//  OFF    = user silenced, no beep
// ------------------------------------------------------------
int kill_get_state() { return (int)killState; }

void kill_request_clear() {
    if (killState == KILL_ACTIVE) {
        kill_clear_requested = true;
    }
}

void kill_request_auto() {
    if (killState == KILL_OFF) {
        kill_auto_requested = true;
    }
}

static void kill_state_machine(float currentTemp) {
    // AUTO -> ACTIVE
    if (killState == KILL_AUTO && currentTemp >= config.tempGear4) {
        killState = KILL_ACTIVE;
        log_print("[KILL] -> ACTIVE (temp %.1f)\n", currentTemp);
        log_write_event("KILL");
        disableLoopWDT();
        bool ok = opal_set_repeater(false);
        enableLoopWDT();
        log_print("[OPAL] auto-kill: %s\n", ok ? "OK" : "FAILED");
        lastAlertStart = millis() - 120000;
    }

    // ACTIVE -> OFF (user clicked)
    if (killState == KILL_ACTIVE && kill_clear_requested) {
        kill_clear_requested = false;
        killState = KILL_OFF;
        log_print("[KILL] -> OFF\n");
        log_write_event("KILL_OFF");
        noTone(BUZZER_PIN);
        beepActive = false;
        beepIndex  = 0;
    }

    // OFF -> AUTO (user clicked)
    if (killState == KILL_OFF && kill_auto_requested) {
        kill_auto_requested = false;
        killState = KILL_AUTO;
        log_print("[KILL] -> AUTO\n");
        log_write_event("KILL_AUTO");
    }
}

// ------------------------------------------------------------
bool fan_stall_active() { return fan_stall_alarm; }

// ------------------------------------------------------------
void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
) {
    // ---- Kill state machine (v4.00) ----
    kill_state_machine(currentTemp);

    // ---- Delta guard evaluation (shared by alert and gear) ----
    // Hysteresis: enter at 5.0, exit at 4.0, so the fan doesn't flap
    // when the delta sits on the boundary.
    {
        float room = readNTC();
        if (room > -90.0f) {
            float d = currentTemp - room;
            if (delta_guard_active) {
                if (d < 4.0f) delta_guard_active = false;
            } else {
                if (d > 5.0f) delta_guard_active = true;
            }
        } else {
            delta_guard_active = false;
        }
    }

    // ---- Alert level (temperature OR delta) ----
    int newLevel = 0;
    if      (currentTemp >= config.tempGear4)   newLevel = 3;
    else if (currentTemp >= config.tempGear3)   newLevel = 2;
    else if (currentTemp >= config.tempGear2)   newLevel = 1;
    else if (delta_guard_active) {
        newLevel = 1;
    }

    if (newLevel != alertLevel) {
        alertLevel = newLevel;
        beepActive = false;
        beepIndex  = 0;
        noTone(BUZZER_PIN);

        if      (alertLevel == 3) log_print("[ALERT] KILL\n");
        else if (alertLevel == 2) log_print("[ALERT] OH SHIT\n");
        else if (alertLevel == 1) log_print("[ALERT] WARNING\n");
        else                      log_print("[ALERT] normal\n");

        lastAlertStart = millis() - 120000;
    }

    bool effectivePhone = phonePresent;

    // ---- Fan gear = max(heat, room-diff, boost) ----
    // Priority: heat control > room delta > boost. Highest demand wins.
    int tempGear  = compute_temp_gear(currentTemp);
    heat_gear_state = tempGear;
    int boostGear = auto_boost_gear();

    // Delta guard: state evaluated above; here we just apply it
    int deltaGear = delta_guard_active ? 1 : 0;

    int fanGear = tempGear;
    if (boostGear > fanGear) fanGear = boostGear;
    if (deltaGear > fanGear) fanGear = deltaGear;

    // ---- Beep on gear change ----
    if (fanGear != lastFanGear) {
        if (lastFanGear >= 0) {
            log_print("[FAN] gear %d -> %d\n", lastFanGear, fanGear);
            beep_once();
        }
        lastFanGear = fanGear;
    }

    // ---- Fan PWM ----
    int newPwm = 0;
    if (fanGear > 0) {
        // gear 1=25%, 2=50%, 3=75%, 4=100% -- real duty, verified on bench
        newPwm = map(fanGear, 0, 4, 0, 255);
    }

    if (settings_is_night()) {
        int cap = (config.nightMax * 255) / 100;
        if (newPwm > cap) newPwm = cap;
    }

    if (!effectivePhone) {
        newPwm = 0;
    }

    fanPWM = newPwm;

    // Kick-start pulse when fan is stopped or nearly stopped
    if (fanGear > 0 && fanRPMLocal < 200) {
        ledcWrite(2, 200);
        delay(400);
    }

    ledcWrite(2, fanPWM);
    fanPctLocal = map(fanPWM, 0, 255, 0, 100);

#if FAN_STALL_ENABLED
    if (fanPctLocal >= 25 && fanRPMLocal == 0) {
        if (fan_stall_since == 0) {
            fan_stall_since = millis();
        } else if (millis() - fan_stall_since > 5000 && !fan_stall_alarm) {
            fan_stall_alarm = true;
            log_print("[FAN] STALL ALARM\n");
            log_write_event("FAN_STALL");
            tone(BUZZER_PIN, BUZZER_TONE_HZ);
            delay(200);
            noTone(BUZZER_PIN);
        }
    } else {
        fan_stall_since = 0;
        if (fan_stall_alarm) {
            fan_stall_alarm = false;
            log_print("[FAN] recovered\n");
            log_write_event("FAN_RECOVERED");
        }
    }
#endif

    // ---- Alarm output ----
    if (fan_stall_alarm) {
        runBeepSequence(5, 120, 120, 15000);
    } else if (killState == KILL_ACTIVE) {
        runBeepSequence(KILL_BEEPS, KILL_BEEP_MS, KILL_GAP_MS, KILL_INTERVAL_MS);
    } else if (alertLevel == 2) {
        runBeepSequence(PANIC_BEEPS, PANIC_BEEP_MS, PANIC_GAP_MS, PANIC_INTERVAL_MS);
    } else if (alertLevel == 1 && !quiet_hours()) {
        runBeepSequence(WARNING_BEEPS, WARNING_BEEP_MS, WARNING_GAP_MS, WARNING_INTERVAL_MS);
    } else {
        noTone(BUZZER_PIN);
    }

    outFanPct       = fanPctLocal;
    outRpm          = fanRPMLocal;
    outAlert        = alertLevel;
    outPhonePresent = phonePresent;
}

// ------------------------------------------------------------
void silenceFanAndAlerts() {
    ledcWrite(2, 0);
    noTone(BUZZER_PIN);
    fanPWM = 0;
    fanPctLocal = 0;
    fanRPMLocal = 0;
    alertLevel = 0;
    beepActive = false;
    beepIndex = 0;
    lastFanGear = -1;
    fan_stall_since = 0;
    fan_stall_alarm = false;
}

static void IRAM_ATTR onTach() {
    tachPulses++;
}

void updateTach() {
    unsigned long now = millis();
    if (now - lastTachRead >= 1000) {
        noInterrupts();
        unsigned long pulses = tachPulses;
        tachPulses = 0;
        interrupts();
        lastTachRead = now;
        fanRPMLocal = (pulses * 60) / 2;
    }
}

void initHardware() {
    ds18b20.begin();
    ds18b20.setWaitForConversion(false);
    pinMode(PHONE_SENSE_PIN, INPUT_PULLUP);

    ledcSetup(2, PWM_FREQ, PWM_RES);
    ledcAttachPin(FAN_PWM_PIN, 2);
    ledcWrite(2, 0);

    pinMode(BUZZER_PIN, OUTPUT);
    digitalWrite(BUZZER_PIN, LOW);

    pinMode(TACH_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(TACH_PIN), onTach, FALLING);
}
