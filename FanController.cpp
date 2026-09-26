#include "FanController.h"
#include "Config.h"
#include "Settings.h"
#include "AutoBoost.h"
#include "Logging.h"
#include "SerialBuffer.h"

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

// Gear state
static int lastFanGear  = -1;
static int lastTempGear = -1;

// Stall detection
static unsigned long fan_stall_since = 0;
static bool          fan_stall_alarm = false;

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
//  Temp gear: 0-4 based on warning/panic/kill
// ------------------------------------------------------------
static int compute_temp_gear(float t) {
    if (t >= config.tempKill)      return 4;
    if (t >= config.tempPanic)     return 3;
    if (t >= config.tempWarning)   return 2;
    if (t >= config.tempWarning - config.tempHysteresis) return 1;
    return 0;
}

// ------------------------------------------------------------
//  Single beep (used for gear changes)
// ------------------------------------------------------------
static void beep_once() {
    ledcWrite(BUZZER_CHANNEL, 200);
    delay(80);
    ledcWrite(BUZZER_CHANNEL, 0);
}

// ------------------------------------------------------------
//  Multi-beep sequence for alerts.
// ------------------------------------------------------------
static void runBeepSequence(int beeps, int beepMs, int gapMs,
                            int duty, int intervalMs) {
    unsigned long now = millis();

    if (!beepActive && beepIndex == 0) {
        if (now - lastAlertStart >= (unsigned long)intervalMs) {
            lastAlertStart = now;
            beepActive = true;
            beepTimer = now;
            ledcWrite(BUZZER_CHANNEL, duty);
        }
        return;
    }

    if (beepActive) {
        if (now - beepTimer >= (unsigned long)beepMs) {
            ledcWrite(BUZZER_CHANNEL, 0);
            beepActive = false;
            beepTimer = now;
        }
    } else {
        if (now - beepTimer >= (unsigned long)gapMs) {
            beepIndex++;
            if (beepIndex >= beeps) {
                beepIndex = 0;
            } else {
                ledcWrite(BUZZER_CHANNEL, duty);
                beepActive = true;
                beepTimer = now;
            }
        }
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
    // ---- Alert level (temperature) ----
    int newLevel = 0;
    if      (currentTemp >= config.tempKill)    newLevel = 3;
    else if (currentTemp >= config.tempPanic)   newLevel = 2;
    else if (currentTemp >= config.tempWarning) newLevel = 1;

    if (newLevel != alertLevel) {
        alertLevel = newLevel;
        beepActive = false;
        beepIndex = 0;
        ledcWrite(BUZZER_CHANNEL, 0);
        if (alertLevel == 3)      log_print("[ALERT] KILL\n");
        else if (alertLevel == 2) log_print("[ALERT] OH SHIT\n");
        else if (alertLevel == 1) log_print("[ALERT] WARNING\n");
        else                      log_print("[ALERT] normal\n");
        lastAlertStart = millis() - 120000;
    }

    bool effectivePhone = (config.phoneMode == "off") ? true : phonePresent;

    // ---- Fan gear = max(temp gear, boost gear) ----
    int tempGear  = compute_temp_gear(currentTemp);
    int boostGear = auto_boost_gear();
    int fanGear   = (tempGear > boostGear) ? tempGear : boostGear;

    // ---- Beep on gear change (skip first tick after boot/wake) ----
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

    // ---- Night cap ----
    if (settings_is_night()) {
        int cap = (config.nightMax * 255) / 100;
        if (newPwm > cap) newPwm = cap;
    }

    // ---- Phone gate ----
    if (config.phoneMode == "auto" && !effectivePhone) {
        newPwm = 0;
    }

    fanPWM = newPwm;
    fanPctLocal = map(fanPWM, 0, 255, 0, 100);
    ledcWrite(0, fanPWM);

#if FAN_STALL_ENABLED
    // ---- Fan stall detection ----
    // Fan commanded on (>=25%) but tach reads zero for >5s
    if (fanPctLocal >= 25 && fanRPMLocal == 0) {
        if (fan_stall_since == 0) {
            fan_stall_since = millis();
        } else if (millis() - fan_stall_since > 5000 && !fan_stall_alarm) {
            fan_stall_alarm = true;
            log_print("[FAN] STALL ALARM\n");
            log_write_event("FAN_STALL");
            ledcWrite(BUZZER_CHANNEL, BUZZER_LOUD);
            delay(200);
            ledcWrite(BUZZER_CHANNEL, 0);
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
        runBeepSequence(5, 120, 120, BUZZER_LOUD, 15000);
    } else if (alertLevel == 3) {
        runBeepSequence(10, 100, 50, BUZZER_LOUD, 30000);
    } else if (alertLevel == 2) {
        runBeepSequence(PANIC_BEEPS, PANIC_BEEP_MS, PANIC_GAP_MS,
                        BUZZER_LOUD, PANIC_INTERVAL_MS);
    } else if (alertLevel == 1) {
        runBeepSequence(WARNING_BEEPS, WARNING_BEEP_MS, WARNING_GAP_MS,
                        BUZZER_QUIET, WARNING_INTERVAL_MS);
    } else {
        ledcWrite(BUZZER_CHANNEL, 0);
    }

    outFanPct       = fanPctLocal;
    outRpm          = fanRPMLocal;
    outAlert        = alertLevel;
    outPhonePresent = phonePresent;
}

// ------------------------------------------------------------
void silenceFanAndAlerts() {
    ledcWrite(0, 0);
    ledcWrite(BUZZER_CHANNEL, 0);
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
    ledcSetup(0, PWM_FREQ, PWM_RES);
    ledcAttachPin(FAN_PWM_PIN, 0);
    ledcWrite(0, 0);
    ledcSetup(BUZZER_CHANNEL, BUZZER_FREQ, BUZZER_RES);
    ledcAttachPin(BUZZER_PIN, BUZZER_CHANNEL);
    ledcWrite(BUZZER_CHANNEL, 0);
    pinMode(TACH_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(TACH_PIN), onTach, FALLING);
}