# Fan-Mate handover — OSA Server v1.4

The OSA Server on the Mac (github.com/bigbadevilaussie-hue/OSA-Server, v1.4)
now accepts a universal POST endpoint with per-channel control.

## What changed since the last handover

The old routes /panic and /fanpanic fired a fixed bundle
(iMessage + Reminder + Sinric). That’s replaced by a flexible
/notify endpoint. Fan-Mate chooses exactly which channels fire per
event.

## The new endpoint

    POST http://192.168.8.187:9999/notify
    Content-Type: application/json
    Body: {"channels": ["say", "alarm"], "msg": "Fan stall", "source": "fanmate"}

Fields:

- channels (required, array) — any subset of:
  - sms — iMessage to Nick’s Apple ID
  - reminder — Reminder (fires immediately, syncs to iPhone)
  - alexa — Echo Show speaks the routine message
  - say — Mac speaks the message aloud
  - alarm — Glass.aiff loops on the Mac for 10 seconds
- msg (required, string) — 200 chars max, newlines stripped
- source (optional, string) — "fanmate" picks the Fan-Mate Sinric
  motion sensor. Default is "bikemate". Set this to "fanmate" or your
  alerts will trigger the Bike-Mate routine instead.
- repeat (optional, int) — fires the alexa channel N times, 2s apart.
  Cap 5.

Response: {"status": "ok", "channels": ["say", "alarm"]}

## Example Fan-Mate calls

Fan stall detected:

    {"channels": ["say", "alarm"], "msg": "Fan stall detected", "source": "fanmate"}

Fan stall with escalation — Echo alert too:

    {"channels": ["sms", "alexa", "say", "alarm"], "msg": "Fan stall - overheating", "source": "fanmate"}

Room too hot, don’t fire the full chain:

    {"channels": ["alexa"], "msg": "Room is too hot, turn on AC", "source": "fanmate", "repeat": 2}

## Old routes (deprecated but still work)

- POST /fanpanic — fires sms + reminder + alexa. Fixed bundle. Kept
  as an alias. Do not use for new work.

## What Fan-Mate needs to do

Replace the current Fan-Mate firmware’s POST to /fanpanic with a
POST to /notify using the JSON body above. Set source: "fanmate" in
every call.

Update Fan-Mate’s README / HANDOVER to point at /notify and
document which channels Fan-Mate uses for which events.

## IPs and infrastructure

- OSA Server (iMac): 192.168.8.187
- Bike-Mate (ESP32): 192.168.8.196
- Fan-Mate (ESP32): 192.168.8.242

Fan-Mate’s /status endpoint is proxied by the OSA server at
GET /fan/status (10s cache). No change needed on the Fan-Mate side for
that.

## Sinric device IDs

- BikeMate motion sensor: 6acc2a5bc07d082fb430b899
- FanMate motion sensor: 6acc2b22c07d082fb430b94e

Motion sensors, not switches. Alexa refuses switches as routine triggers.

## Notes

- Mac must be logged in and awake for any channel to fire. Screen off
  is fine.
- No authentication on /notify. LAN only.
- msg is required. Empty string is OK if the channel doesn’t use it
  (e.g. alarm on its own).
- /notify has no throttle. Fan-Mate must rate-limit itself if it can
  fire rapidly.

## Open items

1. **Fan-Mate → /notify POST.** Firmware side. Fire when kill mode latches
   or fan stall alarm trips. Same wifi/HTTP pattern as Bike-Mate. Set
   source: "fanmate" so the Fan-Mate Sinric motion sensor fires, not
   Bike-Mate. Rate-limit on the device — /notify has no throttle.
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
