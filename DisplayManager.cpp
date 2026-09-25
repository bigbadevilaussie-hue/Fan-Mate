#include "DisplayManager.h"
#include "Config.h"
#include "Settings.h"
#include "WiFiManager.h"

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306_72x40.h>

#include <time.h>

// Exact OLED driver from the known-good FAN-MATE V1.10
Adafruit_SSD1306_72x40 display(SDA_PIN, SCL_PIN);

// ------------------------------------------------------------
//  Init
// ------------------------------------------------------------
void initDisplay() {
    Wire.begin(SDA_PIN, SCL_PIN);
    display.begin();
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("Fan-Mate V"));
    display.print(FAN_MATE_VERSION);
    display.display();
    Serial.println("[OLED] ready");
}

// ------------------------------------------------------------
//  Splash
// ------------------------------------------------------------
void drawSplashScreen() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    display.setTextSize(1);
    display.setCursor(8, 4);
    display.print(F("Fan-Mate"));

    display.setCursor(24, 16);
    display.print(F("V"));
    display.print(FAN_MATE_VERSION);

    display.setCursor(8, 30);
    display.print(F("Booting..."));

    display.display();
    Serial.println("[OLED] splash shown");
}

// ------------------------------------------------------------
//  Main screen — temp, time, fan bar, IP
// ------------------------------------------------------------
void updateDisplay(
    float temp,
    int fanPct,
    int rpm,
    int alertState,
    bool phonePresent
) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    // ---- Big temperature (size 2, top-left) ----
    display.setTextSize(2);
    display.setCursor(0, 2);
    char tempBuf[8];
    snprintf(tempBuf, sizeof(tempBuf), "%.1f", temp);
    display.print(tempBuf);

    display.setTextSize(1);
    display.setCursor(46, 8);
    display.print(F("C"));

    // ---- Fan bar (full width, middle) ----
    int barX = 0;
    int barY = 22;
    int barW = 72;
    int barH = 8;

    display.drawRect(barX, barY, barW, barH, SSD1306_WHITE);

    int filled = (fanPct * (barW - 2)) / 100;
    if (filled > 0) {
        display.fillRect(barX + 1, barY + 1, filled, barH - 2, SSD1306_WHITE);
    }

    // ---- Bottom line: IP if connected, else time ----
    display.setTextSize(1);
    display.setCursor(0, 33);

    if (wifi_connected()) {
        String ip = wifi_ip();
        display.print(ip);
    } else {
        // Fallback: show time
        struct tm timeinfo;
        if (getLocalTime(&timeinfo, 10)) {
            char timeBuf[6];
            snprintf(timeBuf, sizeof(timeBuf), "%02d:%02d",
                     timeinfo.tm_hour, timeinfo.tm_min);
            display.print(timeBuf);
        } else {
            display.print(F("no wifi"));
        }
    }

    display.display();
}

// ------------------------------------------------------------
//  FW update start
// ------------------------------------------------------------
void drawFwStartScreen() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("FW UPDATING"));
    display.setCursor(0, 14);
    display.print(F("Dont touch"));
    display.setCursor(0, 28);
    display.print(F("Starting..."));
    display.display();
    Serial.println("[OLED] FW start shown");
}

// ------------------------------------------------------------
//  FW update progress
// ------------------------------------------------------------
void drawOtaScreen(uint8_t pct, uint32_t recv, uint32_t total) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("FW UPDATING"));
    display.setCursor(0, 9);
    display.print(F("Dont touch"));

    int barX = 0;
    int barY = 20;
    int barW = 72;
    int barH = 10;
    display.drawRect(barX, barY, barW, barH, SSD1306_WHITE);

    int filled = (pct * (barW - 2)) / 100;
    if (filled > 0) {
        display.fillRect(barX + 1, barY + 1, filled, barH - 2, SSD1306_WHITE);
    }

    display.setCursor(0, 32);
    display.print(pct);
    display.print('%');

    display.setCursor(30, 32);
    display.print(recv / 1024);
    display.print('/');
    display.print(total / 1024);
    display.print('K');

    display.display();
}

// ------------------------------------------------------------
//  Reboot countdown
// ------------------------------------------------------------
void drawRebootScreen(int secondsLeft) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("FW COMPLETE"));
    display.setCursor(0, 14);
    display.print(F("Rebooting in"));
    display.setTextSize(2);
    display.setCursor(30, 24);
    display.print(secondsLeft);
    display.display();
    Serial.printf("[OLED] reboot countdown: %d\n", secondsLeft);
}