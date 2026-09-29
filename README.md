# Fan-Mate

ESP32-C3 fan controller that keeps an iPhone cool on a 24/7 hotspot mount.

The iPhone is the sole internet uplink (weak signal, rural Queensland). Every byte through the network heats its cellular modem. Fan-Mate watches the router's WAN traffic rate and spins a 40mm PWM fan when downloads are detected — before the phone gets hot, not after.

---

## Hardware

| Component | Notes |
|---|---|
| MCU | ESP32-C3 SuperMini |
| Display | 72x40 SSD1306 OLED |
| Temperature | DS18B20 waterproof probe (phone back contact) |
| Phone detection | A3144 hall sensor + Quad Lock magnet |
| Fan | 40mm 4-wire PWM, 5V, 0.1A |
| Buzzer | SFM-27 piezo |
| Power | USB-C 5V, 2A |

### Pin map

| GPIO | Function |
|------|----------|
| 0 | Thermistor (NTC room temp, planned) |
| 1 | Hall sensor (phone presence) |
| 3 | Fan tach |
| 4 | DS18B20 |
| 5 | OLED SDA |
| 6 | OLED SCL |
| 7 | Fan PWM (25 kHz) |
| 8 | Blue LED |
| 10 | Buzzer |

---

## What it does

**Network-triggered boost.** The fan responds to router WAN traffic, not to the phone temperature. Traffic heats the modem *before* the phone surface warms. By the time the DS18B20 sees heat, the modem is already cooking. Fan-Mate watches the leading indicator.

**Auto Boost with hysteresis.** Network rate crosses threshold → fan steps up one gear per 4 ticks (60s) → up to 4 gears (25/50/75/100% PWM). Traffic drops below 0.8 × threshold → steps back down. No jitter, no chatter.

**Hourly log rotation.** Log sealed every hour, streamed to the Mac over WiFi, CRC32 verified, then deleted from the ESP32. Files named `log-vX.YY-YYYYMMDD-HHMM.csv`.

**OTA over HTTP.** Compiled binary uploaded from the Mac GUI. Device reboots into new firmware.

**Autonomous.** ESP32 keeps cooling and logging whether the Mac is on or off. Sleeps when the phone is absent, wakes when it returns.

---

## Firmware

Current version: **V4.08**

### HTTP API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Web dashboard |
| `/status` | GET | JSON telemetry |
| `/config` | GET/POST | Config read/update |
| `/time` | POST | Set RTC |
| `/log.csv` | GET | Live log |
| `/log/list` | GET | Sealed file list |
| `/log/file` | GET | Stream sealed file |
| `/log/ack` | POST | Confirm, delete |
| `/log/nack` | POST | CRC failed, keep |
| `/log/info` | GET | Log stats |
| `/log/clear` | POST | Wipe live log |
| `/serial` | GET | Serial page |
| `/serial-raw` | GET | Text serial dump |
| `/reboot` | GET | Restart |
| `/ota` | POST | Firmware upload |

### Log format


---

## Web Dashboard

Open `http://fan-mate.local/` from any browser on the same network — iPhone, iPad, iMac.

- Portrait layout, 420px max-width
- Live refresh every 5s
- Cards: weather, phone temp, fan/RPM, phone/status, clock
- Graphs: network rate, temperature history (15 min)
- Threshold lines drawn on graphs

Read-only. For settings, use the Tk GUI.

---

## Tk GUI

Python 3 on the Mac. Full control.

- Live telemetry every 10s
- Settings dialog (Heat / Boost / Night / Phone)
- Reports: Last 2 Hours, Daily, Weekly
- DynaTune health check
- OTA updates
- Log sync
- Weather card

Launcher: `python3 fanmate.py`

---

## Build

1. Arduino IDE 2.x, or arduino-cli 0.35.3
2. Board: **ESP32C3 Dev Module**
3. ESP32 core: **2.0.17** (2.x required — do NOT upgrade to 3.x)
4. Libraries: Adafruit GFX, Adafruit BusIO, Adafruit SSD1306, OneWire, DallasTemperature, ArduinoJson
5. Create `secrets.h` with WiFi credentials (see `secrets.example.h`)
6. Compile:

---

## Repo layout


---

## Related

- Bike-Mate: https://github.com/bigbadevilaussie-hue/Bike-Mate
- Same author, same stack, different application (motorcycle battery + ride logger)

---

## License

No license. Personal project.
