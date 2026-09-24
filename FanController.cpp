#include "FanController.h"
#include "Config.h"

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


// DS18B20 temperature sensor
void readDS18B20(float &currentTemp) {

    static unsigned long lastRead = 0;

    unsigned long now = millis();

    if (now - lastRead < 2000) {
        return;
    }

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

    // Active LOW — hall sensor triggers when magnet is near
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

        if (
            now - lastAlertStart >=
            (unsigned long)intervalMs
        ) {

            lastAlertStart = now;
            beepIndex = 0;
            beepActive = true;
            beepTimer = now;

            ledcWrite(
                BUZZER_CHANNEL,
                duty
            );

            Serial.printf(
                "[BEEP] start %d beeps\n",
                beeps
            );
        }

        return;
    }

    if (!beepActive) {
        return;
    }

    if (
        beepActive &&
        now - beepTimer >=
        (unsigned long)beepMs
    ) {

        ledcWrite(
            BUZZER_CHANNEL,
            0
        );

        beepActive = false;
        beepTimer = now;

    } else if (
        !beepActive &&
        now - beepTimer >=
        (unsigned long)gapMs
    ) {

        beepIndex++;

        if (beepIndex >= beeps) {

            beepIndex = 0;
            beepActive = false;
            lastAlertStart = now;

        } else {

            ledcWrite(
                BUZZER_CHANNEL,
                duty
            );

            beepActive = true;
            beepTimer = now;
        }
    }
}


// Fan and alerts
void updateFanAndAlerts(
    float currentTemp,
    int &outFanPct,
    int &outRpm,
    int &outAlert,
    bool &outPhonePresent
) {

    int newLevel = 0;

    if (currentTemp >= TEMP_PANIC) {
        newLevel = 2;
    }
    else if (currentTemp >= TEMP_WARNING) {
        newLevel = 1;
    }
    else {
        newLevel = 0;
    }

    if (newLevel != alertLevel) {

        alertLevel = newLevel;

        beepActive = false;
        beepIndex = 0;

        ledcWrite(
            BUZZER_CHANNEL,
            0
        );

        lastAlertStart =
            millis() -
            (
                alertLevel == 2
                ? PANIC_INTERVAL_MS
                : WARNING_INTERVAL_MS
            );

        if (alertLevel == 2) {
            Serial.println("[ALERT] PANIC");
        }
        else if (alertLevel == 1) {
            Serial.println("[ALERT] WARNING");
        }
        else {
            Serial.println("[ALERT] normal");
        }
    }

    int fanMax =
        (alertLevel == 2)
        ? FAN_MAX_PANIC
        : FAN_MAX_WARN;

    if (currentTemp >= TEMP_FULL) {

        fanPWM = fanMax;

    }
    else if (currentTemp > TEMP_ON) {

        fanPWM = map(
            (int)(currentTemp * 10),
            (int)(TEMP_ON * 10),
            (int)(TEMP_FULL * 10),
            PWM_MIN,
            fanMax
        );

    }
    else {

        fanPWM = 0;
    }

    fanPct = map(
        fanPWM,
        0,
        255,
        0,
        100
    );

    ledcWrite(
        0,
        fanPWM
    );

    if (!phonePresent) {

        ledcWrite(
            BUZZER_CHANNEL,
            0
        );

    }
    else if (alertLevel == 2) {

        runBeepSequence(
            PANIC_BEEPS,
            PANIC_BEEP_MS,
            PANIC_GAP_MS,
            BUZZER_LOUD,
            PANIC_INTERVAL_MS
        );

    }
    else if (alertLevel == 1) {

        runBeepSequence(
            WARNING_BEEPS,
            WARNING_BEEP_MS,
            WARNING_GAP_MS,
            BUZZER_QUIET,
            WARNING_INTERVAL_MS
        );

    }
    else {

        ledcWrite(
            BUZZER_CHANNEL,
            0
        );
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

        fanRPM =
            (tachPulses * 60) / 2;

        tachPulses = 0;
    }
}


// Hardware initialisation
void initHardware() {

    ds18b20.begin();

    pinMode(
        PHONE_SENSE_PIN,
        INPUT_PULLUP
    );

    ledcSetup(
        0,
        PWM_FREQ,
        PWM_RES
    );

    ledcAttachPin(
        FAN_PWM_PIN,
        0
    );

    ledcWrite(
        0,
        0
    );

    ledcSetup(
        BUZZER_CHANNEL,
        BUZZER_FREQ,
        BUZZER_RES
    );

    ledcAttachPin(
        BUZZER_PIN,
        BUZZER_CHANNEL
    );

    ledcWrite(
        BUZZER_CHANNEL,
        0
    );

    pinMode(
        TACH_PIN,
        INPUT_PULLUP
    );

    attachInterrupt(
        digitalPinToInterrupt(TACH_PIN),
        onTach,
        FALLING
    );
}