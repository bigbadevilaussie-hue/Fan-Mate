# Fan-Mate handover — current state

Read this before touching the repo. Supersedes anything in git history.

## What Fan-Mate is

ESP32-C3 fan controller. Cools an iPhone on a 24/7 hotspot mount in rural
Queensland. Watches router WAN traffic, spins a 40mm PWM fan when downloads
are detected, logs hourly. Runs autonomously whether the Mac is on or off.

## Versions (actual, as of 2026-10-13)

- Firmware:  `FAN_MATE_VERSION` in `Config.h`            -> 4.61
- Tk GUI:    `GUI_VERSION` in `fanmate/config.py`        -> 4.61
- QML GUI2:  `guiVersion` in `fanmate_v2/qml/Main.qml`   -> 1.12

Bump all three BEFORE compiling. Bump, compile, commit — in that order.
If the bump lands after the compile, the firmware reports the old version
and log filenames carry the old prefix.

## Verified working on Sonoma (2026-10-13)

- ESP32 reachable at 192.168.8.242. Firmware v4.61 serving `/status`
  and `/log/list`. Web dashboard serves.
- Tk GUI:  ~/fanmate-venv-test/bin/python fanmate.py
  Telemetry live. Log sync pulling sealed CSVs into
  ~/Documents/FanMate_logs/ via CRC32. Confirmed on 15+ hourly files.
- QML GUI2:  ~/fanmate-venv-test/bin/python -m fanmate_v2.main
  All gauges live. Reads /status through fanmate_v2/bridge.py.
- ~/fanmate-venv-test/ holds PySide6 6.12.0 + requests.
  bleak was installed by mistake. Unused. Safe to remove.

## What the firmware does NOT do

- No POST to OSA Server. No /notify, no /fanpanic, no Sinric.
  Grep of *.cpp/*.h/*.ino returned zero hits. Any doc describing
  this behaviour is a stale plan, not current code.
- Does not depend on any Mac-side process for its core function.
  The Mac runs GUI + OTA only. The ESP32 cools and logs standalone.

## Where things live

- fanmate/log_sync.py          log sync. Threaded into app.py:149.
                                Do not move it, do not delete it.
- fanmate/dynatune.py          pure-Python KPI analysis. No GUI imports.
- fanmate_v2/dynatune_model.py Tk-free wrapper for the QML side.
- ~/Documents/FanMate_logs/    sealed CSVs + firmware/ archive of .bin files.

## Three things that will bite you

1. Custom SSD1306 fork required.
   ~/Documents/Arduino/libraries/Adafruit_SSD1306_72x40/
   Not the upstream Adafruit library. Compile fails without it.
2. ESP32 core must be 2.0.17. Not 3.x.
   fanmate.ino has a #error guard, so a wrong core fails loudly.
3. Version bump before compile. See top of this file.

## Known cosmetic issues

- fanmate/config.py GUI_VERSION was 4.59, now 4.61. Aligned 2026-10-13.
- fanmate_v2/requirements.txt pin was ==6.4.3, now >=6.4.

## Pending

- FanMate_temp_vs_data.csv (4229 rows, Sept 25) still on the Catalina
  volume at /Volumes/Home — Data/Users/Nick/Documents/. Low priority.
  sudo cp, then sudo chown nick:staff.

## Patching convention (from README)

Write each patch as a Python heredoc into /tmp/patch.py. Back up first
with shutil.copy2. End with a verification print. Patch and run in one
block. Never paste standalone multi-line shell that edits files.
