#include "FanController.h"
#include "Config.h"
#include "Settings.h"

#include <OneWire.h>
#include <DallasTemperature.h>

static OneWire oneWire(DS18B20_PIN);
static DallasTemperature ds18b20(&oneWire);

static int fanPWM = 0;
static int fanPct = 0;
static int fanRPM = 0;
static int alertLevel = 0;

static bool phonePresent = false;

static volatile unsigned long tachPulses = 0;
static unsigned long lastTachRead = 0;

static unsigned long lastAlertStart = 0;
static int beepIndex = 0;
static bool beepActive = false;
static unsigned long beepTimer = 0;

// Hysteresis for fan on/off (prevents flapping at threshold)
static bool fanActive = false;


// DS18B20 temperature sensor
void readDS18B20(float &currentTemp) {
    static unsigned long lastRead = 0;
    unsigned long now = millis();

    if (now - lastRead < 2000) return;
    lastRead = now;

    ds18b20.requestTemperatures();
    float t = ds18b20.getTempCByIndex(0);

    if (t == DEVICE_DISCONNECTED_C) {
        Serial.println("[DS18B20] disconnected");
        return;
    }

    currentTemp = t;
}


// Phone presence detection (hall sensor)
void updatePhoneDetection() {
    static bool lastState = false;
    static unsigned long lastChange = 0;

    bool present = (digitalRead(PHONE_SENSE_PIN) == LOW);

    if (present != lastState) {
        unsigned long now = millis();
        if (now - lastChange > 500) {   // debounce
            lastState = present;
            lastChange = now;
            phonePresent = present;
            Serial.printf("[PHONE] %s\n",
                present ? "detected" : "removed");
        }
    }
}


// Beep sequencer
static void runBeepSequence(
    int beeps,
    int beepMs,
    int gapMs,
    int duty,
    int intervalMs
) {
    unsigned long now = millis();

    if (!beepActive && beepIndex == 0) {
        if (now - lastAlertStart >= (unsigned long)intervalMs) {
            lastAlertStart = now;
            beepIndex = 0;
            beepActive = true;
            beepTimer = now;
            ledcWrite(BUZZER_CHANNEL, duty);
            Serial.printf("[BEEP] start %d beeps\n", beeps);
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


// ============================================================
//  Fan and alerts — now uses config.* instead of hardcoded values
// ============================================================
void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
) {
    // ---- Alert level ----
    int newLevel = 0;
    if (currentTemp >= config.alarmPanic) {
        newLevel = 2;
    } else if (currentTemp >= config.alarmWarning) {
        newLevel = 1;
    }

    if (newLevel != alertLevel) {
        alertLevel = newLevel;
        beepActive = false;
        beepIndex = 0;
        ledcWrite(BUZZER_CHANNEL, 0);

        lastAlertStart = millis() -
            (alertLevel == 2 ? PANIC_INTERVAL_MS : WARNING_INTERVAL_MS);

        if (alertLevel == 2)      Serial.println("[ALERT] PANIC");
        else if (alertLevel == 1) Serial.println("[ALERT] WARNING");
        else                      Serial.println("[ALERT] normal");
    }

    // ---- Fan speed ----
    // Determine night cap (as 0-255 PWM)
    int nightCapPwm = (config.nightMax * 255) / 100;

    // Hysteresis: turn on at tempOn + 1, off at tempOn - 1
    if (currentTemp > config.tempOn + 1.0) fanActive = true;
    if (currentTemp < config.tempOn - 1.0) fanActive = false;

    // Calculate fan PWM
    int newPwm = 0;

    if (config.fanMode == "off") {
        newPwm = 0;
        fanActive = false;
    } else if (config.fanMode == "on") {
        newPwm = 255;
    } else {
        // auto — ramp between tempOn and tempFull
        if (fanActive) {
            if (currentTemp >= config.tempFull) {
                newPwm = 255;
            } else {
                newPwm = map(
                    (int)(currentTemp * 10),
                    (int)(config.tempOn * 10),
                    (int)(config.tempFull * 10),
                    PWM_MIN,
                    255
                );
            }
        }
    }

    // Apply night cap
    if (settings_is_night() && newPwm > nightCapPwm) {
        newPwm = nightCapPwm;
    }

    // Phone gate
    if (config.phoneMode == "auto" && !phonePresent) {
        newPwm = 0;
    }

    fanPWM = newPwm;
    fanPct = map(fanPWM, 0, 255, 0, 100);

    ledcWrite(0, fanPWM);

    // ---- Alarm ----
    bool alarmMuted = (config.alarmMode == "off");
    bool alarmAlways = (config.alarmMode == "on");

    if (alarmMuted) {
        ledcWrite(BUZZER_CHANNEL, 0);
    } else if (alarmAlways && alertLevel > 0) {
        runBeepSequence(
            alertLevel == 2 ? PANIC_BEEPS : WARNING_BEEPS,
            alertLevel == 2 ? PANIC_BEEP_MS : WARNING_BEEP_MS,
            alertLevel == 2 ? PANIC_GAP_MS : WARNING_GAP_MS,
            alertLevel == 2 ? BUZZER_LOUD : BUZZER_QUIET,
            alertLevel == 2 ? PANIC_INTERVAL_MS : WARNING_INTERVAL_MS
        );
    } else if (alertLevel == 2) {
        runBeepSequence(
            PANIC_BEEPS,
            PANIC_BEEP_MS,
            PANIC_GAP_MS,
            BUZZER_LOUD,
            PANIC_INTERVAL_MS
        );
    } else if (alertLevel == 1) {
        runBeepSequence(
            WARNING_BEEPS,
            WARNING_BEEP_MS,
            WARNING_GAP_MS,
            BUZZER_QUIET,
            WARNING_INTERVAL_MS
        );
    } else {
        ledcWrite(BUZZER_CHANNEL, 0);
    }

    outFanPct = fanPct;
    outRpm = fanRPM;
    outAlert = alertLevel;
    outPhonePresent = phonePresent;
}


// Tachometer
static void IRAM_ATTR onTach() {
    tachPulses++;
}

void updateTach() {
    unsigned long now = millis();
    if (now - lastTachRead >= 1000) {
        lastTachRead = now;
        fanRPM = (tachPulses * 60) / 2;
        tachPulses = 0;
    }
}


// Hardware initialisation
void initHardware() {
    ds18b20.begin();

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