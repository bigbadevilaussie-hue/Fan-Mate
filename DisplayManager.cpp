#include "DisplayManager.h"

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

    // Temperature
    display.setTextSize(2);
    display.setCursor(0, 0);

    char tempBuf[8];
    sprintf(tempBuf, "%.1fC", temp);
    display.print(tempBuf);

    // Fan bar
    int barX = 50;
    int barY = 2;
    int barW = 20;
    int barH = 12;

    display.drawRect(
        barX,
        barY,
        barW,
        barH,
        SSD1306_WHITE
    );

    int filled = (fanPct * (barW - 2)) / 100;

    if (filled > 0) {
        display.fillRect(
            barX + 1,
            barY + 1,
            filled,
            barH - 2,
            SSD1306_WHITE
        );
    }

    display.drawLine(
        0,
        17,
        72,
        17,
        SSD1306_WHITE
    );

    // Fan percentage
    display.setTextSize(1);
    display.setCursor(0, 20);

    char fanBuf[12];
    sprintf(fanBuf, "Fan:%3d%%", fanPct);
    display.print(fanBuf);

    // Status
    display.setCursor(0, 29);

    if (alertState == 2) {
        display.print(F("!! PANIC !!"));
    }
    else if (alertState == 1) {
        display.print(F("Warning"));
    }
    else if (phonePresent) {
        display.print(F("Ready"));
    }
    else {
        display.print(F("No phone"));
    }

    display.display();
}