#include "WeatherClient.h"
#include "Config.h"
#include "WiFiManager.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

static float cachedTemp = -99.0f;
static unsigned long lastFetch = 0;
static Preferences weatherPrefs;

static const char* URL =
    "http://api.open-meteo.com/v1/forecast"
    "?latitude=-27.4219&longitude=152.4339"
    "&current=temperature_2m"
    "&timezone=Australia%2FBrisbane";

static const unsigned long REFRESH_MS = 5UL * 60UL * 1000UL;

void weather_init() {
    weatherPrefs.begin("weather", true);
    cachedTemp = weatherPrefs.getFloat("temp", -99.0f);
    weatherPrefs.end();
    if (cachedTemp > -90.0f) {
        Serial.printf("[WEATHER] cached: %.1f C\n", cachedTemp);
    }
}

void weather_loop() {
    static unsigned long lastAttempt = 0;
    static uint8_t       fails       = 0;
    unsigned long now = millis();
    if (lastFetch > 0 && now - lastFetch < REFRESH_MS) return;
    if (WiFi.status() != WL_CONNECTED) return;

    // v4.62: back off after failures (60 s, 2 m, 4 m, 8 m, 15 m cap).
    // Before this, a failed fetch retried on every loop() pass.
    unsigned long backoff = fails == 0 ? 0UL
                          : (fails >= 5 ? 900000UL : (30000UL << fails));
    if (lastAttempt > 0 && now - lastAttempt < backoff) return;
    lastAttempt = now;
    if (!upstream_reachable()) { if (fails < 255) fails++; return; }

    HTTPClient http;
    http.begin(URL);
    http.setConnectTimeout(1500);
    http.setTimeout(2000);
    int code = http.GET();

    if (code == 200) {
        String body = http.getString();
        StaticJsonDocument<512> doc;
        if (deserializeJson(doc, body) == DeserializationError::Ok) {
            float t = doc["current"]["temperature_2m"] | -99.0f;
            if (t > -90.0f) {
                cachedTemp = t;
                weatherPrefs.begin("weather", false);
                weatherPrefs.putFloat("temp", t);
                weatherPrefs.end();
                lastFetch = now;      // only on success
                Serial.printf("[WEATHER] %.1f C\n", t);
            }
        }
    } else {
        Serial.printf("[WEATHER] HTTP %d\n", code);
    }
    http.end();
    if (lastFetch == now) fails = 0; else if (fails < 255) fails++;
}

float weather_get_temp() {
    return cachedTemp;
}
