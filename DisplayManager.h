#ifndef DISPLAY_MANAGER_H
#define DISPLAY_MANAGER_H

#include <Arduino.h>

void initDisplay();
void drawSplashScreen();
void updateDisplay(float temp, int fanPct, int rpm,
                   int alertState, bool phonePresent);
void drawOtaScreen(uint8_t pct, uint32_t recv, uint32_t total);
void drawFwStartScreen();
void drawRebootScreen(int secondsLeft);

#endif
