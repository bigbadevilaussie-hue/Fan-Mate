# Fan-Mate handover — OSA Server

The Mac-side automation hub is now live. Repo:
github.com/bigbadevilaussie-hue/OSA-Server (private).

## What it does

The OSA Server runs 24/7 on Nick's iMac as a LaunchAgent. Receives HTTP
POSTs from ESP32 devices on the LAN and fires Mac-side alerts. Two ESP32
projects use it:

- Bike-Mate POSTs to /panic
- Fan-Mate POSTs to /fanpanic

Each POST triggers a chain: iMessage, Reminder, sound on the Mac, and a
Sinric Pro switch that Alexa picks up as a smart-home device. Alexa
routines on the Echo Show announce the alert.

## What Fan-Mate needs to send

When Fan-Mate needs to alert (fan stalled, temp too high, whatever):

    POST http://192.168.8.187:9999/fanpanic
    Body: "Fan-Mate: <message>"

The OSA Server flips the Fan-Mate Sinric switch on. Alexa's routine
fires on the Echo Show. The switch auto-flips off 10 seconds later, ready
for the next alert.

Throttle: the server throttles /panic to once per 5 min but /fanpanic
has no throttle yet. If Fan-Mate alerts frequently, add one.

## Status page

http://localhost:9999/ shows server state, weather, both switch states,
and Fan-Mate live data — the server proxies http://192.168.8.242/status
with a 10s cache. So Fan-Mate's existing /status endpoint feeds the OSA
status page automatically. No firmware change needed on Fan-Mate for that.

## IPs

- OSA Server (iMac): 192.168.8.187
- Bike-Mate (ESP32): 192.168.8.196
- Fan-Mate (ESP32): 192.168.8.242

## Sinric Pro

Two switches registered:

- Bike-Mate — 6acc0adac07d082fb430a0b0
- Fan-Mate — 6acc0b658039cc7898da9d9d

Free tier = 3 devices. One slot spare.

For Alexa integration: enable the Sinric Pro skill in the Alexa app
(iOS/iPad), sign in with the same Sinric Pro account. Alexa discovers
both switches. Create a routine: "When Fan-Mate turns on -> Alexa says"
...

## Open items

1. **Fan-Mate → /fanpanic POST.** Firmware side. Fire when kill mode latches
   or fan stall alarm trips. Same wifi/HTTP pattern as Bike-Mate. Server route
   exists and works; no throttle on /fanpanic yet.
2. **Move log_sync into OSA Server.** Python process already runs 24/7 at
   login. Same code as fanmate/log_sync.py, threaded, 30s cadence, CRC verify.
   Delete fanmate/log_sync.py and its thread from fanmate/app.py once moved.
   GUIs read from ~/Documents/FanMate_logs/ off disk either way.
3. **Menu bar indicator (xbar plugin).** Script at
   ~/Library/Application Support/xbar/plugins/fanmate.10s.py. Hits
   http://192.168.8.242/status, prints phone temp + RPM for the bar, full
   detail in the dropdown. xbar already installed (Mac fan monitor icon).
   No bundle, no daemon, no compile.

## Adding more to the OSA Server

The server is a Python process. It can do anything a Python script can:
smtplib, open, shortcuts run, POST to Slack/Discord/ntfy, HomeKit via
Shortcuts. Add as a named route. Never add a generic command execution
endpoint.
