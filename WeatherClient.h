#ifndef WEATHER_CLIENT_H
#define WEATHER_CLIENT_H

#include <Arduino.h>

void  weather_init();
void  weather_loop();
float weather_get_temp();   // returns -99 if never fetched

#endif
