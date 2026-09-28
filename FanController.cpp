#include "FanController.h"
#include "Config.h"
#include "Settings.h"
#include "AutoBoost.h"
#include "Logging.h"
#include "SerialBuffer.h"
#include "OpalClient.h"

#include <OneWire.h>
#include <DallasTemperature.h>

static OneWire oneWire(DS18B20_PIN);
static DallasTemperature ds18b20(&oneWire);

static int  fanPWM       = 0;
static int  fanPctLocal  = 0;
static int  fanRPMLocal  = 0;
static int  alertLevel   = 0;
static bool phonePresent = false;

static volatile unsigned long tachPulses   = 0;
static unsigned long          lastTachRead = 0;

static unsigned long lastAlertStart = 0;
static int           beepIndex      = 0;
static bool          beepActive     = false;
static unsigned long beepTimer      = 0;

static bool          tempConversionRunning = false;
static unsigned long tempConversionStart   = 0;
static float         lastGoodTemp          = 25.0f;

// Boost/heat state
static int lastFanGear  = -1;
static int lastTempGear = -1;

// Stall detection
static unsigned long fan_stall_since = 0;
static bool          fan_stall_alarm = false;

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
        lastGoodTemp = t;
        currentTemp  = t;
    }
}

void updatePhoneDetection() {
    static bool lastState = false;
    static unsigned long lastChange = 0;
    bool present = (digitalRead(PHONE_SENSE_PIN) == LOW);
    if (present != lastState) {
        unsigned long now = millis();
        if (now - lastChange > 500) {
            lastState = present;
            lastChange = now;
            phonePresent = present;
            log_print("[PHONE] %s\n", present ? "detected" : "removed");
        }
    }
}

// ------------------------------------------------------------
static int compute_temp_gear(float t) {
    if (t >= config.tempKill)      return 4;
    if (t >= config.tempPanic)     return 3;
    if (t >= config.tempWarning)   return 2;
    if (t >= config.tempWarning - config.tempHysteresis) return 1;
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
static void beep_once() {
    if (quiet_hours()) return;
    tone(BUZZER_PIN, BUZZER_TONE_HZ);
    delay(80);
    noTone(BUZZER_PIN);
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
    if (killState == KILL_AUTO && currentTemp >= config.tempKill) {
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

    // ---- Alert level (temperature) ----
    int newLevel = 0;
    if      (currentTemp >= config.tempKill)    newLevel = 3;
    else if (currentTemp >= config.tempPanic)   newLevel = 2;
    else if (currentTemp >= config.tempWarning) newLevel = 1;

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

    bool effectivePhone = (config.phoneMode == "off") ? true : phonePresent;

    // ---- Fan gear = max(temp, boost) ----
    int tempGear  = compute_temp_gear(currentTemp);
    int boostGear = auto_boost_gear();
    int fanGear   = (tempGear > boostGear) ? tempGear : boostGear;

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
        newPwm = map(fanGear * 25, 1, 100, PWM_MIN, 255);
    }

    if (settings_is_night()) {
        int cap = (config.nightMax * 255) / 100;
        if (newPwm > cap) newPwm = cap;
    }

    if (config.phoneMode == "auto" && !effectivePhone) {
        newPwm = 0;
    }

    fanPWM = newPwm;
    fanPctLocal = map(fanPWM, 0, 255, 0, 100);
    ledcWrite(2, fanPWM);

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
        lastTachRead = now;
        fanRPMLocal = (tachPulses * 60) / 2;
        tachPulses = 0;
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