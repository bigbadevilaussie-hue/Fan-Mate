# Fan-Mate — Chat Handoff

Generated: 2026-09-30 17:30:17

---

## GIT STATE

```
$ git log --oneline -5
8e96a00 v4.16 / gui-v3.86: phoneMode removed (always auto-detect via hall); Nokia tune; NTC + hall wired and verified
8b6f3c4 tools: add hwtest.ino — fan/NTC/hall verification sketch
d056123 v4.14: NTC +6.0 offset, fan kick-start, interrupt-safe tach; gui-v3.85 room column + footer
b43bce2 v4.13: NTC room temp — readNTC(), room_get_temp() wired, room_c in /status
ec99b06 v4.12 / gui-v3.84: boost_lvl reports data_gear (0 during cooldown), cooling flag in /status; Tk layout rework

$ git status --short
 M HANDOFF.md

$ git tag -l | tail -10
v4.03
v4.05
v4.08
v4.09
v4.10
v4.11
v4.12
v4.13
v4.14
v4.16
```

---

## PROJECT_STATE.md

# Fan-Mate — Project State

Snapshot date: 2026-09-29
Latest firmware: V4.10
Latest firmware tag: v4.10
Latest GUI: Tk v3.80 (tag gui-v3.80) / QML v2 v1.01 (tag gui-v2-v1.01)
Repo: https://github.com/bigbadevilaussie-hue/Fan-Mate

---

## PROJECT PHILOSOPHY

Rule 1 — Have fun
Rule 2 — Over engineer it
Rule 3 — It's useless but looks cool
Rule 4 — Fuck it lmao

---

## HARDWARE

### Current bench
- ESP32-C3 SuperMini
- External 72x40 SSD1306 OLED
- DS18B20 waterproof probe (1m cable, 6mm tube) — currently on phone back
- 40mm 4-wire PWM fan — currently on desk, testing
- NTC 10k MF52AT B=3950 thermistor — **on order, in customs**
- A3144 hall sensor (10 pack) — **on order, in transit**
- Buzzer, LEDs

### Room environment
- Donga, Queensland
- Ambient ~29°C (no A/C running)

### Planned
- 3D printed Quad Lock mount (STL in progress)
- Room temp card on web page once NTC arrives
- Beep reminder when room ≥ 30°C

---

## PIN MAP (ESP32-C3)

| GPIO | Function | Notes |
|------|----------|-------|
| 0 | Thermistor (NTC) | **planned — free** |
| 1 | Hall sensor (phone detect) | A3144, INPUT_PULLUP, LOW = present |
| 2 | (free) | strapping, avoid |
| 3 | Fan tach | INPUT_PULLUP, falling edge IRQ |
| 4 | DS18B20 data | 1-Wire, 4.7k pull-up to 3V3 |
| 5 | OLED SDA | I2C |
| 6 | OLED SCL | I2C |
| 7 | Fan PWM | 25 kHz, 8-bit |
| 8 | Blue LED | onboard, active-LOW |
| 9 | (free) | strapping, avoid |
| 10 | Buzzer | LEDC channel 1, 2 kHz, 8-bit |

---

## FIRMWARE

**Current version:** V4.10

### Modules
| File | Purpose |
|------|---------|
| fanmate.ino | Main, setup, loop, sleep state machine |
| Config.h | Pins, constants, version |
| Settings.cpp/.h | Config load/save, NVS, JSON parse |
| FanController.cpp/.h | DS18B20, hall, PWM, tach, buzzer, stall alarm |
| DisplayManager.cpp/.h | OLED rendering |
| WiFiManager.cpp/.h | WiFi, mDNS, NTP |
| WebServer.cpp/.h | HTTP endpoints |
| OpalClient.cpp/.h | Router login, WAN traffic poll |
| AutoBoost.cpp/.h | Boost state machine with on_hold/off_hold hysteresis |
| Logging.cpp/.h | Log rotation, seal, boot recovery, time-jump guard |
| SerialBuffer.cpp/.h | Ring buffer for /serial web page |
| WeatherClient.cpp/.h | Open-Meteo fetch (cached in NVS) |
| WebPage.h | Embedded responsive HTML dashboard |

### Version history (recent)
| Version | Notes |
|---------|-------|
| V3.46 | Heat control, graduated ramp, gear beeps, weather in log |
| V3.70 | Hourly log rotation, CRC-verified Mac sync, ack/nack |
| V3.71 | AutoBoost hysteresis (on_hold/off_hold), GUI settings redesign |
| V3.72 | NTP loop wired (fixes rotation), fan stall alarm, quiet serial |
| V3.73 | Serial buffer refactor, log event routing, stall gated |
| V3.74 | Fan/boost events through serial buffer, log time-jump recovery |
| V3.80 | Responsive web dashboard, /status history arrays |
| V4.09 | Boost start temp logging on gear 0->1 transition, manual `/boost/gear?n=` force endpoint with 30-min auto-release, DS18B20 moved to loop() for every-pass sampling |
| V4.10 | **Boost overhaul**: rate-based target gears (`floor(rate/threshold)`), 80% down-band hysteresis, cold temp capture, temp-latched cooldown phase (fan holds at gear 1 until phone <= cold + 0.3°C), router-down cooldown runs every tick via `net_ok` flag |

---

## GUI

**Tk GUI** — Python 3.11, MacPorts on Catalina. Split into package.

### Package layout
| File | Purpose |
|------|---------|
| fanmate.py | Launcher (11 lines) |
| fanmate/__init__.py | Package marker |
| fanmate/config.py | Constants, paths |
| fanmate/state.py | Shared mutable state, fonts |
| fanmate/helpers.py | Theme, emoji, version read |
| fanmate/http_client.py | /status polling, config fetch |
| fanmate/log_sync.py | Pull sealed logs from ESP32 |
| fanmate/weather.py | Weather thread |
| fanmate/widgets.py | Card, Graph, ReportPlot |
| fanmate/dialogs.py | SettingsDialog, DynaTune |
| fanmate/reports.py | Report2H, ReportDaily, ReportWeekly |
| fanmate/app.py | App class |

### Features
- Live telemetry every 10s
- Weather card (Atkinsons Dam, Open-Meteo)
- Temperature and network-rate graphs
- TURBO badge when boost active
- Settings dialog (Heat / Boost / Night / Phone)
- Reports: Last 2 Hours, Daily, Weekly
- DynaTune health check (Fan + Turbo scoring)
- OTA updates via HTTP multipart
- Log sync via /log/list, /log/file, /log/ack with CRC32 verification
- Day/night theme toggle
- Menu: Settings, Open Serial, Open Dashboard, Reports, DynaTune, Update Firmware, Toggle Day/Night, Quit

---

## WEB DASHBOARD (new in V3.80, current V4.08)

Served directly by the ESP32. Open `http://fan-mate.local/` from iPhone, iPad, iMac.

- Read-only, portrait layout, 420px max-width
- Live refresh every 5s
- Same cards as Tk GUI: weather, phone temp, fan/RPM, phone/status, clock, network graph, temperature graph
- Threshold lines drawn on graphs (temp warning, boost threshold)
- Auto-dims when disconnected

---

## LOG FORMAT

**Schema (v4.08):**

**Planned v3.81:**

**Rotation:** Hourly. Files named `log-v{X.YY}-YYYYMMDD-HHMM.csv` where HHMM is start of content window.

**Events:** SEAL, BOOT, SOFTWARE, POWERON, PANIC, WDT, BROWNOUT, OTA, REBOOT, SLEEP, WAKE, CLEAR, FAN_STALL, FAN_RECOVERED, UPLOAD

**Sync:** GUI pulls via `/log/list` (name+size+crc32), downloads `/log/file?name=X`, verifies CRC32, saves to `~/Documents/FanMate_logs/`, acks via `/log/ack`. ESP32 deletes on ack.

**Rotation guard:** Boot recovery skips seal if clock isn't synced. Time-jump guard resets start epoch if >24h gap.

---

## HTTP ENDPOINTS

| Endpoint | Method | Purpose |
|----------|--------|---------|
| / | GET | Web dashboard (embedded HTML) |
| /status | GET | JSON telemetry + history arrays |
| /config | GET | Current config JSON |
| /config | POST | Update config |
| /time | POST | Set RTC (epoch) |
| /log.csv | GET | Live log stream |
| /log/info | GET | Log size, sealed count, free bytes, paused |
| /log/list | GET | Sealed file list with CRC32 |
| /log/file?name=X | GET | Stream sealed file |
| /log/ack | POST | Confirm received, delete on device |
| /log/nack | POST | CRC failed, keep on device |
| /log/clear | POST | Wipe live log |
| /serial | GET | HTML serial page |
| /serial-raw | GET | Text serial dump (from ring buffer) |
| /reboot | GET | Restart |
| /ota | POST | Firmware upload |

---

## WHAT'S NEXT

### Firmware (V3.81)
- NTC room temp on GPIO 0 (MF52AT 10k B=3950)
- Beep reminder when room ≥ 30°C
- Web page room temp card
- 9th log column `room_c`
- `FAN_STALL_ENABLED 1` once fan is permanently mounted

### GUI
- Refinements as needed

### Later
- Auto-AC via Alexa + Meross (separate project)
- HANDOFF.md / FILES.md docs (this file is part of that)

---

## KNOWN ISSUES

- **No auto-AC yet.** Room hits 30°C, user turns AC on manually.
- **Fan is on the desk** — not permanently mounted yet.
- **NTC not wired** — on order.
- **Hall sensor not wired** — on order.
- **Mount STL in progress** — Quad Lock plate + vented slab + arm.
- **Probe on phone back** reads phone temp; room temp card waiting on NTC.

---

## QUICK REFERENCE

**Build:**

**OTA:**
GUI menu → 📡 Update Firmware → Y/N prompt

**Device:**
http://fan-mate.local/ (web dashboard)
http://fan-mate.local/status (JSON)
http://fan-mate.local/serial (serial page)

**Logs on Mac:**
~/Documents/FanMate_logs/

**Firmware archive:**
~/Documents/FanMate_logs/firmware/

**Handoff generator:**
./update_handoff.sh && cat HANDOFF.md | pbcopy

---

## REPO

https://github.com/bigbadevilaussie-hue/Fan-Mate

Related: https://github.com/bigbadevilaussie-hue/Bike-Mate

---

## FIRMWARE FILES

```
-rw-r--r--@ 1 Nick  staff   5701 30 Sep 09:46 AutoBoost.cpp
-rw-r--r--@ 1 Nick  staff   1610 30 Sep 09:46 AutoBoost.h
-rw-r--r--@ 1 Nick  staff   2224 30 Sep 16:47 Config.h
-rw-r--r--@ 1 Nick  staff   5501 27 Sep 18:00 DisplayManager.cpp
-rw-r--r--@ 1 Nick  staff    422 26 Sep 10:16 DisplayManager.h
-rw-r--r--@ 1 Nick  staff  12666 30 Sep 16:44 FanController.cpp
-rw-r--r--@ 1 Nick  staff    748 30 Sep 12:46 FanController.h
-rw-r--r--@ 1 Nick  staff  14104 30 Sep 12:46 Logging.cpp
-rw-r--r--@ 1 Nick  staff    647 29 Sep 08:06 Logging.h
-rw-r--r--@ 1 Nick  staff   8513 28 Sep 23:36 OpalClient.cpp
-rw-r--r--@ 1 Nick  staff    343 28 Sep 21:16 OpalClient.h
-rw-r--r--@ 1 Nick  staff    779 26 Sep 22:04 SerialBuffer.cpp
-rw-r--r--@ 1 Nick  staff    170 26 Sep 22:03 SerialBuffer.h
-rw-r--r--@ 1 Nick  staff   6978 30 Sep 16:45 Settings.cpp
-rw-r--r--@ 1 Nick  staff   1266 30 Sep 16:44 Settings.h
-rw-r--r--  1 Nick  staff    734 30 Sep 16:02 Songs.cpp
-rw-r--r--  1 Nick  staff     85 30 Sep 16:02 Songs.h
-rw-r--r--@ 1 Nick  staff   1716 28 Sep 22:42 WeatherClient.cpp
-rw-r--r--@ 1 Nick  staff    185 26 Sep 16:33 WeatherClient.h
-rw-r--r--@ 1 Nick  staff  12499 30 Sep 09:00 WebPage.h
-rw-r--r--@ 1 Nick  staff  15926 30 Sep 16:44 WebServer.cpp
-rw-r--r--@ 1 Nick  staff    142 27 Sep 17:39 WebServer.h
-rw-r--r--@ 1 Nick  staff   3533 30 Sep 16:05 WiFiManager.cpp
-rw-r--r--@ 1 Nick  staff    315 26 Sep 17:54 WiFiManager.h
-rw-r--r--  1 Nick  staff   5910 30 Sep 16:45 fanmate.ino
-rw-r--r--@ 1 Nick  staff    669 25 Sep 15:31 secrets.example.h
-rw-r--r--@ 1 Nick  staff    770 25 Sep 16:48 secrets.h
```

---

## GUI FILES

```
-rw-r--r--@ 1 Nick  staff    162 27 Sep 09:23 fanmate.py
-rw-r--r--  1 Nick  staff     27 27 Sep 09:09 fanmate/__init__.py
-rw-r--r--  1 Nick  staff  14895 30 Sep 16:45 fanmate/app.py
-rw-r--r--  1 Nick  staff   1266 30 Sep 16:47 fanmate/config.py
-rw-r--r--  1 Nick  staff  17630 30 Sep 16:46 fanmate/dialogs.py
-rw-r--r--  1 Nick  staff   2289 29 Sep 07:49 fanmate/helpers.py
-rw-r--r--  1 Nick  staff   3963 30 Sep 12:55 fanmate/http_client.py
-rw-r--r--  1 Nick  staff   2248 27 Sep 10:06 fanmate/log_sync.py
-rw-r--r--  1 Nick  staff  10314 28 Sep 22:21 fanmate/reports.py
-rw-r--r--  1 Nick  staff   1129 30 Sep 16:45 fanmate/state.py
-rw-r--r--  1 Nick  staff   1888 27 Sep 09:19 fanmate/weather.py
-rw-r--r--  1 Nick  staff   6205 27 Sep 09:22 fanmate/widgets.py
```

---

## LIVE DEVICE

```
device unreachable
```

---

## LOG FILES ON MAC

```
-rw-r--r--  1 Nick  staff   9709 30 Sep 09:51 /Users/Nick/Documents/FanMate_logs/log-4.12-20260930-0900.csv
-rw-r--r--  1 Nick  staff   2033 30 Sep 10:00 /Users/Nick/Documents/FanMate_logs/log-4.12-20260930-0950.csv
-rw-r--r--  1 Nick  staff   2503 30 Sep 12:50 /Users/Nick/Documents/FanMate_logs/log-4.13-20260930-1000.csv
-rw-r--r--  1 Nick  staff   2204 30 Sep 13:00 /Users/Nick/Documents/FanMate_logs/log-4.13-20260930-1249.csv
-rw-r--r--  1 Nick  staff   2698 30 Sep 13:13 /Users/Nick/Documents/FanMate_logs/log-4.14-20260930-1300.csv
-rw-r--r--  1 Nick  staff   1861 30 Sep 13:22 /Users/Nick/Documents/FanMate_logs/log-4.14-20260930-1322.csv
-rw-r--r--  1 Nick  staff   4534 30 Sep 16:00 /Users/Nick/Documents/FanMate_logs/log-4.14-20260930-1537.csv
-rw-r--r--  1 Nick  staff   2470 30 Sep 16:12 /Users/Nick/Documents/FanMate_logs/log-4.15-20260930-1600.csv
-rw-r--r--  1 Nick  staff    194 30 Sep 16:27 /Users/Nick/Documents/FanMate_logs/log-4.15-20260930-1614.csv
-rw-r--r--  1 Nick  staff   7672 30 Sep 17:00 /Users/Nick/Documents/FanMate_logs/log-4.16-20260930-1700.csv
```

