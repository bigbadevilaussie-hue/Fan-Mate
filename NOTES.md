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

## DYNATUNE — KPI BOARD (planned, next session)

DynaTune becomes a KPI dashboard, not just a plot viewer. Glance-readable,
minimal prose, car-diagnostics layout.

**Six KPIs, each a column:**

    BOOST       COOLDOWN     DELTA      LAG       EVENTS     LOG
    ●●●●●       ●●●○○        ●○○○○      ●●●●●     ●●●●●      ●●●●●
    PASS        WARN         IDLE       PASS      PASS       PASS
    ramp 4/4    rel 1/3      max 3.2    +1.5°C    0 bad      12/12

Each column has:
- 5-dot indicator (filled = PASS, partial = WARN, empty = IDLE/FAIL)
- Status word (PASS / WARN / FAIL / IDLE)
- Primary metric (short — one value or a ratio)
- Small secondary text

**Metric definitions:**

| KPI | Metric | Notes |
|-----|--------|-------|
| BOOST | `ramp N/4` | Highest gear reached when rate supported gear 3+ |
| COOLDOWN | `rel N/M` | Released-by-temp count / total cooldowns |
| DELTA | `max X.X°` | Peak (phone - room) in window |
| LAG | `+X.X°C` | Largest post-burst temp rise (already implemented) |
| EVENTS | `N bad` | Count of PANIC + WDT + BROWNOUT + FAN_STALL |
| LOG | `N/M` | Seals synced / expected seals (hours in window) |

**Colour rules:** all PASS → green dots. Any WARN → amber. Any FAIL → red.

**Recommendation bar:** shown only when at least one KPI is WARN/FAIL.
One line, imperative. E.g.:

    ⚠  COOLDOWN_MAX_MS 20min → 5min

Blank when all PASS. Board is calm when healthy.

**Graphs:** three plots (NET, FAN, TEMP) still below the board, same as now.

---

## DYNATUNE PHASE 2 — ACTIONABLE (future)

Each WARN/FAIL KPI can carry a machine-readable recommendation. Board
shows Apply / Dismiss buttons next to the recommendation bar.

    ⚠  Cooldown running to timeout 3/3 windows.
       Recommended: COOLDOWN_MAX_MS 20min → 5min
       [ Apply ]  [ Dismiss ]

**Applying** POSTs to `/config`. Requires:
1. Every WARN/FAIL test has a structured recommendation: `{label, apply: {...}}`
2. Configurable parameters must live in NVS, not `#define`. `COOLDOWN_MAX_MS`
   is currently `#define` — needs to move to `Settings.cpp` first.
3. Sanity floors — e.g. don't let COOLDOWN_MAX_MS go below 2 min.
4. Undo — store previous value, offer Revert in the same UI slot.

Do NOT build Phase 2 until the six KPI tests have run for several days
and their PASS/WARN/FAIL behaviour is trusted.

---

## ROADMAP — firmware & Tk stabilisation, then QML

**Rule:** No QML work until firmware and Tk are frozen. QML ports
frozen behaviour; it does not chase moving targets.

### Session 1 — Firmware v4.24

High impact:
1. Log actual gear 0-4 in boost column, not binary 0/1
2. Cap Opal rate at 10240 KB/s in tick_15s to reject tick-stretch artefacts
3. Kick-start: non-blocking state machine, no delay(400) in loop
4. Kick-start: gate on phonePresent so phone-absent doesn't pulse the fan

Medium — data loss:
5. log_resume: don't overwrite if pre-sleep seal failed
6. log_evict_oldest: sort by filename before deleting
7. Seal filename collisions: append counter if name exists

Lower:
8. /status: escape SSID and IP quotes in JSON
9. settings_apply_json: validate gear ordering, night range, boost mode
10. Settings.cpp legacy fallback: don't map temp.kill into both gear3 and gear4

Not doing:
- Kill repeater re-enable (deliberate)
- Night cap removal (feature decision)
- Panic/kill quiet hours (arguable)

### Session 2 — Tk GUI v3.92

1. Settings dialog: move fetch_config to background thread
2. fetch_config refresh every 5 min (not just on connect)
3. Remove retired alarm/phone sections from fetch_config
4. _find_files_since: use newest file timestamp, not Mac clock
5. Report window: manual Refresh button
6. is_night_now: read from latest_config, not hardcoded 22/7
7. DynaTune cooldown KPI: leave as-is (log limitation)

### Session 3+ — stabilise

Run for a week. Watch reports. Fix what breaks.

### Session 4 (later) — QML GUI2 v1.12

Only after firmware and Tk are frozen:
1. Settings panel (Rectangle overlay, not Drawer)
2. Kill banner (SILENCE/ARM)
3. Delta lamp
4. Bridge URLs use IP not .local

---

## NEXT SESSION PLAN

**Priority:** fix Tk GUI Settings, then port the fixed Settings to GUI2.

**Step 1 — Tk Settings.**
Reported as "settings did not work" after v3.87 None guard was added.
Candidates, in order:
1. `fetch_config()` returns partial dict → dialog renders with defaults but Apply sends them back unchanged
2. `apply()` POSTs to `/config` but request fails silently (mDNS timeout, busy WebServer)
3. POST succeeds but the change doesn't persist in NVS, or persists but the dialog re-fetches stale values

Reproduce: open Tk GUI, open Settings, note values, change one field, click Apply, curl `http://192.168.8.242/config` and compare.

**Step 2 — Port to GUI2.**
Once Tk Settings works, mirror the same interaction in QML.
Previous attempt failed (see Lessons from tonight). Do NOT use Drawer.
Better patterns to try:
- Rectangle overlay with NumberAnimation on x, anchored to the left or right edge
- StackView with slide transition
- Second page inside the existing Drawer menu

The QML column-with-anchors rule still applies: no `anchors.fill`, `anchors.verticalCenter`, etc. on children of a Column. Use `TapHandler` for click handling.

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
