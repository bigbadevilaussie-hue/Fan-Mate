#!/bin/bash
cd "$(dirname "$0")"

{
  echo "# Fan-Mate — Chat Handoff"
  echo ""
  echo "> **NEW AI — DO THIS FIRST.**"
  echo "> "
  echo "> Do not summarise this document back to Nick."
  echo "> Do not offer to help with a task yet."
  echo "> "
  echo "> Read the \"GETTING THE NEXT AI UP TO SPEED\" section in NOTES.md (below)."
  echo "> Ask Nick to run the dump command it contains. He will paste the output."
  echo "> Read the source files. Only then start work."
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
  curl -s --max-time 5 http://fan-mate.local/status | python3 -m json.tool 2>/dev/null || echo "device unreachable"
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
