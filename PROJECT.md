# Fan-Mate — Project Status

**Last updated:** 2026-09-26
**Current version:** v3.43 (firmware + GUI)
**Next version:** v3.44

## What it does

ESP32-C3 controlled PWM fan for an iPhone hotspot mount. Cools the phone when network traffic heats the cellular modem.

The iPhone is the sole internet uplink (weak signal, ~-101 dBm, 16 km from tower). Every byte through the network heats its modem. Fan-Mate watches the router's WAN traffic rate and spins a fan when downloads are detected.

## Repo

https://github.com/bigbadevilaussie-hue/Fan-Mate

## Current state

- **Firmware:** v3.43 running on ESP32-C3 at fan-mate.local (192.168.8.242)
- **GUI:** Python/Tk on Mac, v3.43
- **Logs:** ~/Documents/FanMate_logs/ (Mac) + /log.csv (ESP32 LittleFS)
- **Serial web page:** http://fan-mate.local/serial

## Build environment

- **macOS:** Catalina (Intel x86_64)
- **Arduino CLI:** v0.35.3 (v1.x crashes on Catalina)
- **ESP32 core:** 2.0.17 (do NOT upgrade to 3.x)
- **Arduino IDE:** 2.2.1 (works, but CLI preferred)

### CLI aliases (in ~/.zshrc)

- fmcd — cd to project
- fmbuild — compile + export .bin
- fmota — upload .bin to ESP32
- fmfw — check firmware version
- fmstatus — full /status JSON
- fmlog — last 10 log rows
- fmserial — last 20 serial lines
- fmdeploy — compile + OTA + verify

## Working features

### Firmware

- NTP at boot — real timestamps in logs and OLED
- Opal router polling — WAN traffic rate every 15s
- Auto Boost — fan on when net rate exceeds threshold
- Peak-hold smoothing — 3-tick window
- DS18B20 warmup — no temp=0.0 on first tick
- HTTP API: /, /status, /config, /time, /log.csv, /serial, /serial-raw, /ota, /reboot
- Log schema: timestamp,temp_c,net_kbps,boost,fan,rpm,event
- Log events: SLEEP, WAKE, POWERON, SOFTWARE, PANIC, WDT, BROWNOUT, OTA, REBOOT, LOG_FULL
- OTA updates — 1 MB in ~5s over WiFi

### GUI

- Live telemetry every 10s
- Weather card (Atkinsons Dam via Open-Meteo)
- Temperature and network-rate graphs
- TURBO badge when boost fires
- Settings dialog (Boost / Alarm / Night / Phone)
- Menu: Open Serial Page, Open Dashboard, Dyna Tune (stub), Update Firmware, Toggle Day/Night
- Custom fan icon in dialogs

### Hardware setup

- ESP32-C3 SuperMini with 72x40 OLED
- DS18B20 probe — currently on phone front glass (will relocate to back)
- 4-wire PWM fan — not yet connected
- Hall sensor (A3144) — arriving in post
- Buzzer, LEDs

## Pending work

### Hardware

- Hall sensor arriving — wire to GPIO 1
- Fan arriving — wire to GPIO 7 (PWM) + GPIO 3 (tach)
- Drill mount — relocate probe to back of phone
- Graphite sheet on phone case (optional)

### Software

**v3.44 (next):**
- Dashboard version dynamic
- Serial link in dashboard footer
- host flag + host_last_seen in /status
- GUI: network graph scale 0-2048
- GUI: version in log filenames
- GUI: OTA threading + console logging
- GUI: .bin archive to ~/Documents/FanMate_logs/firmware/

**v3.45+:**
- Sleep state machine
- Sleep countdown
- Adaptive logging
- Mode-based boost
- Kill alarm (3-tier)
- Combined boost + temp curve
- Hourly log rotation
- /logs/* endpoints
- Silent auto-sync
- Reports menu
- Dyna Tune
- Web GUI with 1-hour graph

### Never do

- Do NOT upgrade ESP32 core to 3.x
- Do NOT install arduino-cli 1.x
- Do NOT upgrade to Arduino IDE 2.3+

## Files

| File | Purpose |
|---|---|
| fanmate.ino | Main, setup, loop |
| Config.h | Pins, constants, version |
| Settings.cpp/.h | Config load/save, NVS |
| FanController.cpp/.h | DS18B20, hall, PWM, tach, buzzer |
| DisplayManager.cpp/.h | OLED rendering |
| WiFiManager.cpp/.h | WiFi, mDNS, NTP |
| WebServer.cpp/.h | HTTP endpoints |
| OpalClient.cpp/.h | Router login, WAN traffic poll |
| AutoBoost.cpp/.h | Boost state machine |
| Logging.cpp/.h | Log write, size check |
| fanmate.py | Companion Python GUI |
| secrets.h | Credentials (gitignored) |

## Notes for new chats

1. Read PROJECT.md first
2. Current firmware: fmfw
3. Recent commits: git log --oneline -10
4. Full source: GitHub or git show HEAD:FILE
5. User prefers CLI over IDE
6. User prefers small diffs, not full-file rewrites
