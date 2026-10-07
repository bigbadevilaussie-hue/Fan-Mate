# Fan-Mate

ESP32-C3 fan controller that keeps an iPhone cool on a 24/7 hotspot mount.

The iPhone is the sole internet uplink (weak signal, rural Queensland). Every byte through the network heats its cellular modem. Fan-Mate watches the router WAN traffic rate and spins a 40mm PWM fan when downloads are detected — before the phone gets hot, not after.

Current: **FW v4.50** · **Tk GUI v4.50** · **QML GUI2 v1.11** (parked)

Repo: https://github.com/bigbadevilaussie-hue/Fan-Mate

## Hardware

| Component | Pin | Notes |
|---|---|---|
| MCU | — | ESP32-C3 SuperMini |
| Thermistor (NTC) | GPIO 0 | 10k MF52AT, room temp, +6.0 offset |
| Hall sensor | GPIO 1 | A3144, phone presence |
| Fan tach | GPIO 3 | INPUT_PULLUP, IRQ |
| DS18B20 | GPIO 4 | Phone back contact |
| OLED SDA / SCL | GPIO 5 / 6 | I2C |
| Fan PWM | GPIO 7 | 25 kHz, 8-bit |
| Blue LED | GPIO 8 | onboard |
| Buzzer | GPIO 10 | LEDC channel 1 |

Shroud printed, mounted on Quad Lock adapter. Phone docked. DS18B20 in the Quad Lock socket against the case back. Fan over the camera bump, adjacent to the SoC.

## What it does

- **Network-triggered boost** — responds to router WAN traffic, not phone temp. Traffic heats the modem before the phone surface warms.
- **Rate-based gears** — target gear = `floor(net_kbps / threshold)`, clamp 0–4, with up/down hysteresis.
- **Cooldown hold** — when traffic stops, holds gear 1 until phone temp returns to the pre-boost value (or 20-min timeout).
- **Delta guard** — phone 5.1°C above room → gear 1 floor. Configurable.
- **Heat control** — four thresholds (Warm/Hot/Hotter/Critical = 33/35/37/39) with per-gear hysteresis.
- **Priority** — `max(heat, delta, boost)`.
- **Kill mode** — at Critical: fan 100%, buzzer every 30s, repeater cut. Manual re-arm.
- **Autonomous** — cools and logs whether the Mac is on or off. Sleeps when phone absent.
- **Hourly log rotation** — sealed, CRC32-verified Mac sync, Drive upload.

## Build

Arduino IDE 2.x or arduino-cli. ESP32 core **2.0.17** (2.x required — do NOT upgrade to 3.x).

Partition: `:PartitionScheme=min_spiffs` (1408 KB LittleFS).

```zsh
arduino-cli compile --fqbn esp32:esp32:esp32c3:PartitionScheme=min_spiffs --export-binaries .
# binary: build/esp32.esp32.esp32c3/fanmate.ino.bin
```

Libraries: Adafruit GFX, Adafruit BusIO, Adafruit SSD1306, OneWire, DallasTemperature, ArduinoJson.

Secrets: copy `secrets.example.h` to `secrets.h`, fill WiFi + Opal credentials.

OTA: Tk GUI menu → 📡 Update Firmware.

## GUI

**Tk GUI** (primary) — `python3 fanmate.py`. Live telemetry, Settings, Reports, DynaTune KPI board, OTA, log sync, weather, day/night theme.

**QML GUI2** (parked) — `fanmate_v2/*`. Ports frozen behaviour once firmware + Tk are stable.

**Web dashboard** — served by ESP32 at `/`. Read-only except kill-mode banner.

## Repo

https://github.com/bigbadevilaussie-hue/Fan-Mate

Related: https://github.com/bigbadevilaussie-hue/Bike-Mate
