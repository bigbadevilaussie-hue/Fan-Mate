#!/bin/bash
# Fan-Mate handoff generator
# Run before starting a new chat session.

cd "$(dirname "$0")"

{
  echo "# Fan-Mate — Chat Handoff"
  echo ""
  echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
  echo ""
  echo "---"
  echo ""
  echo "## GIT STATE"
  echo ""
  echo '```'
  echo "\$ git log --oneline -5"
  git log --oneline -5
  echo ""
  echo "\$ git status --short"
  git status --short
  echo ""
  echo "\$ git tag -l | tail -10"
  git tag -l | tail -10
  echo '```'
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
  echo "## GUI FILES"
  echo ""
  echo '```'
  ls -la fanmate.py fanmate/*.py 2>/dev/null
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
echo "To paste into new chat:"
echo "  cat $(pwd)/HANDOFF.md | pbcopy"
