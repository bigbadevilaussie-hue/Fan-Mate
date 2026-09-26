#include "WeatherClient.h"
#include "Config.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Preferences.h>

static float cachedTemp = -99.0f;
static unsigned long lastFetch = 0;
static Preferences weatherPrefs;

static const char* URL =
    "http://api.open-meteo.com/v1/forecast"
    "?latitude=-27.28&longitude=152.51"
    "&current=temperature_2m"
    "&timezone=Australia%2FBrisbane";

static const unsigned long REFRESH_MS = 15UL * 60UL * 1000UL;

void weather_init() {
    weatherPrefs.begin("weather", true);
    cachedTemp = weatherPrefs.getFloat("temp", -99.0f);
    weatherPrefs.end();
    if (cachedTemp > -90.0f) {
        Serial.printf("[WEATHER] cached: %.1f C\n", cachedTemp);
    }
}

void weather_loop() {
    unsigned long now = millis();
    if (lastFetch > 0 && now - lastFetch < REFRESH_MS) return;
    if (WiFi.status() != WL_CONNECTED) return;

    lastFetch = now;

    HTTPClient http;
    http.begin(URL);
    http.setTimeout(8000);
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
                Serial.printf("[WEATHER] %.1f C\n", t);
            }
        }
    } else {
        Serial.printf("[WEATHER] HTTP %d\n", code);
    }
    http.end();
}

float weather_get_temp() {
    return cachedTemp;
}
