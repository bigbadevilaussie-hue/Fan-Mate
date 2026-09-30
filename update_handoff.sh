#!/bin/bash
cd "$(dirname "$0")"

{
  echo "# Fan-Mate — Chat Handoff"
  echo ""
  echo "> **NEW AI — YOUR FIRST RESPONSE MUST BE TO ASK NICK TO RUN THE DUMP COMMAND.**"
  echo "> "
  echo "> Do NOT summarise this document back to Nick."
  echo "> Do NOT offer to help with a task."
  echo "> Do NOT ask what he wants to work on."
  echo "> Just ask him to run the dump command below. That is your entire first reply."
  echo "> "
  echo "> When he pastes the output, read the source files. Only then start work."
  echo "> "
  echo "> The dump command:"
  echo "> "
  echo ">     cd ~/Documents/Arduino/fanmate"
  echo ">     {"
  echo ">       echo \"===== GIT STATE =====\""
  echo ">       git fetch --all --tags 2>&1"
  echo ">       git log --oneline -15"
  echo ">       git status --short"
  echo ">       git tag -l | tail -20"
  echo ">       echo"
  echo ">       echo \"===== VERSIONS =====\""
  echo ">       grep FAN_MATE_VERSION Config.h"
  echo ">       grep GUI_VERSION fanmate/config.py"
  echo ">       grep guiVersion fanmate_v2/qml/Main.qml 2>/dev/null"
  echo ">       echo"
  echo ">       echo \"===== DOCS =====\""
  echo ">       for f in HANDOFF.md NOTES.md PROJECT_STATE.md FILES.md README.md; do"
  echo ">         echo \"########## \$f ##########\"; cat \"\$f\" 2>&1; echo"
  echo ">       done"
  echo ">       echo \"===== FIRMWARE =====\""
  echo ">       for f in Config.h fanmate.ino AutoBoost.h AutoBoost.cpp \\"
  echo ">                FanController.h FanController.cpp DisplayManager.h DisplayManager.cpp \\"
  echo ">                WiFiManager.h WiFiManager.cpp WebServer.h WebServer.cpp WebPage.h \\"
  echo ">                OpalClient.h OpalClient.cpp Logging.h Logging.cpp \\"
  echo ">                SerialBuffer.h SerialBuffer.cpp Settings.h Settings.cpp \\"
  echo ">                WeatherClient.h WeatherClient.cpp Songs.h Songs.cpp; do"
  echo ">         echo \"########## \$f ##########\"; cat \"\$f\" 2>&1; echo"
  echo ">       done"
  echo ">       echo \"===== TK GUI =====\""
  echo ">       for f in fanmate.py fanmate/__init__.py fanmate/config.py fanmate/state.py \\"
  echo ">                fanmate/helpers.py fanmate/http_client.py fanmate/log_sync.py \\"
  echo ">                fanmate/weather.py fanmate/widgets.py fanmate/dialogs.py \\"
  echo ">                fanmate/reports.py fanmate/app.py; do"
  echo ">         echo \"########## \$f ##########\"; cat \"\$f\" 2>&1; echo"
  echo ">       done"
  echo ">       echo \"===== QML GUI2 =====\""
  echo ">       for f in fanmate_v2/__init__.py fanmate_v2/bridge.py fanmate_v2/main.py \\"
  echo ">                fanmate_v2/qml/Main.qml fanmate_v2/qml/TempGauge.qml \\"
  echo ">                fanmate_v2/qml/RpmGauge.qml fanmate_v2/qml/TrafficGauge.qml \\"
  echo ">                fanmate_v2/qml/BoostBar.qml fanmate_v2/qml/TempBar.qml \\"
  echo ">                fanmate_v2/qml/StatusLamps.qml fanmate_v2/qml/MenuButton.qml \\"
  echo ">                fanmate_v2/qml/OtaDialog.qml fanmate_v2/qml/Bar.qml; do"
  echo ">         echo \"########## \$f ##########\"; cat \"\$f\" 2>&1; echo"
  echo ">       done"
  echo ">       echo \"===== LIVE DEVICE =====\""
  echo ">       curl -s --max-time 5 http://192.168.8.242/status 2>&1 | python3 -m json.tool 2>&1 | head -50"
  echo ">       curl -s --max-time 5 http://192.168.8.242/config 2>&1 | python3 -m json.tool 2>&1"
  echo ">       echo \"===== LOGS =====\""
  echo ">       ls -la ~/Documents/FanMate_logs/*.csv 2>/dev/null | tail -5"
  echo ">     } > ~/Desktop/fanmate-dump.txt 2>&1"
  echo ">     wc -l ~/Desktop/fanmate-dump.txt"
  echo "> "
  echo "> Naming: GUI = Tk (fanmate/*.py), GUI2 = QML (fanmate_v2/*),"
  echo "> Web = WebPage.h (needs flash), Firmware = *.cpp/*.h/fanmate.ino."
  echo "> "
  echo "> Nick's shell is zsh and eats multi-line pastes. Patch via Python"
  echo "> scripts written to /tmp/ then run with python3. Never paste heredocs"
  echo "> or # comments directly."
  echo ""
  echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "---"
  echo ""
  echo "## GIT STATE"
  echo ""
  echo '```'
  echo "\$ git log --oneline -10"
  git log --oneline -10
  echo ""
  echo "\$ git status --short"
  git status --short
  echo ""
  echo "\$ git tag -l | tail -15"
  git tag -l | tail -15
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## VERSIONS"
  echo ""
  echo '```'
  grep "FAN_MATE_VERSION" Config.h
  grep "GUI_VERSION" fanmate/config.py 2>/dev/null
  grep "guiVersion" fanmate_v2/qml/Main.qml 2>/dev/null
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## NOTES.md"
  echo ""
  cat NOTES.md
  echo ""
  echo "---"
  echo ""
  echo "## PROJECT_STATE.md"
  echo ""
  cat PROJECT_STATE.md
  echo ""
  echo "---"
  echo ""
  echo "## FIRMWARE FILES"
  echo ""
  echo '```'
  ls -la *.h *.cpp *.ino 2>/dev/null
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## TK GUI FILES"
  echo ""
  echo '```'
  ls -la fanmate.py fanmate/*.py 2>/dev/null
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## QML GUI2 FILES"
  echo ""
  echo '```'
  ls -la fanmate_v2/*.py fanmate_v2/qml/*.qml 2>/dev/null
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## LIVE DEVICE"
  echo ""
  echo '```'
  curl -s --max-time 5 http://192.168.8.242/status | python3 -m json.tool 2>/dev/null || echo "device unreachable"
  echo '```'
  echo ""
  echo "---"
  echo ""
  echo "## LOG FILES ON MAC"
  echo ""
  echo '```'
  ls -la ~/Documents/FanMate_logs/*.csv 2>/dev/null | tail -10
  echo '```'
  echo ""
} > HANDOFF.md

echo "HANDOFF.md updated ($(wc -l < HANDOFF.md) lines)"
echo ""
echo "Path: $(pwd)/HANDOFF.md"
