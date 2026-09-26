#include "DisplayManager.h"
#include "Config.h"
#include "Settings.h"
#include "Logging.h"
#include "WiFiManager.h"
#include "FanController.h"

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306_72x40.h>

#include <time.h>

Adafruit_SSD1306_72x40 display(SDA_PIN, SCL_PIN);

// ============================================================
//  OLED driver — V3.72
//  Bottom line priority: FAN STALL > Log Paused > time
// ============================================================

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
//  Main screen
//
//   25.4 C
//   ████████░░░░░░░░  ← fan bar
//                  12:35   ← time (right-aligned)
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

    // ---- Temperature (size 2, top-left) ----
    display.setTextSize(2);
    display.setCursor(0, 2);
    if (temp > 0.0) {
        char tempBuf[8];
        snprintf(tempBuf, sizeof(tempBuf), "%.1f", temp);
        display.print(tempBuf);
    } else {
        display.print(F("--.-"));
    }

    display.setTextSize(1);
    display.setCursor(46, 8);
    display.print(F("C"));

    // ---- Fan bar (full width) ----
    int barX = 0, barY = 22, barW = 72, barH = 8;
    display.drawRect(barX, barY, barW, barH, SSD1306_WHITE);
    int filled = (fanPct * (barW - 2)) / 100;
    if (filled > 0) {
        display.fillRect(barX + 1, barY + 1, filled, barH - 2, SSD1306_WHITE);
    }

    // ---- Bottom line ----
    display.setTextSize(1);

    if (fan_stall_active()) {
        display.setCursor(0, 33);
        display.print(F("FAN STALL"));
    } else if (log_rotation_paused()) {
        display.setCursor(0, 33);
        display.print(F("Log Paused"));
    } else {
        struct tm timeinfo;
        if (getLocalTime(&timeinfo, 10)) {
            char timeBuf[6];
            snprintf(timeBuf, sizeof(timeBuf), "%02d:%02d",
                     timeinfo.tm_hour, timeinfo.tm_min);
            // Each char is 6px at size 1, 5 chars = 30px, right edge at x=72
            display.setCursor(42, 33);
            display.print(timeBuf);
        }
    }

    display.display();
}

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
void drawOtaScreen(uint8_t pct, uint32_t recv, uint32_t total) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("FW UPDATING"));
    display.setCursor(0, 9);
    display.print(F("Dont touch"));

    int barX = 0, barY = 20, barW = 72, barH = 10;
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

void clearDisplay() {
    display.clearDisplay();
    display.display();
    Serial.println("[OLED] blanked");
}

void wakeDisplay() {
    display.clearDisplay();
    display.display();
    Serial.println("[OLED] restored");
}