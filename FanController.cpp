#include "FanController.h"
#include "Config.h"
#include "Settings.h"
#include "AutoBoost.h"

#include <OneWire.h>
#include <DallasTemperature.h>

static OneWire oneWire(DS18B20_PIN);
static DallasTemperature ds18b20(&oneWire);

static int  fanPWM       = 0;
static int  fanPctLocal  = 0;
static int  fanRPMLocal  = 0;
static int  alertLevel   = 0;
static bool phonePresent = false;

static volatile unsigned long tachPulses    = 0;
static unsigned long          lastTachRead  = 0;

static unsigned long lastAlertStart = 0;
static int           beepIndex      = 0;
static bool          beepActive     = false;
static unsigned long beepTimer      = 0;

static bool fanActive = false;

static bool          tempConversionRunning = false;
static unsigned long tempConversionStart   = 0;
static float         lastGoodTemp          = 25.0f;

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

        if (t == DEVICE_DISCONNECTED_C || t == 0.0) {
            Serial.println("[DS18B20] read failed");
            return;
        }

        lastGoodTemp = t;
        currentTemp  = t;
    }
}

// ------------------------------------------------------------
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
            Serial.printf("[PHONE] %s\n", present ? "detected" : "removed");
        }
    }
}

// ------------------------------------------------------------
static void runBeepSequence(int beeps, int beepMs, int gapMs,
                            int duty, int intervalMs) {
    unsigned long now = millis();

    if (!beepActive && beepIndex == 0) {
        if (now - lastAlertStart >= (unsigned long)intervalMs) {
            lastAlertStart = now;
            beepIndex = 0;
            beepActive = true;
            beepTimer = now;
            ledcWrite(BUZZER_CHANNEL, duty);
            Serial.printf("[BEEP] start %d\n", beeps);
        }
        return;
    }

    if (!beepActive) return;

    if (beepActive && now - beepTimer >= (unsigned long)beepMs) {
        ledcWrite(BUZZER_CHANNEL, 0);
        beepActive = false;
        beepTimer = now;
    } else if (!beepActive && now - beepTimer >= (unsigned long)gapMs) {
        beepIndex++;
        if (beepIndex >= beeps) {
            beepIndex = 0;
            beepActive = false;
            lastAlertStart = now;
        } else {
            ledcWrite(BUZZER_CHANNEL, duty);
            beepActive = true;
            beepTimer = now;
        }
    }
}

// ------------------------------------------------------------
void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
) {
    // ---- Alert level ----
    int newLevel = 0;
    if (currentTemp >= config.alarmPanic) newLevel = 2;
    else if (currentTemp >= config.alarmWarning) newLevel = 1;

    if (newLevel != alertLevel) {
        alertLevel = newLevel;
        beepActive = false;
        beepIndex = 0;
        ledcWrite(BUZZER_CHANNEL, 0);
        lastAlertStart = millis() -
            (alertLevel == 2 ? PANIC_INTERVAL_MS : WARNING_INTERVAL_MS);

        if (alertLevel == 2) Serial.println("[ALERT] PANIC");
        else if (alertLevel == 1) Serial.println("[ALERT] WARNING");
        else Serial.println("[ALERT] normal");
    }

    // ---- Effective phone ----
    bool effectivePhone = config.benchMode ? true : phonePresent;

    // ---- Fan % ----
    // V2.24: no fan.mode. Auto Boost IS the mode.
    //   boost.enabled == true  → network controls fan (100% or 0%)
    //   boost.enabled == false → temp curve
    int newPwm = 0;

    if (config.boostEnabled) {
        // Network mode — boost state directly controls fan
        if (auto_boost_is_active()) {
            newPwm = 255;
        } else {
            newPwm = 0;
        }
    } else {
        // Temp mode — fan follows temp curve
        if (currentTemp > config.tempOn + 0.2) fanActive = true;
        if (currentTemp < config.tempOn - 0.2) fanActive = false;

        if (fanActive) {
            if (currentTemp >= config.tempFull) {
                newPwm = 255;
            } else {
                newPwm = map(
                    (int)(currentTemp * 10),
                    (int)(config.tempOn * 10),
                    (int)(config.tempFull * 10),
                    PWM_MIN, 255);
            }
        }
    }

    // Night cap
    if (settings_is_night()) {
        int cap = (config.nightMax * 255) / 100;
        if (newPwm > cap) newPwm = cap;
    }

    // Phone gate
    if (config.phoneMode == "auto" && !effectivePhone) {
        newPwm = 0;
    }

    fanPWM = newPwm;
    fanPctLocal = map(fanPWM, 0, 255, 0, 100);

    ledcWrite(0, fanPWM);

    // ---- Alarm output ----
    if (config.alarmMode == "off") {
        ledcWrite(BUZZER_CHANNEL, 0);
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

// ------------------------------------------------------------
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