# Fan-Mate — What To Do Next

Last updated: 2026-10-02
Firmware: **v4.24**
Tk GUI: **v3.95**
QML GUI2: **v1.11** (parked)

---

## CURRENT PHASE — MONITOR

Firmware and Tk GUI are frozen. Running under real conditions
for ~7 days before any further work.

**Do NOT start QML port until the monitor week is up.**

See NOTES.md → CURRENT PHASE for details.

---

## WHEN THE MONITOR WEEK IS UP

1. Read the week's reports (Tk GUI → Reports → Daily / Weekly,
   and DynaTune KPI board).
2. Look for anomalies the audit didn't predict. Especially:
   - delta guard flapping on AC or heater transitions
   - cooldown timeout vs early release ratio
   - log rotation edge cases
   - Opal tick stability (should be 15.0s ± 0.1s)
   - sun-through-curtain solar gain
3. If firmware is stable, freeze it.
4. If Tk is stable, freeze it.
5. THEN port to QML — translation only, no redesign.

---

## OPEN FIRMWARE ITEMS

Low priority. Not blocking.

- F7 — seal filename minute-resolution collisions. Multiple sleep
  cycles inside one minute collide. Wake overwrites live file.
- F8 — `/status` SSID and IP not JSON-escaped. Breaks if SSID
  ever contains a quote or backslash.
- F9 — `settings_apply_json` accepts anything. Add validation for
  gear ordering, night ranges, boost mode. Currently a user can
  save `gear3 < gear2` and shadow out gears.
- F10 — legacy NVS fallback maps `temp.kill` into both gear3 and
  gear4. Only bites devices with pre-gear-schema NVS.

---

## OPEN TK ITEMS

None critical. AUDIT.md Priority 3 has cosmetics if bored.

---

## QML WORK (deferred until firmware + Tk frozen)

- Settings panel — Rectangle overlay with NumberAnimation, not
  Drawer (Drawer fought Qt layout rules last attempt)
- Kill banner — SILENCE / ARM buttons, top-centred overlay
- Delta lamp — fifth lamp or repurpose one existing
- Bridge URLs use IP not `.local`

---

## AUDIT

Full list in **AUDIT.md** — 97 findings, ranked by consensus and
severity. 26 closed. Remaining are mostly cosmetic or design
decisions.

**Priority 1 and 2 in AUDIT.md** are the ones worth attention.

---

## PARTITION SCHEME

Each ESP32 project needs its own partition, and the Arduino IDE
only remembers one per board type. Switching between projects
loses the setting.

| Project | Partition | FQBN suffix |
|---|---|---|
| Fan-Mate | Default 4MB (1.2MB APP) | *(none — default)* |
| Bike-Mate | Minimal SPIFFS (1.9MB APP) | `:PartitionScheme=min_spiffs` |

**For Fan-Mate compile:** `esp32:esp32:esp32c3` — default partition,
no suffix needed.

**For Bike-Mate compile:** `esp32:esp32:esp32c3:PartitionScheme=min_spiffs`.

**Never trust the IDE dropdown.** Use arduino-cli with the FQBN above,
or a project-local build.sh.

---

## RULES — DO NOT VIOLATE

- **Version bump on every change.** Firmware → `Config.h`.
  Tk → `fanmate/config.py`. QML → `Main.qml`.
- **Read the file before patching it.** No guessing anchors.
- **One command per paste.** Nick's zsh mangles multi-line
  heredocs and `#` comments.
- **Do not start QML work** until the monitor phase is declared
  complete.
- **Ask before assuming** — if the phase has changed, confirm.

---

## REPO

https://github.com/bigbadevilaussie-hue/Fan-Mate
