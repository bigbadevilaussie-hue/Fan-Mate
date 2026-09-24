#include "DisplayManager.h"
#include "Config.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306_72x40.h>

// Exact OLED driver from the known-good FAN-MATE V1.10
Adafruit_SSD1306_72x40 display(SDA_PIN, SCL_PIN);

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

void drawSplashScreen() {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(2);
    display.setCursor(2, 0);
    display.print(F("FAN-MATE"));
    display.setTextSize(1);
    display.setCursor(24, 20);
    display.print(F("V"));
    display.print(FAN_MATE_VERSION);
    display.setCursor(8, 32);
    display.print(F("Booting..."));
    display.display();
    Serial.println("[OLED] splash shown");
}

void updateDisplay(
    float temp,
    int fanPct,
    int rpm,
    int alertState,
    bool phonePresent
) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);

    display.setTextSize(2);
    display.setCursor(0, 0);
    char tempBuf[8];
    sprintf(tempBuf, "%.1fC", temp);
    display.print(tempBuf);

    int barX = 50;
    int barY = 2;
    int barW = 20;
    int barH = 12;
    display.drawRect(barX, barY, barW, barH, SSD1306_WHITE);
    int filled = (fanPct * (barW - 2)) / 100;
    if (filled > 0) {
        display.fillRect(barX + 1, barY + 1, filled, barH - 2, SSD1306_WHITE);
    }

    display.drawLine(0, 17, 72, 17, SSD1306_WHITE);

    display.setTextSize(1);
    display.setCursor(0, 20);
    char fanBuf[12];
    sprintf(fanBuf, "Fan:%3d%%", fanPct);
    display.print(fanBuf);

    display.setCursor(0, 29);
    if (alertState == 2) {
        display.print(F("!! PANIC !!"));
    } else if (alertState == 1) {
        display.print(F("Warning"));
    } else if (phonePresent) {
        display.print(F("Ready"));
    } else {
        display.print(F("No phone"));
    }

    display.display();
}

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

void drawRebootScreen(int secondsLeft) {
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.print(F("FW COMPLETE"));
    display.setCursor(0, 12);
    display.print(F("Rebooting in"));
    display.setTextSize(2);
    display.setCursor(30, 22);
    display.print(secondsLeft);
    display.display();
    Serial.printf("[OLED] reboot countdown: %d\n", secondsLeft);
}
