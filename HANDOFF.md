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
> 
> Partition: Fan-Mate uses the DEFAULT partition (no FQBN suffix).
> Bike-Mate uses :PartitionScheme=min_spiffs. Do not mix them up.

Generated: 2026-10-06 14:42:08

---

## GIT STATE

```
$ git log --oneline -10
76ea94e docs: v4.28 handoff -- partition scheme corrected, version history through v4.28, [STORAGE] noted
79b01bc v4.28: [STORAGE] line on seal -- LittleFS percent used, KB, sealed count
e641d20 v4.28: network resilience -- Opal timeout cap, RSSI floor, WebServer priority
3212013 v4.27: silence beeps for gear 0-1, alert level 1, and all returns to zero; beep only on 2+ to 2+ transitions
f90f5a1 v4.26: /status temp_lvl reads heat_get_gear() — display now matches fan decision
1ef22e0 v4.25: Drive upload — sealed logs POST to Apps Script on seal, 302 treated as success
bd23182 docs: regenerate handoff with updated README/FILES/PROJECT_STATE
1f4b9f7 docs: README, FILES, PROJECT_STATE updated to v4.24 / gui-v3.95
9398bf0 docs: partition scheme note in TODONEXT and handoff top block
a376c51 docs: regenerate handoff

$ git status --short
 M HANDOFF.md

$ git tag -l | tail -15
v4.12
v4.13
v4.14
v4.16
v4.17
v4.18
v4.20
v4.21
v4.22
v4.23
v4.24
v4.25
v4.26
v4.27
v4.28
```

---

## VERSIONS

```
#define FAN_MATE_VERSION "4.28"
GUI_VERSION = "3.95"
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

### 2026-10-01/02 — v4.18 → v4.24, Tk v3.87 → v3.95, five-AI audit

**Five-AI desk check.** Gemini, ChatGPT, Copilot, Claude, Mistral all read the
same dump. Consolidated into AUDIT.md — 97 findings, ranked by severity and
consensus. Claude and Mistral found the deepest items (NVS key length, log_resume
truncation, DS18B20 85°C gap). All reports preserved in the audit doc as
attributions.

**Firmware v4.19 → v4.24:**
- v4.20 — `/config` GET was returning invalid JSON since v4.16 (stray `{}` and
  trailing comma after the night block). Fixed. This was why the Tk Settings
  dialog kept failing with "Device unreachable".
- v4.21 — delta guard exit band (5.0→4.0), heat gear exit band per gear,
  cosmetic cleanup (dead `Config.h` macros removed, stale comments fixed,
  unused vars removed)
- v4.22 — NVS boost keys shortened to fit 15-char limit. This was silent data
  loss — six keys 18-22 chars, `putInt`/`getInt` silently failed both
  directions, boost config reverted to defaults on every reboot. Fixed.
- v4.23 — WebPage.h room temp card, net graph axis 2048→8192
- v4.24 — Opal rate cap at 10240 KB/s (kills 4.7 GB/s phantom from
  tick-stretch), log writes actual gear 0-4 not binary, kick-start
  non-blocking + phone gate, log_resume preserves orphan, log_evict_oldest
  sorts by name

**Tk GUI v3.87 → v3.95:**
- v3.88 — FANMATE_URL uses IP not mDNS (Catalina resolves .local in 3-5s)
- v3.89 — KPI board (six tests, dynatune.py module)
- v3.90 — version drift correction (code said 3.87 while gui-v3.89 tag existed)
- v3.91 — DynaTune fixes (7): boost clamp, thresholds, cooldown signature,
  delta exit band, events include KILL, log seals exclude sleep, lag uses
  timestamps. GUI robustness (5): tick try/except, level clamps, temp_graph
  trigger, settings labels, Apply-wait-for-response. Reports fixes (2):
  _find_files_since span walk, missing heuristic uses real gaps
- v3.92 — SettingsDialog fetches config off main thread (no 10s freeze)
- v3.93 — retired alarm/phone sections removed; is_night_now reads device config
- v3.94 — periodic config refresh (5 min); report timestamp cutoff uses
  newest file not Mac clock; Refresh button on report windows
- v3.95 — version string catch-up (was stuck at 3.90 through four commits)

**Five-AI audit findings fixed:** 25 of 97. Remaining are logged in AUDIT.md.
The highest remaining priorities are firmware (log sealing edge cases, /status
escaping, settings validation) and reports (DynaTune cooldown KPI needs
firmware log change to be accurate).

**Rule learned (again):** version bump is part of every patch. Multiple commits
this session skipped the GUI_VERSION bump. Handoff and tags got out of sync
with what the code reported.

**Rule learned:** QML work deferred until firmware and Tk are frozen. QML ports
frozen behaviour; it does not chase moving targets.

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


### 2026-10-05/06 — v4.25 → v4.28, Opal 2.4 GHz investigation, power outage

**Firmware v4.25 → v4.28:**
- v4.25 — Drive upload: sealed logs POST to Apps Script on seal. HTTP 302
  treated as success (Apps Script redirect pattern). `[DRIVE] name OK http=302`
- v4.26 — `/status` `temp_lvl` reads `heat_get_gear()` instead of recomputing,
  so the display matches the fan decision exactly
- v4.27 — Beep gate: `beep_once()` only fires when `fanGear >= 2 && lastFanGear >= 2`.
  Gear 0-1, alert level 1, and all returns to zero are silent. Kills the
  every-transition beep.
- v4.28 — Network resilience:
  - `OPAL_HTTP_TIMEOUT_MS 400` — Opal RPC cap (was 3000ms)
  - `OPAL_RSSI_FLOOR -70` — skip Opal poll entirely below this RSSI
  - `server_loop()` moved to top of `loop()` — HTTP serviced before anything blocking
  - `NTP_SYNC_COOLDOWN_MS 60000` — throttle NTP re-syncs
  - `[STORAGE]` line on seal — LittleFS % used, KB, sealed count

**The Opal 2.4 GHz story.** A power outage took out the Opal. When it came back,
its 2.4 GHz radio was in a broken state: `handle_probe_req: send failed`
firing multiple times per second, `radar set region 1` (US regulatory domain
instead of AU). RSSI to the ESP32 dropped from -56 to -68/-71. The ESP32's
WebServer hung — HTTP timed out, OLED lagged, but ping still replied and the
thermal path kept running. Root cause: single-radio repeater mode. The Opal's
2.4 GHz chip has to time-slice between STA uplink (Nick hotspot on ch 6) and
AP broadcast (StarCabin). When the STA retries storm, the AP can't answer
probes. ESP32 starves on blocked network calls in `loop()`.

**The v4.28 fix.** Caps Opal RPC at 400ms, skips it entirely below -70 RSSI,
and services HTTP first in `loop()`. Under the same conditions now, the ESP
stays reachable even when the Opal link is bad. Verified: device survived
another Opal restart mid-session without hanging.

**Power outage 12:02.** Woke to dead AC. ESP32 logged through it — sealed 510
rows of pre-outage data on next boot, uploaded to Drive (302), Mac synced.
Boot recovery + Drive upload + Mac sync all confirmed working under worst case.

**Docs were backwards.** Handoff said "Fan-Mate uses the DEFAULT partition,
Bike-Mate uses min_spiffs". Reality is the opposite. Fixed in this pass.

**Lessons:**
- `str.replace("#endif", ...)` on a header file will hit the FIRST `#endif`,
  which in `Config.h` is the secrets.h `#else` close. Constants landed inside
  the `#else` branch. Anchor with the surrounding context, not the bare token.
- zsh eats `#` lines even inside a heredoc paste if they're at column 0. Keep
  Python scripts on one line or wrap them in `cat > /tmp/x.py <<'EOF'` and
  make sure no Python `#` comment starts at column 0 of the pasted block.
- `server.handleClient()` doesn't work in `fanmate.ino` — `server` is `static`
  inside `WebServer.cpp`. Must call the exposed `server_loop()` wrapper.
- `WiFi.RSSI()` returns 0 when disconnected, so `0 < -70` is false — the RSSI
  floor doesn't fire on a dropped link. v4.28.1 candidate.

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

---

## PROJECT_STATE.md

# Fan-Mate — Project State

Snapshot date: 2026-10-06
Latest firmware: **V4.28** (tag v4.28)
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

**Current version:** V4.28

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
| V4.25 | Drive upload: sealed logs POST to Apps Script on seal, HTTP 302 treated as success |
| V4.26 | `/status` temp_lvl reads `heat_get_gear()` — display now matches the fan decision |
| V4.27 | Beep gate: only 2+ to 2+ gear transitions beep; gear 0-1, alert level 1, and returns to zero silenced |
| V4.28 | Network resilience: Opal HTTP timeout cap 400ms, RSSI floor -70 (skip Opal poll below), `server_loop()` at top of loop(), NTP re-sync throttle. `[STORAGE]` line on seal — LittleFS % used, KB, sealed count |

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

**Serial-only (not in CSV):** `[STORAGE] %u%% used (%u/%u KB, %u sealed)` — emitted on every seal since v4.28

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
    arduino-cli compile --fqbn esp32:esp32:esp32c3:PartitionScheme=min_spiffs --export-binaries .
    # binary: build/esp32.esp32.esp32c3/fanmate.ino.bin
    # Fan-Mate uses :PartitionScheme=min_spiffs (1408KB LittleFS).
    # Bike-Mate uses the DEFAULT partition — do not mix.

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
-rw-r--r--@ 1 Nick  staff   2065  6 Oct 14:20 Config.h
-rw-r--r--@ 1 Nick  staff   5501 27 Sep 18:00 DisplayManager.cpp
-rw-r--r--@ 1 Nick  staff    422 26 Sep 10:16 DisplayManager.h
-rw-r--r--@ 1 Nick  staff  14553  2 Oct 12:21 FanController.cpp
-rw-r--r--@ 1 Nick  staff    829  2 Oct 11:23 FanController.h
-rw-r--r--@ 1 Nick  staff  17550  6 Oct 14:30 Logging.cpp
-rw-r--r--@ 1 Nick  staff    647 29 Sep 08:06 Logging.h
-rw-r--r--@ 1 Nick  staff   8466  6 Oct 14:20 OpalClient.cpp
-rw-r--r--@ 1 Nick  staff    343 28 Sep 21:16 OpalClient.h
-rw-r--r--@ 1 Nick  staff    779 26 Sep 22:04 SerialBuffer.cpp
-rw-r--r--@ 1 Nick  staff    170 26 Sep 22:03 SerialBuffer.h
-rw-r--r--@ 1 Nick  staff   6800  1 Oct 10:04 Settings.cpp
-rw-r--r--@ 1 Nick  staff   1254  1 Oct 09:28 Settings.h
-rw-r--r--  1 Nick  staff    734 30 Sep 16:02 Songs.cpp
-rw-r--r--  1 Nick  staff     85 30 Sep 16:02 Songs.h
-rw-r--r--@ 1 Nick  staff   1716 28 Sep 22:42 WeatherClient.cpp
-rw-r--r--@ 1 Nick  staff    185 26 Sep 16:33 WeatherClient.h
-rw-r--r--@ 1 Nick  staff  12801  2 Oct 08:54 WebPage.h
-rw-r--r--@ 1 Nick  staff  15735  2 Oct 11:23 WebServer.cpp
-rw-r--r--@ 1 Nick  staff    142 27 Sep 17:39 WebServer.h
-rw-r--r--@ 1 Nick  staff   3533  1 Oct 09:28 WiFiManager.cpp
-rw-r--r--@ 1 Nick  staff    315 26 Sep 17:54 WiFiManager.h
-rw-r--r--  1 Nick  staff   6024  6 Oct 14:29 fanmate.ino
-rw-r--r--@ 1 Nick  staff    872  2 Oct 11:07 secrets.example.h
-rw-r--r--@ 1 Nick  staff    907  2 Oct 11:09 secrets.h
```

---

## TK GUI FILES

```
-rw-r--r--@ 1 Nick  staff    162 27 Sep 09:23 fanmate.py
-rw-r--r--  1 Nick  staff     27 27 Sep 09:09 fanmate/__init__.py
-rw-r--r--@ 1 Nick  staff  15101  2 Oct 09:31 fanmate/app.py
-rw-r--r--  1 Nick  staff   1265  2 Oct 10:12 fanmate/config.py
-rw-r--r--@ 1 Nick  staff  19519  2 Oct 10:03 fanmate/dialogs.py
-rw-r--r--  1 Nick  staff   8602  2 Oct 09:34 fanmate/dynatune.py
-rw-r--r--  1 Nick  staff   2437  2 Oct 10:06 fanmate/helpers.py
-rw-r--r--  1 Nick  staff   4173  2 Oct 10:08 fanmate/http_client.py
-rw-r--r--  1 Nick  staff   2248 27 Sep 10:06 fanmate/log_sync.py
-rw-r--r--  1 Nick  staff  13212  2 Oct 10:08 fanmate/reports.py
-rw-r--r--  1 Nick  staff   1129 30 Sep 16:45 fanmate/state.py
-rw-r--r--  1 Nick  staff   1888 27 Sep 09:19 fanmate/weather.py
-rw-r--r--  1 Nick  staff   7134  1 Oct 07:17 fanmate/widgets.py
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
    "fw": "4.28",
    "uptime": 463,
    "ip": "192.168.8.242",
    "rssi": -65,
    "ssid": "StarCabin",
    "temp": 30.31,
    "fan": 0,
    "rpm": 0,
    "phone": 1,
    "alert": 0,
    "fan_stall": 0,
    "boost": 0,
    "boost_lvl": 0,
    "cooling": 0,
    "net_kbps": 11.0,
    "temp_lvl": 0,
    "opal": 1,
    "host": 1,
    "host_last_seen": 0,
    "sleep": 0,
    "sleep_countdown": 0,
    "log_size": 1686,
    "outdoor_c": 24.7,
    "room_c": 26.0,
    "temp_hist": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.4,
        30.4,
        30.4,
        30.4,
        30.4,
        30.4,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3,
        30.3
    ],
    "net_hist": [
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        16.0,
        16.0,
        16.0,
        13.3,
        13.3,
        13.3,
        12.4,
        9.6,
        11.4,
        11.9,
        11.9,
        11.9,
        15.1,
        16.5,
        16.5,
        16.5,
        15.0,
        15.0,
        15.6,
        15.6,
        21.4,
        21.4,
        21.4,
        18.8,
        9.5,
        12.3,
        12.3,
        12.3,
        11.0
    ],
    "kill_mode": 0,
    "temp_gear1": 33.0,
    "temp_gear2": 35.0,
    "temp_gear3": 37.0,
    "temp_gear4": 39.0,
    "temp_warning": 35.0,
    "temp_panic": 37.0,
    "temp_kill": 39.0,
    "boost_threshold": 900
}
```

---

## LOG FILES ON MAC

```
-rw-r--r--  1 Nick  staff  11560  6 Oct 03:23 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0200.csv
-rw-r--r--  1 Nick  staff  11561  6 Oct 05:54 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0300.csv
-rw-r--r--  1 Nick  staff  11429  6 Oct 05:54 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0400.csv
-rw-r--r--  1 Nick  staff  11586  6 Oct 07:06 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0500.csv
-rw-r--r--  1 Nick  staff  11576  6 Oct 07:06 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0600.csv
-rw-r--r--  1 Nick  staff  11632  6 Oct 08:00 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0700.csv
-rw-r--r--  1 Nick  staff  12246  6 Oct 12:42 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-0800.csv
-rw-r--r--  1 Nick  staff   4048  6 Oct 13:00 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-1241.csv
-rw-r--r--  1 Nick  staff  12539  6 Oct 14:00 /Users/Nick/Documents/FanMate_logs/log-4.27-20261006-1300.csv
-rw-r--r--  1 Nick  staff   6821  6 Oct 14:34 /Users/Nick/Documents/FanMate_logs/log-4.28-20261006-1400.csv
```

