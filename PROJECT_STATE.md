# Fan-Mate — Project State

Snapshot date: 2026-10-02
Latest firmware: **V4.24** (tag v4.24)
Latest GUI: Tk **v3.95** (tag gui-v3.95) — workhorse, primary
Latest GUI2: QML **v1.11** (tag gui-v2-v1.11) — parked until monitor phase completes

**Hardware is 100% complete and installed.** Fan shroud printed, mounted on Quad Lock adapter, phone docked, all sensors wired and verified on-bench and in-place.
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
- ESP32-C3 SuperMini — mounted on perfboard in printed enclosure
- External 72x40 SSD1306 OLED
- DS18B20 waterproof probe — inside Quad Lock socket, contacting phone back
- 40mm 4-wire PWM fan — in printed shroud, mounted on Quad Lock adapter
- NTC 10k MF52AT B=3950 thermistor — on board, room reading
- A3144 hall sensor — detecting phone presence via Quad Lock magnet
- Buzzer, LEDs

### Room environment
- Donga, Queensland
- Ambient ~29°C (no A/C running)

### Installed
- Fan shroud printed, mounted on Quad Lock adapter, docked to phone
- Hardware 100% complete — sensors wired, verified on-bench and in-place
- Mount position fixed by RF: 10cm off the spot and mobile drops from 36 to 5 Mbps

---

## PIN MAP (ESP32-C3)

| GPIO | Function | Notes |
|------|----------|-------|
| 0 | Thermistor (NTC) | 10k MF52AT, +6.0 offset |
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

**Current version:** V4.18

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
| Songs.cpp/.h | Nokia jingle on sleep/wake |
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
| V4.11 | Heat thresholds renamed Warm/Hot/Hotter/Critical (30/32/34/36) |
| V4.12 | `boost_lvl` reports `data_gear` (0 during cooldown); `cooling` flag in `/status` |
| V4.13 | NTC room temp: `readNTC()`, `room_get_temp()`, `room_c` in `/status` |
| V4.14 | NTC +6.0 offset (board heat); fan kick-start; interrupt-safe tach |
| V4.15 | Nokia tune on phone detect/disconnect (`Songs.cpp/h`) |
| V4.16 | `phoneMode` removed entirely — always auto-detect via hall sensor |
| V4.17 | `phonePresent` made `extern` in `FanController.cpp` (was `static`, shadowing global); jingle moved to sleep/wake |
| V4.18 | **Delta guard** (`phone-room > 5` → gear 1 floor), delta alert branch, **flat PWM map** (`map(gear, 0, 4, 0, 255)` = real 25/50/75/100), kick-start 400ms |
| V4.20 | `/config` GET valid JSON again (stray `{}` + trailing comma removed since v4.16) |
| V4.21 | Delta guard exit band (5.0→4.0), heat gear hysteresis per gear, cosmetic cleanup |
| V4.22 | NVS boost keys shortened to ≤15 chars — boost config now persists across reboot |
| V4.23 | Web dashboard room card, net graph axis 2048→8192 |
| V4.24 | Rate cap 10 MB/s, log actual gear 0–4 not binary, non-blocking kick-start, kick-start phone gate, log_resume preserves orphan, log_evict_oldest sorts by name |

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
| fanmate/dynatune.py | Six KPI tests for DynaTune |
| fanmate/reports.py | Report2H, ReportDaily, ReportWeekly |
| fanmate/app.py | App class |

### Features
- Live telemetry every 10s (IP-based, bypasses mDNS 3–5s tax)
- Weather card (Atkinsons Dam, Open-Meteo)
- Temperature and network-rate graphs
- Settings dialog (Heat / Boost / Night)
- Reports: Last 2 Hours, Daily, Weekly (room temp overlay)
- DynaTune KPI board (6 tests: boost, cooldown, delta, lag, events, log)
- OTA updates via HTTP multipart
- Log sync via /log/list, /log/file, /log/ack with CRC32 verification
- Day/night theme toggle
- Menu: Settings, Open Serial, Open Dashboard, Reports, DynaTune, Update Firmware, Toggle Day/Night, Quit

---

## WEB DASHBOARD (new in V3.80, current V4.23)

Served directly by the ESP32. Open `http://fan-mate.local/` from iPhone, iPad, iMac.

- Read-only, portrait layout, 420px max-width
- Live refresh every 5s
- Cards: outdoor, room, phone temp, fan/RPM, phone/status, clock, network graph, temperature graph
- Net graph axis 0–8192 KB/s; boost threshold line at config value
- Auto-dims when disconnected

---

## LOG FORMAT

**Schema (v4.24):** `timestamp, temp_c, net_kbps, boost, fan, rpm, event, outdoor_c, room_c`
- `boost` column is now the actual gear (0–4), not binary, since v4.24
- Older files (pre-v4.24) have binary 0/1 in that column

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

**See TODONEXT.md — that's the authoritative current phase doc.**

Summary as of 2026-10-02:

**Current phase: MONITOR.** Firmware v4.24 and Tk v3.95 frozen and running
under real conditions for ~7 days before any further work.

After the monitor week:
1. Read the week's reports
2. Freeze firmware and Tk if stable
3. Then port to QML GUI2 — translation only

**Open firmware items (low priority):**
- F7 seal filename collisions
- F8 `/status` SSID quote escape
- F9 `settings_apply_json` validation
- F10 legacy NVS fallback

**Open Tk items:** none critical.

**QML work:** deferred until firmware + Tk frozen.

**Later / separate project:** Auto-AC via Alexa + Meross.

---

## KNOWN ISSUES

- **No auto-AC yet.** Room hits 30°C, user turns AC on manually.
- **Summer tuning pending.** Thresholds currently fixed (33/35/37/39); will
  need adjustment when ambient climbs. Adaptive (room-relative) thresholds
  designed but not built.
- **Cooling tends to timeout, not release on temp.** `cold_temp` captured
  once per boost; morning captures from overnight cool don't track the
  phone's actual temperature by the time cooldown runs. Known.
- **Five-AI audit:** 97 findings in AUDIT.md. 26 closed. Remaining are
  cosmetic, low-priority, or design decisions.

---

## QUICK REFERENCE

**Build:**
    cd ~/Documents/Arduino/fanmate
    rm -rf build
    arduino-cli compile --fqbn esp32:esp32:esp32c3 --export-binaries .
    # binary: build/esp32.esp32.esp32c3/fanmate.ino.bin
    # Fan-Mate uses the DEFAULT partition.
    # Bike-Mate needs :PartitionScheme=min_spiffs — do not mix.

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
