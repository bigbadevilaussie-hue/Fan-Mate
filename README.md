# Fan-Mate — V3.23

ESP32-C3 fan controller for keeping an iPhone cool on a 24/7 hotspot mount. Network-triggered boost control. WiFi + HTTP. No BLE.

Watches the router's WAN traffic rate and spins a 4-wire PWM fan when downloads are detected. Reads phone-case temperature and sounds warnings when thresholds are crossed. Detects phone presence via hall sensor.

---

## Hardware

| Component | Notes |
|---|---|
| MCU | ESP32-C3 SuperMini with onboard 72x40 OLED |
| Temperature | DS18B20 waterproof probe, 1m cable, 1-Wire |
| Phone detection | A3144 hall sensor (TO-92), in mount adapter |
| Fan | 4-wire 5V PWM fan, 40x40x10mm, 0.1A |
| Buzzer | SFM-27 piezo, 3-24V |
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
| 8 | Blue LED | Onboard, active-LOW |
| 10 | Buzzer | 2 kHz, 8-bit |

---

## Architecture

The ESP32 is fully autonomous. The GUI is optional - a viewer and remote control.

| Function | ESP32 | GUI |
|---|---|---|
| Phone detection | yes | Display only |
| Traffic monitoring | yes (Opal poll) | Display only |
| Boost trigger | yes | Display only |
| Fan control | yes | Display only |
| Logging | yes (LittleFS) | Sync + clear |
| NTP time sync | - | POST /time on connect |
| OTA | yes (HTTP endpoint) | Trigger only |
| Settings | yes (NVS persist) | Edit interface |
| OLED | yes | - |
| Buzzer | yes | - |

If the GUI never runs, the ESP32 keeps logging, cooling, running - indefinitely.

---

## Features

### Network-triggered boost

The fan is driven by network activity, not phone temperature. At 24/7 idle, the phone produces no heat. Only traffic heats the modem.

Boost fires on the router's WAN rate. When sustained activity crosses threshold for N consecutive ticks, the fan goes to 100%. When traffic drops, the fan releases after the off-hold.

Current config (V3.23): single threshold, single hold.

| Setting | Value |
|---|---|
| Threshold | 300 KB/s |
| Hold | 4 ticks (60s) |

Configurable via the GUI.

### Alarm thresholds

| Temperature | Action |
|---|---|
| 45C | Warning - 2 beeps, every 2 min |
| 50C | Panic - 5 beeps, every 2 min |

### Fan control

- 25 kHz PWM, inaudible
- 8-bit resolution
- Boost triggers 100% fan
- Tach feedback for RPM reading

### Logging

CSV log in LittleFS at /log.csv:


Written every 15s while active. Max size 512 KB. Cleared manually via POST /log/clear.

### HTTP API

| Endpoint | Method | Purpose |
|---|---|---|
| / | GET | HTML dashboard |
| /status | GET | JSON telemetry |
| /config | GET | Full config |
| /config | POST | Update config |
| /time | POST | Set RTC |
| /log.csv | GET | Stream log |
| /log/info | GET | Log size/status |
| /log/clear | POST | Wipe log |
| /reboot | GET | Restart |
| /ota | POST | Firmware upload |

---

## File layout

| File | Purpose |
|---|---|
| fanmate.ino | Main, setup, loop |
| Config.h | Pins, constants, version |
| Settings.cpp/.h | Config load/save, JSON parse |
| FanController.cpp/.h | DS18B20, hall, PWM, tach, buzzer |
| DisplayManager.cpp/.h | OLED rendering |
| WiFiManager.cpp/.h | WiFi, mDNS |
| WebServer.cpp/.h | HTTP endpoints |
| OpalClient.cpp/.h | Router login, WAN traffic poll |
| AutoBoost.cpp/.h | Boost state machine |
| Logging.cpp/.h | Log write, size check |
| fanmate.py | Companion Python GUI (optional) |

---

## GUI (companion)

Python/Tk on the Mac. Reads /status every 10s. Pushes config changes to /config.

- Live telemetry (temp, fan, RPM, phone, alert)
- Weather (Open-Meteo, Brisbane)
- Temperature history graph
- TURBO badge when boost fires
- Settings dialog with Boost / Alarm / Night / Phone sections
- Log sync, log clear, OTA update
- Day/night theme

---

## Build

1. Arduino IDE 2.x
2. Board: ESP32C3 Dev Module
3. ESP32 core: 2.0.17 (2.x required)
4. Libraries: Adafruit GFX, Adafruit BusIO, Adafruit SSD1306, Adafruit_SSD1306_72x40, OneWire, DallasTemperature, ArduinoJson
5. Create secrets.h with WiFi credentials (see secrets.example.h)
6. Open fanmate.ino, compile, upload

---

## Version history

| Version | Notes |
|---|---|
| V2.00 | Modularised. Fake sensor. |
| V2.01 | Real DS18B20 on GPIO 4. |
| V2.02 | Hall sensor phone detection. |
| V2.03 | OTA over BLE. |
| V2.11 | Flow-control OTA at MTU 23. |
| V2.23 | Auto Boost + en1 monitoring. |
| V3.00 | WiFi + HTTP server alongside BLE. |
| V3.02 | AutoBoost, OpalClient, Logging. fan.mode removed. |
| V3.23 | LED on Opal request. Real time in log + OLED. |
| V4.00 | (in development) NTP at boot, DS18B20 warmup, sleep state machine, 3-tier alarm, mode-based boost (normal/aggressive), 7-column log with events, adaptive logging, peak-hold smoothing, boost-only fan control, hall-sensor sleep/wake. |

---

## Related

- Bike-Mate: https://github.com/bigbadevilaussie-hue/Bike-Mate

## License

No license. Personal project.
