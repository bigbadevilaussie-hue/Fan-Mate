# Fan-Mate — What To Do Next

Last updated: 2026-10-06
Firmware: **v4.30**
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

## v4.30 CANDIDATES

**Primary item: clock from Opal, NTP removed.**

The Opal is the only device that is always on. The iPhone comes and goes. The
ESP32 asks the Opal for time, period. NTP is not demoted, not a fallback,
removed.

Why:
- NTP over the carrier is a trap. UDP 123 gets throttled, blackholed, or
  routed through CGNAT. Worst-case SNTP retry chain is 15-30 s, during
  which the ESP32's radio is held and every other network operation
  queues behind it.
- The self-locking gate: log_rotate_check() returns early if !ntp_synced(),
  and log_boot_recovery() discards rows if time_ok is false. If NTP never
  succeeds, rotation stops and boot recovery loses data.
- The Opal's Date header is a bounded 250 ms HEAD over the LAN. Measured
  from Mac: median 8.7 ms, max 225 ms. Expected from ESP32: median 30-80 ms,
  worst 250 ms. 10-50x faster than NTP, no retry tail, no radio hold.
- Opal has an RTC and NTP-synced clock of its own. Drift is seconds/day.
  For log timestamps that is more than accurate enough.

Scope:

| File | Change |
|---|---|
| WiFiManager.cpp | Remove start_ntp(), ntp_loop(), _ntp_synced_flag. Add clock_sync() -- HEAD to WiFi.gatewayIP(), read Date header, parse, settimeofday(). |
| WiFiManager.h | Replace ntp_synced() with clock_synced() or make ntp_synced() return clock validity. |
| fanmate.ino | Replace setup NTP wait with 3-try LAN clock wait (500 ms each). Call clock_sync() every 15 min in tick_15s(). |
| Logging.cpp | log_rotate_check() gates on time() > 1700000000UL directly, not on a flag. log_boot_recovery() preserves rows under recovered-<uptime>.csv if time unavailable. |
| Config.h | Add CLOCK_SYNC_INTERVAL_MS, CLOCK_HTTP_TIMEOUT_MS. Bump version to 4.29. |

Implementation notes:
- HTTPClient: sendRequest("HEAD", NULL, 0). No body transfer.
- Manual month/day parse -- newlib does not expose timegm() reliably on
  ESP32 core 2.0.17. Howard Hinnant days_from_civil() for epoch conversion.
- Sanity floor: reject Date values below 1700000000UL (kernel default 1970).
- Never hard-fail on clock. Clock is an enhancement, not a gate.
- Reference: Bike-Mate V5.00, commit 249322f, WifiManager.cpp opalClockSync().

Carried from v4.28 session:



Carried from v4.28 session:

- **F7 seal filename collision** — confirmed live. Two files named
  `log-4.27-20261006-1241.csv` were synced to the Mac, different sizes.
  `seal_live()` must append a counter (`-01`, `-02`) when the target name
  already exists.
- **v4.28.1: WiFi-down guard before RSSI check.** `WiFi.RSSI()` returns 0 when
  disconnected. `0 < -70` is false, so the Opal RSSI floor doesn't fire on a
  dropped link. Add `if (WiFi.status() != WL_CONNECTED) return false;` before
  the RSSI check in `rpc_call()`.

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

- **Report2H window trim.** `_find_files_since(2)` walks back by files, not
  by hours. Confirmed live: report labelled "Last 2 Hours" showed 08:00–14:00
  (6 hours). Fix: keep the file walk, then trim rows to the actual last N
  hours by timestamp before plotting. ReportDaily and ReportWeekly are fine —
  they select by date.

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
| Fan-Mate | Minimal SPIFFS (1.9MB APP / 1408KB LittleFS) | `:PartitionScheme=min_spiffs` |
| Bike-Mate | Default 4MB | *(none — default)* |

**For Fan-Mate compile:** `esp32:esp32:esp32c3:PartitionScheme=min_spiffs`.

**For Bike-Mate compile:** `esp32:esp32:esp32c3` — default partition.

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
