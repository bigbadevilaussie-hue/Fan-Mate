#include "DisplayManager.h"
#include "Config.h"

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306_72x40.h>
#include <time.h>

static Adafruit_SSD1306_72x40 display(SDA_PIN, SCL_PIN);

// ============================================================
//  DisplayManager — OLED rendering + sleep screen
//  V3.32
// ============================================================

void initDisplay() {
    if (!display.begin()) {
        Serial.println("[OLED] begin failed");
        return;
    }
    display.clearDisplay();
    display.display();
    display.ssd1306_command(SSD1306_DISPLAYON);
    Serial.println("[OLED] ready");
}

// ------------------------------------------------------------
void drawSplashScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 4);
    display.println("FAN-MATE");
    display.setCursor(2, 16);
    display.printf("v%s", FAN_MATE_VERSION);
    display.setCursor(2, 28);
    display.println("booting...");
    display.display();
    Serial.println("[OLED] splash shown");
}

// ------------------------------------------------------------
//  Sleep / wake
// ------------------------------------------------------------
void clearDisplay() {
    display.clearDisplay();
    display.display();
    delay(50);
    display.ssd1306_command(SSD1306_DISPLAYOFF);
    Serial.println("[OLED] off");
}

void wakeDisplay() {
    display.ssd1306_command(SSD1306_DISPLAYON);
    delay(50);
    display.clearDisplay();
    display.display();
    Serial.println("[OLED] on");
}

// ------------------------------------------------------------
//  Normal display
// ------------------------------------------------------------
void updateDisplay(float temp, int fanPct, int rpm,
                   int alertState, bool phonePresent) {
    display.clearDisplay();

    // Line 1: temp + fan
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 2);
    display.printf("%.1fC", temp);

    display.setCursor(40, 2);
    if (fanPct == 0) {
        display.print("off");
    } else {
        display.printf("%d%%", fanPct);
    }

    // Line 2: rpm
    display.setCursor(2, 14);
    display.printf("RPM %d", rpm);

    // Line 3: phone / alert
    display.setCursor(2, 26);
    display.printf("PH %s", phonePresent ? "Y" : "N");

    display.setCursor(40, 26);
    if (alertState == 2)      display.print("!PANIC");
    else if (alertState == 1) display.print("!WARN");
    else                      display.print("OK");

    // Bottom right: time
    time_t now = time(nullptr);
    if (now >= 1700000000UL) {
        struct tm tm;
        localtime_r(&now, &tm);
        display.setCursor(48, 34);
        display.printf("%02d:%02d", tm.tm_hour, tm.tm_min);
    }

    display.display();
}

// ------------------------------------------------------------
//  OTA screens
// ------------------------------------------------------------
void drawOtaScreen(uint8_t pct, uint32_t recv, uint32_t total) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 2);
    display.println("OTA UPDATE");
    display.setCursor(2, 16);
    display.printf("%u%%", pct);

    // Progress bar
    int barW = (70 * pct) / 100;
    display.drawRect(1, 28, 70, 8, SSD1306_WHITE);
    display.fillRect(2, 29, barW, 6, SSD1306_WHITE);

    display.display();
}

void drawFwStartScreen() {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 8);
    display.println("Firmware");
    display.setCursor(2, 20);
    display.println("starting...");
    display.display();
}

void drawRebootScreen(int secondsLeft) {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(2, 8);
    display.println("Rebooting");
    display.setCursor(2, 20);
    display.printf("in %ds...", secondsLeft);
    display.display();
}