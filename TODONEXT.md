# Fan-Mate — Todo Next

## Current state (2026-10-07)

- Firmware **v4.50** — configurable delta trigger, RPM clamp
- Tk GUI **v4.50** — matches Web, Delta trigger setting, heat threshold check
- QML GUI2 **v1.11** — parked

Both firmware and GUI tags pushed. Everything tested, everything committed.

## Confirmed working

- **Apply settings** — value changes persist to NVS, config snapshot
  writes on Apply, Drive upload (302) succeeds. The earlier "Apply does
  not work" report was a test artefact: Apply was pressed without
  changing any value, so nothing appeared to change.
- **DynaTune** — opens in under 1 second on 19k rows (was 6 minutes
  before the `_test_lag` O(n) rewrite).
- **Network resilience** — Opal hang no longer stalls the ESP32 WebServer.
- **Tk matches Web** — alert/stall/sleep/opal/boost states now render
  identically across both UIs.

## Open — real

### F1. No-op Apply must not seal + snapshot [minor]

Every Apply seals the log and writes a `config-*.csv`. That moves the
DynaTune cutoff to the snapshot timestamp. If nothing changed, this
blanks the window for ~25 minutes until the next hourly seal.

Fix in `Settings.cpp settings_apply_json()`:
  1. Copy `config` at function entry
  2. Parse JSON into `config`
  3. Compare entry vs parsed. If identical, log "no change" and skip
     settings_save(), log_seal_now(), log_write_config_snapshot(),
     log_write_event("CFG_APPLIED")
  4. If different, proceed as now

### F2. DynaTune doesn't distinguish external vs internal reboots [minor]

`_test_boot` counts all BOOT/SOFTWARE/POWERON events the same. Storm
brownouts and firmware crashes look identical. Fix: parse the reset
reason from the log's event column (`POWERON`, `BROWNOUT`, `PANIC`,
`WDT`, `SOFTWARE`) and only WARN on the internal ones. External resets
should be reported but not flagged.

### F3. DynaTune heat-gear tolerance may be too tight [minor]

`_test_heat_gears` WARNs when `temp.gear1` differs from
`avg_room + delta_trigger` by more than 1.5°C. That's tight for a
variable environment. Consider loosening to 2.5 or 3.0. Current board
shows `HEAT: g1 33.0 vs room+5.1 = 29.3` (diff 3.7) — genuine signal,
but the same test will fire on a well-tuned 30.0 gear1 in a 25°C room
(diff 0.7, passes) but WARN on 32.0 (diff 2.7).

## Open — cosmetic

### C1. DynaTune "tell me off" header

Header shows `last rec: <top rec>` from the newest `dynatune-history.csv`
row. It echoes the rec without acknowledging whether it was acted on.
Should say: `still unaddressed — 14m, 4 runs` when the same rec appears
in consecutive history rows. Add to `fanmate/dialogs.py` header block;
needs `_rec_streak()` walker in place of `_last_recommendation()`.

### C2. Dead code in `dialogs.py`

`_kpi_card` and `_recommendation_bar` methods in `DynaTune` are
defined but never called since the pretty layout rewrite. Safe to
delete.

### C3. `PWM_MIN = 40` unused in Config.h

The flat PWM map doesn't use it. Either remove or annotate as
documentation.

### C4. Docs regen

- HANDOFF.md still says v4.28 / v3.95 — regen
- PROJECT_STATE.md version history stops at v4.28
- Partition-scheme contradiction in HANDOFF top block (says DEFAULT,
  actual is min_spiffs)

## Parked

- QML GUI2 v1.12 — settings panel (Rectangle overlay, not Drawer),
  kill banner, delta lamp, bridge URLs use IP not .local
- Thermal runaway failsafe — sensor health (DS18B20 stale detection,
  NTC plausibility, rate-of-rise). Designed, not implemented.
- Night cap removal — `FanController.cpp` caps at `nightMax` (75%),
  no UI to change. Feature decision.
- Temp gear hysteresis for gears 2/3/4 — currently exact-threshold.
  Only gear 1 entry has hysteresis.
- WiFi Nokia trigger — patch failed, only phone-detect triggers.
