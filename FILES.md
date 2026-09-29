# Fan-Mate — File Index

One entry per file. Purpose / Key items / Notes.

---

### fanmate.ino
- **Purpose:** Main coordinator — setup, loop, 15s tick, sleep state machine.
- **Key vars:** currentTemp, fanPct, fanRPM, alertState, phonePresent, sys_state, webTempHist[], webNetHist[], webHistIdx.
- **Key funcs:** setup, loop, tick_15s, enter_sleep, exit_sleep.
- **Notes:** Owns global state. Exposes history ring buffers for web page.

### Config.h
- **Purpose:** Single source of truth — pins, constants, version.
- **Key defines:** FAN_MATE_VERSION, DEBUG_VERBOSE, GPIO pins, PWM, buzzer, HTTP, Opal, AutoBoost, logging.
- **Notes:** Version 3.80.

### Settings.cpp / .h
- **Purpose:** Config load/save via NVS Preferences, JSON apply.
- **Key vars:** config (FanMateConfig struct), NVS "fanmate" namespace.
- **Key funcs:** settings_load, settings_save, settings_reset, settings_apply_json, settings_is_night.
- **Notes:** All temp/boost/night/phone settings live here.

### FanController.cpp / .h
- **Purpose:** DS18B20 read, hall sensor, fan PWM, tach, buzzer, alert levels, stall detection.
- **Key vars:** fanPWM, fanPctLocal, fanRPMLocal, alertLevel, beep state, temp gear state, lastFanGear.
- **Key funcs:** readDS18B20, updatePhoneDetection, updateFanAndAlerts, updateTach, initHardware, silenceFanAndAlerts, fan_stall_active.
- **Notes:** Fan stall alarm gated by FAN_STALL_ENABLED. Beep sequence has gap-timer fix.

### DisplayManager.cpp / .h
- **Purpose:** OLED rendering.
- **Key funcs:** initDisplay, updateDisplay, drawSplashScreen, drawFwStartScreen, drawOtaScreen, drawRebootScreen, clearDisplay, wakeDisplay.
- **Notes:** Bottom line priority: FAN STALL > Log Paused > time.

### WiFiManager.cpp / .h
- **Purpose:** WiFi bring-up, mDNS, NTP sync.
- **Key vars:** _ntp_synced_flag, ntp_started.
- **Key funcs:** wifi_setup, wifi_loop, ntp_loop, ntp_synced, wifi_connected, wifi_ip, wifi_rssi.
- **Notes:** NTP flag resets when WiFi drops — requires fresh sync on reconnect.

### WebServer.cpp / .h
- **Purpose:** HTTP endpoints.
- **Key funcs:** server_setup, server_loop, and per-endpoint handlers.
- **Notes:** Serves WebPage.h from flash via send_P. /status extended with history arrays.

### OpalClient.cpp / .h
- **Purpose:** Router login, WAN traffic poll.
- **Key funcs:** opal_init, opal_poll, opal_pause, opal_resume, opal_logged_in.
- **Notes:** Every 15s. Also drives LED during rpc_call.

### AutoBoost.cpp / .h
- **Purpose:** Rate-based boost gears + thermal cooldown hold. Rewritten in v4.10.
- **State machine:** `PH_IDLE` → `PH_RUNNING` → `PH_COOLDOWN` → `PH_IDLE`
- **Key vars:** `phase`, `data_gear`, `over_ticks`, `under_ticks`, `cold_temp`, `cooldown_start`, `force_active`, `force_gear_value`, `force_start`
- **Key funcs:** `auto_boost_init`, `auto_boost_update(net_kbps, phone_temp, net_ok)`, `auto_boost_gear`, `auto_boost_release`, `auto_boost_threshold`, `auto_boost_force_gear(n, phone_temp)`, `auto_boost_cooling`, `auto_boost_cold_temp`
- **How it works:**
  - **Data gear** = `floor(rate / threshold)`, clamped 0–4. One gear per `on_hold` ticks up, one per `off_hold` down.
  - **Down-band hysteresis** — gear holds until rate drops below `80% × current_gear × threshold`.
  - **Cold temp** captured on first tick over threshold while idle. Persists across sessions, overwritten on next boost start.
  - **Cooldown** — when data gear returns to 0, phase → COOLDOWN. `auto_boost_gear()` returns 1 (hold) until `phone_temp <= cold_temp + 0.3°C` or 20-min timeout.
  - **Router-down** — call site passes `opal_ok` as `net_ok`; cooldown check still runs when router unreachable.
  - **Force** — `/boost/gear?n=N` locks gear, auto-releases after 30 min, kicks to COOLDOWN on release.
- **Config:** Uses `boostNormal` / `boostAggr` thresholds and on/off_hold. `boostMode == 0` disables entirely.
- **Notes:** Log lines: `[BOOST] start cold=X`, `[BOOST] gear+ ...`, `[BOOST] gear- ...`, `[BOOST] data stopped, cooling to X`, `[BOOST] cooled (...) end`, `[BOOST] force gear=N`, `[BOOST] force released`, `[BOOST] force expired`.

### Logging.cpp / .h
- **Purpose:** CSV log write, hourly rotation, seal, boot recovery, time-jump guard.
- **Key vars:** _live_file_start_epoch (NVS persisted).
- **Key funcs:** log_init, log_write, log_write_event, log_rotate_check, log_boot_recovery, log_clear, log_list_sealed, log_delete_sealed, log_rotation_paused, log_get_size.
- **Notes:** Schema 8 columns + outdoor_c. Boot skips seal if clock unset. Time-jump resets epoch instead of refusing forever.

### SerialBuffer.cpp / .h
- **Purpose:** Ring buffer feeding /serial web page.
- **Key funcs:** serial_buf_init, log_print, get_serial_dump.
- **Notes:** Buffer size 50 lines. Important events route through log_print.

### WeatherClient.cpp / .h
- **Purpose:** Open-Meteo fetch, cached in NVS Preferences.
- **Key funcs:** weather_init, weather_loop, weather_get_temp.
- **Notes:** 15-minute refresh. Returns -99 if not yet fetched.

### WebPage.h
- **Purpose:** Embedded responsive HTML dashboard as PROGMEM string.
- **Notes:** Served at /. Light theme only. Uses /status + history arrays. 5s poll. Threshold lines drawn on graphs.

---

## Python GUI (package `fanmate/`)

### fanmate.py
- **Purpose:** Launcher. 11 lines.
- **Notes:** `python3 fanmate.py`.

### fanmate/config.py
- **Purpose:** Constants — URLs, paths, intervals, fonts, themes.
- **Notes:** GUI_VERSION, FANMATE_URL, LOG_DIR.

### fanmate/state.py
- **Purpose:** Shared mutable state.
- **Key vars:** latest, latest_config, temp_hist, download_hist, connected, time_synced, status_msg, fonts.
- **Notes:** Never rebind; mutate in place. Everything else imports from here.

### fanmate/helpers.py
- **Purpose:** Theme, time, emoji, version reads.
- **Key funcs:** is_daytime, current_theme, set_status, get_status, read_target_version, read_device_version, compute_md5, local_time_str, time_emoji, phone_temp_emoji, fan_emoji.
- **Notes:** set_status/get_status write/read state.status_msg via state.

### fanmate/http_client.py
- **Purpose:** /status polling, /config fetch, /time sync.
- **Key funcs:** http_poll_loop, fetch_config, sync_time_once.
- **Notes:** Uses state.* for scalars. 10s timeout. Prints "connected" once per session.

### fanmate/log_sync.py
- **Purpose:** Pull sealed logs from ESP32.
- **Key funcs:** log_sync_loop.
- **Notes:** CRC32 verify. Saves to LOG_DIR. Acks on success, nacks on CRC mismatch. 30s poll.

### fanmate/weather.py
- **Purpose:** Weather fetch thread.
- **Key funcs:** fetch_weather, weather_thread_loop, weather_code_to_desc.
- **Notes:** Open-Meteo Brisbane. 30-min refresh.

### fanmate/widgets.py
- **Purpose:** Tk widgets.
- **Classes:** Card, Graph, ReportPlot.
- **Notes:** Theme-aware. Graph has trigger line support.

### fanmate/dialogs.py
- **Purpose:** Settings dialog + DynaTune window.
- **Classes:** SettingsDialog, DynaTune.
- **Notes:** Themed to match App. Applies on close, no success toast.

### fanmate/reports.py
- **Purpose:** Report windows.
- **Classes:** Report2H, ReportDaily, ReportWeekly.
- **Notes:** All subclass Report2H, override _find_files() and _HEADER. Plot x-axis time labels, gear counts.

### fanmate/app.py
- **Purpose:** Main App class, window, menu, tick loop.
- **Key funcs:** menu_settings, menu_report_2h/daily/weekly, menu_dyna_tune, menu_ota, tick, apply_theme, theme_check.
- **Notes:** Reads state.connected for status line. Launches 3 threads.

---

## Docs

### PROJECT_STATE.md
Project snapshot — versions, hardware, pin map, features, known issues, next steps.

### FILES.md (this file)
One entry per file.

### HANDOFF.md
Generated by update_handoff.sh. Git state + PROJECT_STATE + file list + live /status + log list.

### README.md
Public-facing intro.

### update_handoff.sh
Regenerates HANDOFF.md.

### PROJECT.md
Legacy doc (stale, says v3.44). Superseded by PROJECT_STATE.md.

---

## External

### Config.h secrets
- secrets.h — WiFi creds, Opal password (gitignored)
- secrets.example.h — template

### Build
- build/esp32.esp32.esp32c3/ — compiled binaries

### Logs
- ~/Documents/FanMate_logs/ — sealed CSV files
- ~/Documents/FanMate_logs/firmware/ — archived .bin files

### Related
- Bike-Mate: https://github.com/bigbadevilaussie-hue/Bike-Mate
