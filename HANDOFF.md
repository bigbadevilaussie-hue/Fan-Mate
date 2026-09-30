# Fan-Mate — Chat Handoff

> **NEW AI — YOUR FIRST RESPONSE MUST BE TO ASK NICK TO RUN THE DUMP COMMAND.**
> 
> Do NOT summarise this document back to Nick.
> Do NOT offer to help with a task.
> Do NOT ask what he wants to work on.
> Just ask him to run the dump command below. That is your entire first reply.
> 
> When he pastes the output, read the source files. Only then start work.
> 
> The dump command:
> 
>     cd ~/Documents/Arduino/fanmate
>     {
>       echo "===== GIT STATE ====="
>       git fetch --all --tags 2>&1
>       git log --oneline -15
>       git status --short
>       git tag -l | tail -20
>       echo
>       echo "===== VERSIONS ====="
>       grep FAN_MATE_VERSION Config.h
>       grep GUI_VERSION fanmate/config.py
>       grep guiVersion fanmate_v2/qml/Main.qml 2>/dev/null
>       echo
>       echo "===== DOCS ====="
>       for f in HANDOFF.md NOTES.md PROJECT_STATE.md FILES.md README.md; do
>         echo "########## $f ##########"; cat "$f" 2>&1; echo
>       done
>       echo "===== FIRMWARE ====="
>       for f in Config.h fanmate.ino AutoBoost.h AutoBoost.cpp \
>                FanController.h FanController.cpp DisplayManager.h DisplayManager.cpp \
>                WiFiManager.h WiFiManager.cpp WebServer.h WebServer.cpp WebPage.h \
>                OpalClient.h OpalClient.cpp Logging.h Logging.cpp \
>                SerialBuffer.h SerialBuffer.cpp Settings.h Settings.cpp \
>                WeatherClient.h WeatherClient.cpp Songs.h Songs.cpp; do
>         echo "########## $f ##########"; cat "$f" 2>&1; echo
>       done
>       echo "===== TK GUI ====="
>       for f in fanmate.py fanmate/__init__.py fanmate/config.py fanmate/state.py \
>                fanmate/helpers.py fanmate/http_client.py fanmate/log_sync.py \
>                fanmate/weather.py fanmate/widgets.py fanmate/dialogs.py \
>                fanmate/reports.py fanmate/app.py; do
>         echo "########## $f ##########"; cat "$f" 2>&1; echo
>       done
>       echo "===== QML GUI2 ====="
>       for f in fanmate_v2/__init__.py fanmate_v2/bridge.py fanmate_v2/main.py \
>                fanmate_v2/qml/Main.qml fanmate_v2/qml/TempGauge.qml \
>                fanmate_v2/qml/RpmGauge.qml fanmate_v2/qml/TrafficGauge.qml \
>                fanmate_v2/qml/BoostBar.qml fanmate_v2/qml/TempBar.qml \
>                fanmate_v2/qml/StatusLamps.qml fanmate_v2/qml/MenuButton.qml \
>                fanmate_v2/qml/OtaDialog.qml fanmate_v2/qml/Bar.qml; do
>         echo "########## $f ##########"; cat "$f" 2>&1; echo
>       done
>       echo "===== LIVE DEVICE ====="
>       curl -s --max-time 5 http://192.168.8.242/status 2>&1 | python3 -m json.tool 2>&1 | head -50
>       curl -s --max-time 5 http://192.168.8.242/config 2>&1 | python3 -m json.tool 2>&1
>       echo "===== LOGS ====="
>       ls -la ~/Documents/FanMate_logs/*.csv 2>/dev/null | tail -5
>     } > ~/Desktop/fanmate-dump.txt 2>&1
>     wc -l ~/Desktop/fanmate-dump.txt
> 
> Naming: GUI = Tk (fanmate/*.py), GUI2 = QML (fanmate_v2/*),
> Web = WebPage.h (needs flash), Firmware = *.cpp/*.h/fanmate.ino.
> 
> Nick's shell is zsh and eats multi-line pastes. Patch via Python
> scripts written to /tmp/ then run with python3. Never paste heredocs
> or # comments directly.

Generated: 2026-09-30 21:37:37

---

## GIT STATE

```
$ git log --oneline -10
500ecb4 docs: NOTES session log to v4.18/GUI2-v1.11; PROJECT_STATE header updated; pending items refreshed
1b12561 gui-v2-v1.11: lamp bars (BoostBar/TempBar) + 4 status lamps + bottom info row; top strip + STATUS removed
98c24fe gui-v2-v1.08: QML room temp wired to bridge (room_c from /status)
cd7ab69 gui-v3.87: SettingsDialog None guard on fetch_config failure
d90a6f4 v4.18: delta guard (phone-room > 5C -> gear 1 + WARN), flat PWM map (gear 1 = 25%), kick-start 400ms
10a2963 v4.17: phonePresent extern shadow fix; Nokia jingle on sleep/wake
55d1ac7 docs: remove FIRST.md (unused)
4dbe9da docs: add FIRST.md — bare command file for new chat opener
69319e4 docs: regenerate handoff
17e75e5 docs: handoff top block inlines dump command, forces first response

$ git status --short
 M HANDOFF.md
 M update_handoff.sh

$ git tag -l | tail -15
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
v4.17
v4.18
```

---

## VERSIONS

```
#define FAN_MATE_VERSION "4.18"
GUI_VERSION = "3.87"
    property string guiVersion: "1.11"
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

### 2026-09-30 — v4.17 → v4.18, GUI2 work begins

**Firmware:**
- v4.17 — `phonePresent` made `extern` in `FanController.cpp` (was `static`, shadowed the global in `fanmate.ino`). Wake path corrected. Nokia jingle moved to sleep/wake transitions.
- v4.18 — **delta guard** added to decision tree: `fanGear = max(tempGear, deltaGear, boostGear)`, delta floor is gear 1 when `phone - room > 5.0` and NTC valid. **Delta alert branch** added: `newLevel = 1` when delta fires and no temp gear active (Tk shows WARNING). **Flat PWM map**: `map(fanGear, 0, 4, 0, 255)` → gear 1 = real 25%, gear 2 = 50%, gear 3 = 75%, gear 4 = 100%. **Kick-start** duration 350 → 400 ms. Verified: 24%/1500 RPM on forced gear 1, full Shakira ramp 0→1→2→3→4 at 60s/step, down-ramp 4→3→2→1 same cadence, cooldown hold engaged and released.

**Priority order confirmed:** heat control (absolute thresholds) > room delta > boost (network rate). Highest demand wins — `max()` of three sources.

**Tk GUI:**
- v3.87 — `SettingsDialog` None guard: if `fetch_config()` returns None, show error and exit gracefully instead of crashing with `TypeError`.

**QML GUI2:**
- v1.08 — room temp wired to bridge (`room_c` from `/status`).
- v1.11 — BoostBar rewritten as 5 separate lamp rectangles (Parked/Cruising/Fast/Racing/Nitro, bottom-to-top, single active lamp in zone colour). New TempBar mirror on right (Normal/Warm/Hot/Hotter/Critical). New StatusLamps row centred above gauges: BOOST / TEMP / OPAL / KILL lamps, small uppercase labels under each. Bottom info row added (OUT / ROOM / TIME / PHONE). Top strip removed. STATUS text removed. Window 900×440.

**Bridge additions in `fanmate_v2/bridge.py`:**
- `roomChanged` / `room` (v1.08)
- `tempLvlChanged` / `tempLvl`
- `killModeChanged` / `killMode`
- `fanStallChanged` / `fanStall`

---

### Lessons from tonight

**QML `Column` + anchors don't mix.** Any child of a `Column` cannot use `anchors.verticalCenter`, `anchors.fill`, `anchors.top`, etc. — Column manages vertical positioning and Qt errors out with `QML Column: Cannot specify top, bottom, verticalCenter, fill or centerIn anchors for items inside Column.` Use `TapHandler` for click handling inside Columns, not `MouseArea`.

**QML `Drawer` for side panels fails when its content needs MouseAreas.** Tried adding BoostPanel/TempPanel as left/right Drawers — reverted. The Drawer's MouseArea needs `anchors.fill`, which is illegal inside Column-managed items. Panel approach on hold.

**macOS Catalina mDNS is slow.** `curl http://fan-mate.local/status` takes ~3–5 seconds to resolve. `curl http://192.168.8.242/status` takes 0.17s. Same host, same LAN. `sudo killall -HUP mDNSResponder` improves it slightly (5.3s → 3.0s) but doesn't fix it. This was causing Tk GUI polls to feel sluggish, and OTA from the GUI to occasionally time out. The GUI was updated to use the IP for the live demo, but `FANMATE_URL` in `fanmate/config.py` and the OTA/reboot URLs in `fanmate_v2/bridge.py` are still `.local` — small pending fixes.

**Hardware is 100% complete.** Fan shroud printed and mounted on Quad Lock adapter. DS18B20 sits inside the Quad Lock socket against the thinnest part of the case back (best available position given the geometry). NTC reads ambient on the board. Phone mounted upside down (antenna toward tower). Fan over the camera bump, which is adjacent to the SoC heat spreader.

**Cooldown hold vs probe position.** Cold temp is captured before boost starts. Cooldown releases when `phone_temp <= cold_temp + 0.3`. In practice the probe lags (thermal mass of case + shroud) so release often happens at the 20-minute timeout rather than the temperature condition. Not a bug — probe physics.

**Version bump rule applies to both.** Any firmware change bumps `FAN_MATE_VERSION` in `Config.h`. Any Tk GUI change bumps `GUI_VERSION` in `fanmate/config.py`. Any QML GUI2 change bumps `guiVersion` in `fanmate_v2/qml/Main.qml`. No exceptions. Previous AIs didn't do this and it caused confusion.

**The kill mode is three actions, not one.** (1) Firmware fires `opal_set_repeater(false)` at Critical — network drops. (2) Human acknowledges by clicking SILENCE on web dashboard → killState → OFF, but repeater stays off. (3) Human manually re-enables repeater on Opal admin, then clicks ARM → killState → AUTO. No auto-recovery at any stage. Intentional.

**Fan fails safe to 100%.** With the ESP32-C3 in bootloader mode (GPIO 9 held low), GPIO 7 is undriven and the fan spins at full speed. If a 10k pull-down were added, it would fail to 0%. Fail-to-100% is the current behaviour and is deliberate — no change planned.

---

## PENDING ITEMS

### Firmware
1. **Thermal runaway failsafe** — sensor health (DS18B20 stale detection, NTC plausibility, rate-of-rise trigger). Designed, not implemented.
2. **Night cap removal** — `FanController.cpp` still caps all fan output at `nightMax` (75%). No UI to change it. `PWM_MIN = 40` in `Config.h` is now unused (flat map doesn't use it) — clean up or leave as documentation.
3. **Temp gear hysteresis for gears 2/3/4** — currently exact-threshold. Only gear 1 entry has hysteresis (`tempGear1 - hysteresis`).
4. **Delta guard hysteresis** — the delta floor (`phone-room > 5`) has no release band. In the 24–29 °C band with no heat/boost active, the fan can hunt (fan on → probe cools → delta drops below 5 → fan off → phone warms → delta > 5 → fan on). Watch the reports; add a release band if it's annoying.
5. **Beep on gear 0→1 during cooldown** — `beep_once` fires on any gear change.
6. **WiFi Nokia trigger** — patch failed (duplicate `_last_connected_state` declaration in `WiFiManager.cpp`). Currently only phone-detect triggers the tune.

### Tk GUI
7. **`FANMATE_URL` still `.local`** — change to `http://192.168.8.242` to bypass the 3–5s Catalina mDNS tax.
8. **Settings "did not work"** — reported after v3.87 None guard. Not diagnosed. Could be: (a) fetch_config returns partial data, (b) Apply doesn't reach device, (c) apply persists but doesn't show. Reproduce and fix.
9. **Report2H `_find_recent_files(2)`** — takes last 2 sealed files by name, not "last 2 hours of coverage". Should walk backwards accumulating files until the cumulative span reaches 2h.
10. **Report2H `missing` heuristic** — `expected = span_min * 60 / 15` assumes one row per 15s. Sleep windows, seal boundaries, and log-paused periods all break this. Shows phantom "missing" rows. Either rewrite to count real inter-row gaps >20s, or drop the metric.

### QML GUI2
11. **Kill banner not in GUI2** — GUI2 shows KILL lamp but no way to SILENCE / ARM. Bridge needs `killSilence()` and `killArm()` slots that POST `/kill/clear` and `/kill/auto`. Add a top-centred Rectangle banner visible when `killMode >= 1`.
12. **Boost / Temp settings panels** — Drawer approach failed (Qt layout rules). Need a different pattern — likely a plain Rectangle with x-animation, or a StackView.
13. **Bridge uses `.local` for OTA and reboot URLs** — same mDNS tax. Change to IP.
14. **BoostBar/TempBar lamp colors** — currently only the active lamp is coloured; the other four are dim grey text. Confirmed design. But `#4a5568` may be a touch dark — consider `#5a6578` for readability.

### Docs
15. **PROJECT_STATE.md stale** — needs top section update (v4.18, HW complete, GUI2 in progress, new priority order).
16. **FILES.md** — doesn't list `StatusLamps.qml`, `TempBar.qml`, `Songs.cpp/h`, `hwtest/hwtest.ino`.
17. **README.md** — check build command and endpoint list are current.
18. **Web dashboard rework — NOT DONE.** The layout Nick asked for (BOOST into PHONE slot, TEMP into STATUS, OUT+PHONE+TIME bottom row, remove title/kill banner/footer) is not applied. Source is `WebPage.h`. Needs compile + flash.

---

## KNOWN FALSE ALARMS

- **Phone +10°C above room** — observed once, transient. Delta settled to +2.6. Not a bug.
- **NTC offset tuning** — +7.0 was picking up board heat, +6.0 correct (verified 25.8 vs 25.81).
- **OPAL login "loop"** — never existed. Normal 4-min SID refresh.
- **"Boost is not working"** — observed mid-ramp. Boost ramps one gear per `on_hold × 15s` tick = 60s per gear. From IDLE to Nitro takes ~4 minutes if rate holds. Not broken, just slow by design.
- **Curtain incident** — sun through the window heated the phone back. Delta crossed 5 with no network activity. This is exactly what the delta guard was built for; it would have fired gear 1 (25%) if it had been in place. Prior to v4.18, fan did nothing. Not a bug — expected behaviour after v4.18.

---

## TESTING CHEATSHEET

Force a boost gear (auto-expires after 30 min, or release with n=0):

    curl "http://192.168.8.242/boost/gear?n=1"
    curl "http://192.168.8.242/boost/gear?n=2"
    curl "http://192.168.8.242/boost/gear?n=3"
    curl "http://192.168.8.242/boost/gear?n=4"
    curl "http://192.168.8.242/boost/gear?n=0"

Kill mode (only test with the phone off the mount or actually overheated):

    curl -X POST "http://192.168.8.242/kill/clear"   # silence
    curl -X POST "http://192.168.8.242/kill/auto"    # re-arm

Live status in one line:

    curl -s http://192.168.8.242/status | python3 -c "import json,sys; d=json.load(sys.stdin); print('temp:',d.get('temp'),'room:',d.get('room_c'),'delta:',round(d.get('temp',0)-d.get('room_c',0),2),'fan:',d.get('fan'),'rpm:',d.get('rpm'),'boost_lvl:',d.get('boost_lvl'),'temp_lvl:',d.get('temp_lvl'),'alert:',d.get('alert'),'kill:',d.get('kill_mode'))"

Serial tail:

    curl -s http://192.168.8.242/serial-raw | tail -30

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
Latest firmware: V4.18 (tag v4.18)
Latest GUI: Tk v3.87 (tag gui-v3.87) — workhorse, primary
Latest GUI2: QML v1.11 (tag gui-v2-v1.11) — in progress, target

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
-rw-r--r--@ 1 Nick  staff   2224 30 Sep 19:30 Config.h
-rw-r--r--@ 1 Nick  staff   5501 27 Sep 18:00 DisplayManager.cpp
-rw-r--r--@ 1 Nick  staff    422 26 Sep 10:16 DisplayManager.h
-rw-r--r--@ 1 Nick  staff  13243 30 Sep 19:30 FanController.cpp
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
-rw-r--r--  1 Nick  staff   5971 30 Sep 18:07 fanmate.ino
-rw-r--r--@ 1 Nick  staff    669 25 Sep 15:31 secrets.example.h
-rw-r--r--@ 1 Nick  staff    770 25 Sep 16:48 secrets.h
```

---

## TK GUI FILES

```
-rw-r--r--@ 1 Nick  staff    162 27 Sep 09:23 fanmate.py
-rw-r--r--  1 Nick  staff     27 27 Sep 09:09 fanmate/__init__.py
-rw-r--r--  1 Nick  staff  14895 30 Sep 16:45 fanmate/app.py
-rw-r--r--  1 Nick  staff   1266 30 Sep 20:04 fanmate/config.py
-rw-r--r--  1 Nick  staff  17801 30 Sep 20:05 fanmate/dialogs.py
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
-rw-r--r--  1 Nick  staff     0 28 Sep 13:37 fanmate_v2/__init__.py
-rw-r--r--  1 Nick  staff  8089 30 Sep 21:29 fanmate_v2/bridge.py
-rw-r--r--  1 Nick  staff  1049 30 Sep 00:45 fanmate_v2/main.py
-rw-r--r--  1 Nick  staff  2012 28 Sep 16:49 fanmate_v2/qml/Bar.qml
-rw-r--r--  1 Nick  staff  1517 30 Sep 20:39 fanmate_v2/qml/BoostBar.qml
-rw-r--r--  1 Nick  staff  4543 29 Sep 20:00 fanmate_v2/qml/BoostGauge.qml
-rw-r--r--  1 Nick  staff  9567 30 Sep 21:29 fanmate_v2/qml/Main.qml
-rw-r--r--  1 Nick  staff   599 30 Sep 00:19 fanmate_v2/qml/MenuButton.qml
-rw-r--r--  1 Nick  staff  6659 30 Sep 01:08 fanmate_v2/qml/OtaDialog.qml
-rw-r--r--  1 Nick  staff  7503 30 Sep 01:01 fanmate_v2/qml/RpmGauge.qml
-rw-r--r--  1 Nick  staff  4639 30 Sep 21:29 fanmate_v2/qml/StatusLamps.qml
-rw-r--r--  1 Nick  staff  1407 30 Sep 20:39 fanmate_v2/qml/TempBar.qml
-rw-r--r--  1 Nick  staff  7481 30 Sep 08:27 fanmate_v2/qml/TempGauge.qml
-rw-r--r--  1 Nick  staff  7521 30 Sep 00:09 fanmate_v2/qml/TrafficGauge.qml
```

---

## LIVE DEVICE

```
{
    "fw": "4.18",
    "uptime": 4430,
    "ip": "192.168.8.242",
    "rssi": -61,
    "ssid": "StarCabin",
    "temp": 21.12,
    "fan": 49,
    "rpm": 3540,
    "phone": 1,
    "alert": 0,
    "fan_stall": 0,
    "boost": 1,
    "boost_lvl": 2,
    "cooling": 0,
    "net_kbps": 34.8,
    "temp_lvl": 0,
    "opal": 1,
    "host": 1,
    "host_last_seen": 0,
    "sleep": 0,
    "sleep_countdown": 0,
    "log_size": 7625,
    "outdoor_c": 15.1,
    "room_c": 20.3,
    "temp_hist": [
        21.5,
        21.5,
        21.5,
        21.5,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.4,
        21.3,
        21.3,
        21.4,
        21.3,
        21.3,
        21.3,
        21.3,
        21.3,
        21.3,
        21.3,
        21.3,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.2,
        21.1,
        21.2,
        21.1,
        21.1,
        21.2
    ],
    "net_hist": [
        47.1,
        231.3,
        231.3,
        231.3,
        32.0,
        38.4,
        38.4,
        38.4,
        34.0,
        34.0,
        32.6,
        32.6,
        30.2,
        30.2,
        29.5,
        32.6,
        40.3,
        40.3,
        40.3,
        30.2,
        30.2,
        30.8,
        51.2,
        51.2,
        51.2,
        30.3,
        30.3,
        31.4,
        31.4,
        31.5,
        31.5,
        31.5,
        30.8,
        32.1,
        32.1,
        34.6,
        34.6,
        34.6,
        31.5,
        36.9,
        36.9,
        37.4,
        37.4,
        37.4,
        34.1,
        34.1,
        34.1,
        32.4,
        29.8,
        29.8,
        27.7,
        30.7,
        30.7,
        31.2,
        31.2,
        36.1,
        36.1,
        36.1,
        34.8,
        34.8
    ],
    "kill_mode": 0,
    "temp_gear1": 30.0,
    "temp_gear2": 32.0,
    "temp_gear3": 34.0,
    "temp_gear4": 36.0,
    "temp_warning": 32.0,
    "temp_panic": 34.0,
    "temp_kill": 36.0,
    "boost_threshold": 700
}
```

---

## LOG FILES ON MAC

```
-rw-r--r--  1 Nick  staff   2228 30 Sep 18:11 /Users/Nick/Documents/FanMate_logs/log-4.16-20260930-1800.csv
-rw-r--r--  1 Nick  staff    512 30 Sep 18:12 /Users/Nick/Documents/FanMate_logs/log-4.16-20260930-1811.csv
-rw-r--r--  1 Nick  staff    932 30 Sep 18:15 /Users/Nick/Documents/FanMate_logs/log-4.16-20260930-1815.csv
-rw-r--r--  1 Nick  staff    340 30 Sep 18:16 /Users/Nick/Documents/FanMate_logs/log-4.16-20260930-1816.csv
-rw-r--r--  1 Nick  staff    698 30 Sep 18:17 /Users/Nick/Documents/FanMate_logs/log-4.17-20260930-1817.csv
-rw-r--r--  1 Nick  staff    797 30 Sep 18:20 /Users/Nick/Documents/FanMate_logs/log-4.17-20260930-1820.csv
-rw-r--r--  1 Nick  staff   1728 30 Sep 18:38 /Users/Nick/Documents/FanMate_logs/log-4.17-20260930-1829.csv
-rw-r--r--  1 Nick  staff   2128 30 Sep 19:00 /Users/Nick/Documents/FanMate_logs/log-4.17-20260930-1849.csv
-rw-r--r--  1 Nick  staff   6663 30 Sep 19:35 /Users/Nick/Documents/FanMate_logs/log-4.18-20260930-1900.csv
-rw-r--r--  1 Nick  staff   5381 30 Sep 20:00 /Users/Nick/Documents/FanMate_logs/log-4.18-20260930-1935.csv
```

