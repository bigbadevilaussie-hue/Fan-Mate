# Fan-Mate — Chat Handoff

> **NEW AI — DO THIS FIRST.**
> 
> Do not summarise this document back to Nick.
> Do not offer to help with a task yet.
> 
> Read the "GETTING THE NEXT AI UP TO SPEED" section in NOTES.md (below).
> Ask Nick to run the dump command it contains. He will paste the output.
> Read the source files. Only then start work.
> 
> Naming: GUI = Tk (fanmate/*.py), GUI2 = QML (fanmate_v2/*),
> Web = WebPage.h (needs flash), Firmware = *.cpp/*.h/fanmate.ino.
> 
> Nick's shell is zsh and eats multi-line pastes. Patch via Python
> scripts written to /tmp/ then run with python3. Never paste heredocs
> or # comments directly.

Generated: 2026-09-30 17:41:00

---

## GIT STATE

```
$ git log --oneline -10
0f86673 docs: regenerate handoff
ab39347 docs: add NOTES.md, rewrite update_handoff.sh (no pbcopy)
2ec541c docs: regenerate handoff at v4.16 / gui-v3.86
8e96a00 v4.16 / gui-v3.86: phoneMode removed (always auto-detect via hall); Nokia tune; NTC + hall wired and verified
8b6f3c4 tools: add hwtest.ino — fan/NTC/hall verification sketch
d056123 v4.14: NTC +6.0 offset, fan kick-start, interrupt-safe tach; gui-v3.85 room column + footer
b43bce2 v4.13: NTC room temp — readNTC(), room_get_temp() wired, room_c in /status
ec99b06 v4.12 / gui-v3.84: boost_lvl reports data_gear (0 during cooldown), cooling flag in /status; Tk layout rework
3328c38 v4.11 / gui-v3.82 / gui-v2-v1.07: heat control renamed to four gear thresholds (Warm/Hot/Hotter/Critical)
c3d05c0 docs: overhaul notes for v4.10 boost rewrite

$ git status --short
 M HANDOFF.md
 M update_handoff.sh

$ git tag -l | tail -15
v3.94
v3.95
v4.00-firmware
v4.01
v4.02
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

## VERSIONS

```
#define FAN_MATE_VERSION "4.16"
GUI_VERSION = "3.86"
    property string guiVersion: "1.07"
            text: "GUI v" + root.guiVersion + "  ·  FW " + dev.fw
```

---

## NOTES.md

# Fan-Mate — Notes

Everything that isn't in PROJECT_STATE.md or README.md. Session logs,
working rules, gotchas, environment details.

---

## NAMING CONVENTION — READ THIS FIRST

When Nick says:

| Term | Means | Source |
|------|-------|--------|
| **GUI** | Tk GUI, runs on Mac | `fanmate/*.py` |
| **GUI2** | QML GUI v2, runs on Mac | `fanmate_v2/*` |
| **Web** | Web dashboard served by ESP32 | `WebPage.h` (needs compile + flash) |
| **Firmware** | ESP32 code | `*.cpp` / `*.h` / `fanmate.ino` |

Do not guess. If Nick says "GUI" he means the Tk package.

---

## WORKING WITH NICK'S SHELL — CRITICAL

Nick's zsh is broken for multi-line edits. Do NOT:

- Use `cat > file <<'EOF' ... EOF` heredocs for anything long
- Paste blocks with `#` comment lines — zsh treats them as commands
- Paste anything longer than ~10 lines directly to the prompt
- Use `echo` with backslashes or special characters
- Assume `$(...)` expands correctly in a paste

ALWAYS do this instead:

1. Write the patch as a **Python script to `/tmp/`**
2. Run `python3 /tmp/patch.py`
3. Python does all file edits

Pattern that works:

    cat > /tmp/patch.py <<'PYEOF'
    p = "filename"
    s = open(p).read()
    s = s.replace("old", "new")
    open(p, "w").write(s)
    print("done")
    PYEOF
    python3 /tmp/patch.py

The heredoc only works because it's short and has no `#`.
For longer scripts, split into multiple short pastes or have Nick
paste the file into Sublime and save.

NEVER edit files by pasting shell commands directly. Always via Python script file.

---

## ENVIRONMENT

- **Shell:** zsh (mangled multi-line pastes, comments become commands)
- **Python:** `/opt/local/bin/python3.11` (MacPorts, Catalina)
- **QML GUI venv:** `~/fanmate-venv-test/bin/activate` (PySide6 6.4.3, last version supporting Catalina)
- **Arduino IDE:** 2.x with esp32 core **2.0.17** — do NOT upgrade to 3.x
- **arduino-cli:** `arduino-cli` if in PATH, else bundled at `/Applications/Arduino.app/Contents/Resources/app/lib/backend/resources/arduino-cli`
- **Compile:** `arduino-cli compile --fqbn esp32:esp32:esp32c3 --export-binaries .`
- **Binary:** `build/esp32.esp32.esp32c3/fanmate.ino.bin`
- **OTA:** Tk GUI → menu → 📡 Update Firmware → Y/N
- **Repo:** `/Users/Nick/Documents/Arduino/fanmate`
- **Logs:** `~/Documents/FanMate_logs/`
- **Firmware archive:** `~/Documents/FanMate_logs/firmware/`

---

## BEHAVIOUR RULES

- No time-of-day references
- No sleep/rest/break suggestions
- No session-length comments
- No "good morning" / "good evening" openers
- Don't argue about what "the GUI" means — see naming convention
- Read files before patching. Never guess anchors or regex.
- If a patch fails, paste the actual file and rewrite against that.
- Short answers. Code first, explanation second.

---

## SESSION LOG

### 2026-09-30 — v4.10 → v4.16

**Firmware:**
- v4.10 — AutoBoost rewrite: three-phase state machine (IDLE/RUNNING/COOLDOWN), rate-based gears `floor(net/thr)`, cold_temp capture on 0→1, temp-latched cooldown hold, 80% down-band hysteresis
- v4.11 — Four heat thresholds renamed Warm/Hot/Hotter/Critical (30/32/34/36), `/config` and `/status` use `temp_gear1..4`
- v4.12 — `boost_lvl` reports `data_gear` (0 during cooldown), `cooling` flag in `/status`
- v4.13 — NTC room temp wired: `readNTC()`, `room_get_temp()`, `room_c` in `/status`
- v4.14 — NTC +6.0 offset (board heat), fan kick-start (`ledcWrite(2,200)` for 350ms), interrupt-safe tach
- v4.15 — Nokia tune on phone detect/disconnect (`Songs.cpp/h`), `phone_absent_since` reset on `mode=auto`
- v4.16 — `phoneMode` removed entirely, always auto-detect via hall sensor

**Tk GUI:**
- v3.84 — Layout rework: FAN/RPM, BOOST/TEMP level names, OUT/ROOM/PHONE/TIME bottom row
- v3.85 — ROOM column added, footer shows `GUI · FW` (no HTTP text)
- v3.86 — phoneMode setting removed from Settings dialog

**Hardware wired and verified:**
- NTC MF52AT 10k on GPIO 0, 10k pull-up to 3V3, +6.0 offset applied
- A3144 hall sensor on GPIO 1, VCC 5V VBUS, 10k pull-up to 3V3, south pole triggers, flat face toward magnet
- DS18B20 on GPIO 4
- Fan on GPIO 7 (PWM), GPIO 3 (tach)

**Verified:**
- Shakira 4K test — full boost ramp 0→1→2→3, down-ramp 3→2→1→0, cooldown released instantly (fan overcooled phone below cold_temp + 0.3)
- Gear 4 / Nitro did NOT fire — YouTube ABR bursty, not sustained. Torrent test pending.
- Level names track correctly (Cruising → Fast → Racing)
- Nokia tune plays on phone detect/disconnect

---

## PENDING ITEMS

1. **Thermal runaway failsafe** — sensor health (DS18B20 stale detection, NTC plausibility, rate-of-rise trigger). Designed, not implemented.
2. **Night cap removal** — `FanController.cpp` still caps all fan output at `nightMax` (75%). No UI to change it.
3. **Temp gear hysteresis for gears 2/3/4** — currently exact-threshold. Only gear 1 entry has hysteresis (`tempGear1 - hysteresis`).
4. **Kill repeater restore** — kill fires `opal_set_repeater(false)`, no code path turns it back on.
5. **Beep on gear 0→1 during cooldown** — `beep_once` fires on any gear change.
6. **WiFi Nokia trigger** — patch failed (duplicate `_last_connected_state` declaration in `WiFiManager.cpp`). Currently only phone-detect triggers the tune.
7. **Docs stale** — `FILES.md`, `PROJECT_STATE.md`, `README.md` stop at v4.10.

**Web dashboard rework — NOT DONE.** The layout Nick asked for (BOOST into PHONE slot, TEMP into STATUS, OUT+PHONE+TIME bottom row, remove title/kill banner/footer) is not applied. Source is `WebPage.h`. Needs compile + flash.

---

## KNOWN FALSE ALARMS

- **Phone +10°C above room** — observed once, was transient. Delta settled to +2.6. Not a bug.
- **NTC offset tuning** — +7.0 was picking up board heat, +6.0 correct (verified 25.8 vs 25.81)
- **OPAL login "loop"** — never existed. Normal 4-min SID refresh. Diagnostics confirmed `t=10848` set once, `diff` grows 15s/poll, relogin only at 240s.

---

## GETTING THE NEXT AI UP TO SPEED

If you are a new AI picking this up, ask Nick to run this command and paste the output:

    cd ~/Documents/Arduino/fanmate
    {
      echo "===== GIT STATE ====="
      git fetch --all --tags 2>&1
      git log --oneline -15
      git status --short
      git branch -vv
      git tag -l | tail -20
      echo
      echo "===== VERSIONS ====="
      grep "FAN_MATE_VERSION" Config.h
      grep "GUI_VERSION" fanmate/config.py
      grep "guiVersion" fanmate_v2/qml/Main.qml 2>/dev/null
      echo
      echo "===== DOCS ====="
      for f in HANDOFF.md NOTES.md PROJECT_STATE.md FILES.md README.md; do
        echo "########## $f ##########"; cat "$f" 2>&1; echo
      done
      echo "===== FIRMWARE ====="
      for f in Config.h fanmate.ino AutoBoost.h AutoBoost.cpp \
               FanController.h FanController.cpp DisplayManager.h DisplayManager.cpp \
               WiFiManager.h WiFiManager.cpp WebServer.h WebServer.cpp WebPage.h \
               OpalClient.h OpalClient.cpp Logging.h Logging.cpp \
               SerialBuffer.h SerialBuffer.cpp Settings.h Settings.cpp \
               WeatherClient.h WeatherClient.cpp Songs.h Songs.cpp; do
        echo "########## $f ##########"; cat "$f" 2>&1; echo
      done
      echo "===== TK GUI ====="
      for f in fanmate.py fanmate/__init__.py fanmate/config.py fanmate/state.py \
               fanmate/helpers.py fanmate/http_client.py fanmate/log_sync.py \
               fanmate/weather.py fanmate/widgets.py fanmate/dialogs.py \
               fanmate/reports.py fanmate/app.py; do
        echo "########## $f ##########"; cat "$f" 2>&1; echo
      done
      echo "===== QML GUI2 ====="
      for f in fanmate_v2/__init__.py fanmate_v2/bridge.py fanmate_v2/main.py \
               fanmate_v2/qml/Main.qml fanmate_v2/qml/TempGauge.qml \
               fanmate_v2/qml/RpmGauge.qml fanmate_v2/qml/TrafficGauge.qml \
               fanmate_v2/qml/BoostBar.qml fanmate_v2/qml/MenuButton.qml \
               fanmate_v2/qml/OtaDialog.qml fanmate_v2/qml/Bar.qml; do
        echo "########## $f ##########"; cat "$f" 2>&1; echo
      done
      echo "===== LIVE DEVICE ====="
      curl -s --max-time 5 http://fan-mate.local/status 2>&1 | python3 -m json.tool 2>&1 | head -50
      curl -s --max-time 5 http://fan-mate.local/config 2>&1 | python3 -m json.tool 2>&1
      echo "===== LOGS ====="
      ls -la ~/Documents/FanMate_logs/*.csv 2>/dev/null | tail -5
    } > ~/Desktop/fanmate-dump.txt 2>&1

    wc -l ~/Desktop/fanmate-dump.txt

Then read `~/Desktop/fanmate-dump.txt`. That's the complete project state.

---

## REPO

https://github.com/bigbadevilaussie-hue/Fan-Mate

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

## TK GUI FILES

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

## QML GUI2 FILES

```
-rw-r--r--  1 Nick  staff      0 28 Sep 13:37 fanmate_v2/__init__.py
-rw-r--r--  1 Nick  staff   7096 30 Sep 08:27 fanmate_v2/bridge.py
-rw-r--r--  1 Nick  staff   1049 30 Sep 00:45 fanmate_v2/main.py
-rw-r--r--  1 Nick  staff   2012 28 Sep 16:49 fanmate_v2/qml/Bar.qml
-rw-r--r--  1 Nick  staff   2743 30 Sep 00:03 fanmate_v2/qml/BoostBar.qml
-rw-r--r--  1 Nick  staff   4543 29 Sep 20:00 fanmate_v2/qml/BoostGauge.qml
-rw-r--r--  1 Nick  staff  10300 30 Sep 08:32 fanmate_v2/qml/Main.qml
-rw-r--r--  1 Nick  staff    599 30 Sep 00:19 fanmate_v2/qml/MenuButton.qml
-rw-r--r--  1 Nick  staff   6659 30 Sep 01:08 fanmate_v2/qml/OtaDialog.qml
-rw-r--r--  1 Nick  staff   7503 30 Sep 01:01 fanmate_v2/qml/RpmGauge.qml
-rw-r--r--  1 Nick  staff   7481 30 Sep 08:27 fanmate_v2/qml/TempGauge.qml
-rw-r--r--  1 Nick  staff   7521 30 Sep 00:09 fanmate_v2/qml/TrafficGauge.qml
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

