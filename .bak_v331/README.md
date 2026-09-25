# Fan-Mate — V2.02

Thermostatic PWM fan controller for keeping an iPhone cool on a 24/7 charge mount. ESP32-C3 + OLED + DS18B20 + 4-wire fan + hall sensor + buzzer + BLE.

Reads phone-case temperature from a DS18B20 waterproof probe, ramps a 4-wire 5V PWM fan from off to full based on a configurable temperature curve, sounds warnings and panic alarms when thresholds are crossed, and detects phone presence via a hall sensor.

## Hardware

| Component | Notes |
|---|---|
| MCU | ESP32-C3 SuperMini with onboard 72x40 OLED |
| Temperature | DS18B20 waterproof probe, 1m cable, 1-Wire |
| Phone detection | A3144 hall sensor (TO-92), in mount adapter |
| Fan | 4-wire 5V PWM fan, 40x40x10mm, 0.1A |
| Buzzer | SFM-27 piezo, 3-24V (direct GPIO drive, quiet) |
| Power | USB-C 5V, 2A supply |

## Pin map

| GPIO | Function | Notes |
|---|---|---|
| 1 | Phone presence (hall) | Input, pull-up, LOW = present |
| 3 | Fan tach | Input, pull-up, falling edge |
| 4 | DS18B20 data | 1-Wire, 4.7k pull-up to 3V3 |
| 5 | OLED SDA | I2C |
| 6 | OLED SCL | I2C |
| 7 | Fan PWM | 25 kHz, 8-bit |
| 10 | Buzzer | 2 kHz, 8-bit |

## Features

### Temperature monitoring
- DS18B20 digital sensor, +/-0.5C accuracy
- Waterproof probe through mount adapter to touch phone case
- Read every 2s while active

### Phone presence detection
- A3144 hall sensor in the mount adapter
- Detects phone presence via case magnetic field
- Debounced 500 ms
- Reported over BLE to GUI

### Fan control
- 25 kHz PWM, inaudible
- 8-bit resolution, 256 speed steps
- PWM_MIN 40 for reliable spin-up
- Linear ramp between TEMP_ON and TEMP_FULL
- Tach feedback for RPM reading

### Temperature thresholds

| Temperature | Action |
|---|---|
| 34C | Fan starts (minimum speed) |
| 42C | Fan full speed |
| 45C | Warning - 2 beeps, every 2 min |
| 50C | Panic - 5 beeps, every 2 min |

### BLE

- Device name: Fan-Mate
- Service UUID: 4fafc201-1fb5-459e-8fcc-c5c9c331914b
- DATA characteristic - JSON status every 2s
  - Fields: temp, fan, rpm, phone, alert
- TIME characteristic - GUI writes Unix epoch on connect

## File layout

| File | Purpose |
|---|---|
| fanmate.ino | Main coordinator |
| Config.h | Pins, thresholds, PWM, UUIDs |
| FanController.cpp/.h | DS18B20, hall, PWM fan, tach, alerts |
| DisplayManager.cpp/.h | OLED rendering |
| BleManager.cpp/.h | BLE server |
| fanmate.py | Companion Python GUI |

## Build

1. Arduino IDE 2.x
2. Board: ESP32C3 Dev Module
3. ESP32 core: 2.0.17 (2.x required)
4. Libraries: Adafruit GFX, BusIO, SSD1306, Adafruit_SSD1306_72x40, OneWire, DallasTemperature
5. Open fanmate.ino, compile, upload

## Version history

| Version | Notes |
|---|---|
| V2.00 | Modularised. Fake sensor. |
| V2.01 | Real DS18B20 on GPIO 4. |
| V2.02 | Hall sensor phone detection on GPIO 1. |

## Related

- Bike-Mate: https://github.com/bigbadevilaussie-hue/Bike-Mate

## License

No license. Personal project.
