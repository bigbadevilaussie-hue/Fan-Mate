#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include "Config.h"

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306_72x40.h>

extern Adafruit_SSD1306_72x40 display;

void initDisplay();

void updateDisplay(
    float temp,
    int fanPct,
    int rpm,
    int alertState,
    bool phonePresent
);

#endif