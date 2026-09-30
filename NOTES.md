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
