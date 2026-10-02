# Fan-Mate — Desk Check Audit

**Date:** 2026-10-01
**Firmware at audit:** v4.20
**Tk GUI at audit:** v3.89
**Auditors:** Gemini, ChatGPT, Copilot, Claude, Mistral

This is a consolidated desk check of the firmware and Tk GUI. Five
independent AIs read the same code dump and produced findings. This
file merges their reports, ranks by agreement and severity, and
tracks fix status.

**Column key:**
- `AIs` = how many of the five flagged this (`5/5` = unanimous)
- `Status` = `open` / `fixed <version>` / `wontfix` / `not-a-bug`

---

## PRIORITY 1 — fix before summer / silent data loss / loop-blocking

| # | Finding | File | AIs | Status |
|---|---------|------|-----|--------|
| 1 | Kick-start pulse ignores phone-absent override — fan pulses 78% every loop when phone off mount | FanController.cpp | 1/5 | **fixed v4.24** |
| 2 | Six NVS boost keys exceed 15-char limit — silently fail, revert to defaults every reboot | Settings.cpp | 1/5 | **fixed v4.22** |
| 3 | `log_evict_oldest()` isn't actually oldest — LittleFS iteration isn't sorted | Logging.cpp | 4/5 | **fixed v4.24** |
| 4 | `log_resume()` truncates live file unconditionally — wake can wipe rows if seal failed | Logging.cpp | 2/5 | **fixed v4.24** |
| 5 | Opal rate = sum of LAN clients, not WAN — Mac/other devices inflate boost | OpalClient.cpp | 1/5 | **fixed v4.24** |
| 6 | Heat gear lacks hysteresis on gears 2/3/4 — flaps at thresholds | FanController.cpp | 5/5 | **fixed v4.21** |
| 7 | Delta guard has no exit band — sawtooth at 5°C | FanController.cpp | 5/5 | **fixed v4.21** |
| 8 | Gear→% is 24/49/74/100 not 25/50/75/100 — stall check can't fire at gear 1 | FanController.cpp | 2/5 | **fixed v4.24** |
| 9 | `COOLDOWN_MARGIN_C = 0.3` too tight — cooldown almost always times out | AutoBoost.cpp | 5/5 | open |
| 10 | Cooldown defeated after any timeout — next burst captures hot phone as `cold_temp` | AutoBoost.cpp | 2/5 | open |
| 11 | WeatherClient retries every loop with no backoff — WAN down = 3s block every pass | WeatherClient.cpp | 2/5 | open |
| 12 | `_test_cooldown` can never detect a cooldown — log's `boost` is 1 during hold | dynatune.py | 3/5 | **fixed v3.91** |
| 13 | `_test_boost` under-reports every gear by one (24/49/74 issue) | dynatune.py | 2/5 | **fixed v3.91** |
| 14 | Gear ordering not validated in firmware or GUI | Settings.cpp | 5/5 | open |
| 15 | Kill display keys off `alertState==3` not `killState` — OLED lies | DisplayManager.cpp | 2/5 | open |
| 16 | 400ms kick-start + 200ms stall delays block main loop | FanController.cpp | 4/5 | **fixed v4.24** |
| 17 | `OPAL_LOGIN_REFRESH_MS` defined twice — 50min vs 4min, second wins | OpalClient.cpp | 4/5 | open |
| 18 | Version-prefixed filenames break lexical sort | Logging.cpp | 3/5 | open |
| 19 | `/log/list` caps at 32 but `LOG_MAX_SEALED` is 64 | WebServer.cpp | 2/5 | open |
| 20 | `MDNS.update()` never called — `.local` dies after a while | WiFiManager.cpp | 1/5 | open |

---

## PRIORITY 2 — real bugs, not seasonal

| # | Finding | File | AIs | Status |
|---|---------|------|-----|--------|
| 21 | Boost freezes at last state when Opal unreachable | fanmate.ino | 3/5 | **fixed v4.24** |
| 22 | `reset_all()` doesn't clear `force_active` — sleep doesn't cancel a forced gear | AutoBoost.cpp | 3/5 | open |
| 23 | 15s tick gated on `server_ready` — never starts if WiFi fails | fanmate.ino | 1/5 | open |
| 24 | `readNTC()` called 2× per loop pass, not per tick | FanController.cpp | 5/5 | open |
| 25 | `temp_graph.trigger` looks for `temp.warning` — never matches | app.py | 3/5 | **fixed v3.91** |
| 26 | NTP flag reset on WiFi drop — reports disagree on whether it works | WiFiManager.cpp | 3/5 | open |
| 27 | Stale globals in sleep — `/status` shows old fan/RPM/alert while asleep | fanmate.ino | 1/5 | open |
| 28 | `/boost/gear` is GET that mutates state; `/reboot`, `/log/clear` unauthenticated | WebServer.cpp | 1/5 | open |
| 29 | `handle_log_list` bitwise CRC over all files on every call | WebServer.cpp | 1/5 | open |
| 30 | `webTempHist`/`webNetHist` zero-filled — first 15min graphs dive to zero | fanmate.ino | 1/5 | open |
| 31 | `StaticJsonDocument<128>` in `handle_time_post` — reports disagree | WebServer.cpp | 1/5 | open |
| 32 | `StaticJsonDocument<512>` check rejects >512 payloads with misleading error | WebServer.cpp | 3/5 | open |
| 33 | Temp gear formula duplicated in `WebServer.handle_status()` | WebServer.cpp | 2/5 | open |
| 34 | Night has three definitions — compile-time, NVS, GUI hardcoded | multiple | 2/5 | open |
| 35 | `/status` SSID/IP not JSON-escaped | WebServer.cpp | 1/5 | open |
| 36 | Legacy NVS migration maps `temp.kill` to both gear3 and gear4 | Settings.cpp | 5/5 | open |
| 37 | Minute-resolution seal filenames — collisions on rapid sleep/wake | Logging.cpp | 3/5 | open |
| 38 | `handle_log_list` recomputes CRC every call — GUI polls every 30s | WebServer.cpp | 1/5 | open |
| 39 | `alg` field from Opal challenge ignored — assumes SHA-256 | OpalClient.cpp | 1/5 | open |
| 40 | `StaticJsonDocument<8192>` on loop stack — 8KB loop stack | OpalClient.cpp | 3/5 | open |
| 41 | DS18B20 85.0°C power-on-reset passes validation — above kill threshold | FanController.cpp | 1/5 | open |
| 42 | Setup blocks 20–30s at boot with fan PWM at 0 | fanmate.ino | 2/5 | open |
| 43 | NTC +6 offset calibrated at ~27°C — may be wrong at 15°C and 35°C | FanController.cpp | 2/5 | open |
| 44 | `tick()` in Tk reschedules as last statement — exception kills loop | app.py | 1/5 | **fixed v3.91** |
| 45 | Settings dialog blocks Tk thread on `fetch_config()` up to 10s | dialogs.py | 2/5 | **fixed v3.92** |
| 46 | Apply closes dialog before POST succeeds | dialogs.py | 1/5 | **fixed v3.91** |
| 47 | `_find_recent_files(2)` — last two by name, not two hours | reports.py | 5/5 | **fixed v3.91** |
| 48 | `missing` heuristic assumes 1 row / 15s | reports.py | 5/5 | **fixed v3.91** |
| 49 | `uptime:N` timestamped rows dropped silently by both parsers | Logging.cpp | 2/5 | open |
| 50 | `_test_events` doesn't count KILL | dynatune.py | 1/5 | **fixed v3.91** |
| 51 | `_test_log` counts SEALs but sleep seals inflate count | dynatune.py | 2/5 | **fixed v3.91** |
| 52 | `_test_lag` uses row counts as time | dynatune.py | 2/5 | **fixed v3.91** |
| 53 | `_test_boost` associates independent maxes (net + fan) | dynatune.py | 1/5 | **fixed v3.91** |
| 54 | Cooldown KPI recommendation can never fire | dynatune.py | 1/5 | open |
| 55 | `DynaTune._load_recent_rows(hours=18)` takes 18 files then filters | dialogs.py | 1/5 | open |
| 56 | Reports use current config threshold, not one in force at log time | dynatune.py | 1/5 | **fixed v3.91** |
| 57 | `_summarise` returns `{}` on empty files — `_build_ui` KeyError | reports.py | 1/5 | **fixed v3.91** |
| 58 | ReportPlot x-axis labels assume linear time | widgets.py | 1/5 | open |
| 59 | `fetch_config` runs only on connect — changes invisible to live GUI | app.py | 1/5 | open |

---

## PRIORITY 3 — cosmetic / dead code / stale comments

| # | Finding | File | AIs | Status |
|---|---------|------|-----|--------|
| 60 | `PWM_MIN` unused in production | Config.h | 5/5 | **fixed v4.21** |
| 61 | `TEMP_ON/FULL/WARNING/PANIC` dead, contradict real thresholds | Config.h | 2/5 | **fixed v4.21** |
| 62 | `BOOST_DEFAULT_*` dead — real defaults in `set_defaults()` | Config.h | 2/5 | **fixed v4.21** |
| 63 | `LOG_TICK_MS`, `OPAL_POLL_INTERVAL_MS` unused | Config.h | 2/5 | **fixed v4.21** |
| 64 | `// TODO(NTC)` above working `readNTC()` | Logging.cpp | 5/5 | **fixed v4.21** |
| 65 | Unused vars: `lastGoodTemp`, `lastTempGear`, `opal_last_rx`, `opal_have_baseline`, `sleep_start_ms` | multiple | 3/5 | open |
| 66 | Settings dialog labels 36/57/78% — actual 24/49/74 | dialogs.py | 5/5 | **fixed v3.91** |
| 67 | Settings dialog can't edit hysteresis or night settings | dialogs.py | 2/5 | open |
| 68 | `GUI_VERSION` drift 3.87 vs 3.89 | config.py | 5/5 | **fixed v3.90** |
| 69 | Settings.h header says "V3.73" | Settings.h | 2/5 | **fixed v4.21** |
| 70 | Duplicate `FONT_*` imports in app.py | app.py | 2/5 | open |
| 71 | `status_msg`/`status_lock` imported but unused | app.py | 1/5 | open |
| 72 | `rpm`/`phonePresent` params unused in `updateDisplay()` | DisplayManager.cpp | 1/5 | open |
| 73 | `drawFwStartScreen`, `drawOtaScreen`, `drawRebootScreen` never called | DisplayManager.cpp | 2/5 | open |
| 74 | `wakeDisplay()` log says "restored" but blanks panel | DisplayManager.cpp | 2/5 | open |
| 75 | `sleep_countdown` permanently 0 | WebServer.cpp | 4/5 | open |
| 76 | "Atkinsons Dam" typo (should be "Atkinson Dam") | WebPage.h | 1/5 | **not-a-bug** |
| 77 | Weather thread in Tk redundant — outdoor comes from `/status` | weather.py | 2/5 | open |
| 78 | Stale comment `// 7.0 was board heat` above +6.0 offset | FanController.cpp | 1/5 | **fixed v4.21** |
| 79 | TZ set in five places | multiple | 1/5 | open |
| 80 | `secrets.example.h` — `OPAL_CRYPT_HASH` missing, `OPAL_PASSWORD` unused | secrets.example.h | 1/5 | open |
| 81 | Dead branch in `opal_set_repeater(true)` — nothing calls it | OpalClient.cpp | 1/5 | open |
| 82 | Opal SID appears in serial ring, served at `/serial` | OpalClient.cpp | 1/5 | open |
| 83 | `[OPAL] check` logs every tick — 10 min of serial history | OpalClient.cpp | 2/5 | open |
| 84 | `weather_get_temp()` unknown logged as -99.0, room as blank | Logging.cpp | 1/5 | open |
| 85 | `log_time_string` calls `setenv`/`tzset` per row | Logging.cpp | 2/5 | open |
| 86 | Dashboard `DISABLE` in AUTO does nothing | WebPage.h | 1/5 | open |
| 87 | Unauthenticated destructive endpoints | WebServer.cpp | 2/5 | open |
| 88 | Net graph axis fixed 0–2048 — 4 MB/s plots off-chart | WebPage.h | 1/5 | **fixed v4.23** |
| 89 | `ntp_synced()` means clock valid, not SNTP state | WiFiManager.cpp | 1/5 | **fixed v4.21** |
| 90 | `boost_threshold` falls back to magic 700 in mode 0 | WebServer.cpp | 1/5 | open |
| 91 | `fetch_config` asks for retired `alarm`/`phone` sections | http_client.py | 2/5 | **fixed v3.93** |
| 92 | Tk disconnected state has no visible indicator | app.py | 2/5 | open |
| 93 | `hwtest.ino` uses old PWM map | hwtest/hwtest.ino | 2/5 | open |
| 94 | `is_night_now()` uses hardcoded constants, not device NVS | helpers.py | 1/5 | open |
| 95 | Event rows carry held values — parsers treat as samples | Logging.cpp | 1/5 | open |
| 96 | `map()` truncation comment says "verified on bench" but values are 24/49/74 | FanController.cpp | 1/5 | open |
| 97 | `[CFG] applied + saved` prints regardless of NVS write success | Settings.cpp | 1/5 | open |

---

## VERIFIED NOT-A-BUG

| # | Finding | Verdict |
|---|---------|---------|
| N1 | `/config` GET invalid JSON | Fixed in v4.20 |
| N2 | Songs called from multiple paths | Not present — only enter_sleep/exit_sleep |
| N3 | `FAN_STALL_ENABLED` unused | Used, but neutered at gear 1 by 24% truncation |
| N4 | CRC32 matches zlib | Correct |
| N5 | `millis()` rollover | Handled |
| N6 | `log_printf` column count | All 4 variants match 9-col header |
| N7 | `StaticJsonDocument<8192>` for Opal list | Reasonable, but stack risk |
| N8 | Phone debounce, tach math | Correct |
| N9 | `/log/file` traversal check | Fine |
| N10 | `readDS18B20` keeping last value on failure | Deliberate |
| N11 | TZ hardcoded AEST-10 | Safe (QLD no DST) |

---

## WHERE REPORTS DISAGREE

- **#26 NTP flag reset:** Gemini and Copilot say the code works and the comment lies; ChatGPT says the code lies.
- **#31 `StaticJsonDocument<128>`:** Gemini says bug in `handle_time_post`; Claude says fine there, flags only `handle_config_post`.

---

## WHERE ALL FIVE AGREE (highest confidence)

- #6 Heat gear hysteresis missing
- #7 Delta guard exit band missing
- #9 Cooldown margin too tight
- #14 Gear ordering not validated
- #24 `readNTC()` called too often
- #47 `_find_recent_files(2)` wrong
- #48 `missing` heuristic broken
- #60 `PWM_MIN` unused
- #64 `// TODO(NTC)` stale
- #66 Settings dialog labels stale
- #68 GUI version drift
