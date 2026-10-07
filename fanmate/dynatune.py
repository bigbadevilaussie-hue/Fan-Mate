"""Fan-Mate DynaTune — KPI board analysis.

Pure Python. Takes a list of parsed log rows (dicts with keys
t, temp, net, boost, fan, rpm, room) and returns a dict of KPI
results. No GUI, no I/O — the caller provides rows.

Status values: PASS / WARN / FAIL / IDLE
IDLE means "no evidence either way" — not a failure.
"""


def _status_dots(status):
    """5-dot indicator: PASS=5, WARN=3, FAIL=1, IDLE=2."""
    return {"PASS": 5, "WARN": 3, "FAIL": 1, "IDLE": 2}.get(status, 0)


def _test_boost(rows, boost_thr=700):
    """Did boost ramp cleanly when rate supported it?

    Look at the highest network rate in the window. If it was >= 3x thr,
    check whether boost reached gear 3 or higher during that burst.
    """
    if not rows:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    # Clamp rate at 10 MB/s to reject tick-stretch artefacts
    nets = [min(r["net"], 10240.0) for r in rows if r["net"] is not None]
    peak = max(nets) if nets else 0

    # The log's boost column is binary (0/1), not the gear number.
    # Infer max gear from fan % — firmware maps gear N to fan %:
    # gear 1 = 25, gear 2 = 50, gear 3 = 75, gear 4 = 100.
    # Fan % from firmware is integer-truncated:
    #   gear 1 -> map(map(1,0,4,0,255),0,255,0,100) = 24
    #   gear 2 -> 49   (not 50 — map(127,0,255,0,100) truncates)
    #   gear 3 -> 74
    #   gear 4 -> 100
    max_gear = 0
    for r in rows:
        f = r["fan"]
        if f >= 100:   max_gear = max(max_gear, 4)
        elif f >= 74:  max_gear = max(max_gear, 3)
        elif f >= 49:  max_gear = max(max_gear, 2)
        elif f >= 24:  max_gear = max(max_gear, 1)

    thr = boost_thr
    expected = min(4, int(peak / thr)) if peak >= thr else 0

    if expected == 0:
        return {"status": "IDLE", "metric": "no load", "detail": ""}

    if max_gear >= expected:
        return {"status": "PASS", "metric": f"ramp {max_gear}/4",
                "detail": f"peak {peak:.0f} KB/s"}
    if max_gear >= expected - 1:
        return {"status": "WARN", "metric": f"ramp {max_gear}/{expected}",
                "detail": f"stalled below target {expected}"}
    return {"status": "FAIL", "metric": f"ramp {max_gear}/{expected}",
            "detail": f"peak {peak:.0f} KB/s, expected gear {expected}"}


def _test_cooldown(rows):
    """Count cooling episodes.

    Firmware log's boost column is auto_boost_gear()>0, which is 1
    during cooldown hold. So a cooldown row looks like: boost=1, fan
    at gear 1 (24-25%). Match that signature, and require the episode
    to follow a period of high network activity (a boost session).
    Without a cooling flag in the log, temp-release vs timeout cannot
    be distinguished.
    """
    if not rows:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    # Walking window: only count an episode that starts within
    # 5 minutes of a net rate above threshold.
    episodes = 0
    in_episode = False
    recent_high = False
    high_until_idx = 0
    for i, r in enumerate(rows):
        if r["net"] is not None and r["net"] > 700:
            high_until_idx = i + 20   # 20 rows ~= 5 min at 15s
        recent_high = (i < high_until_idx)

        cooling = (r["boost"] == 1 and 24 <= r["fan"] <= 26)
        if cooling and not in_episode and recent_high:
            episodes += 1
            in_episode = True
        elif not cooling:
            in_episode = False

    if episodes == 0:
        return {"status": "IDLE", "metric": "0 episodes", "detail": ""}

    return {"status": "PASS", "metric": f"{episodes} events",
            "detail": "count only (timeout vs temp not logged)"}


def _test_delta(rows):
    """Peak phone-room delta in the window."""
    if not rows:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    deltas = []
    for r in rows:
        if r["temp"] is None or r["room"] is None:
            continue
        deltas.append(r["temp"] - r["room"])

    if not deltas:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    peak = max(deltas)
    # Match firmware: enter at 5.0, exit at 3.0 (hysteresis band).
    events = 0
    above = False
    for d in deltas:
        if above:
            if d < 3.0:
                above = False
        else:
            if d > 5.0:
                events += 1
                above = True

    if peak < 5.0:
        return {"status": "IDLE", "metric": f"max {peak:.1f}",
                "detail": "guard armed, never fired"}
    return {"status": "PASS" if events <= 3 else "WARN",
            "metric": f"max {peak:.1f}",
            "detail": f"{events} event(s) > 5°C"}


def _test_lag(rows, boost_thr=700):
    """Detect post-burst thermal lag using linear moving windows."""
    if len(rows) < 40:
        return {"status": "IDLE", "metric": "window small", "detail": ""}

    from collections import deque
    from datetime import timedelta

    high = boost_thr * 2.5
    low = boost_thr * 0.6
    n = len(rows)

    # Rows are chronological. Each deque holds candidate indexes for
    # the maximum value in its moving timestamp window.
    prev_q = deque()
    after_q = deque()
    later_q = deque()

    prev_right = 0
    after_right = 0
    later_right = 0

    for i, row in enumerate(rows):
        ti = row["t"]

        prev_start = ti - timedelta(minutes=4)
        after_end = ti + timedelta(minutes=3)
        later_end = ti + timedelta(minutes=9)

        while prev_right < i:
            v = rows[prev_right]["net"]
            if v is not None:
                while prev_q and rows[prev_q[-1]]["net"] <= v:
                    prev_q.pop()
                prev_q.append(prev_right)
            prev_right += 1

        while prev_q and rows[prev_q[0]]["t"] < prev_start:
            prev_q.popleft()

        while after_right < n and rows[after_right]["t"] < after_end:
            v = rows[after_right]["net"]
            if v is not None and after_right >= i:
                while after_q and rows[after_q[-1]]["net"] <= v:
                    after_q.pop()
                after_q.append(after_right)
            after_right += 1

        while after_q and after_q[0] < i:
            after_q.popleft()

        while later_right < n and rows[later_right]["t"] < later_end:
            v = rows[later_right]["temp"]
            if v > 0 and later_right >= i:
                while later_q and rows[later_q[-1]]["temp"] <= v:
                    later_q.pop()
                later_q.append(later_right)
            later_right += 1

        while later_q and later_q[0] < i:
            later_q.popleft()

        if prev_q and after_q:
            if rows[prev_q[0]]["net"] > high and rows[after_q[0]]["net"] < low:
                t_drop = row["temp"]
                if later_q:
                    peak = rows[later_q[0]]["temp"]
                    rise = peak - t_drop
                    if rise >= 1.5:
                        return {
                            "status": "PASS",
                            "metric": f"+{rise:.1f}°C",
                            "detail": f"{t_drop:.1f} → {peak:.1f}"
                        }

    return {"status": "IDLE", "metric": "none", "detail": ""}

def _test_events(rows):
    """Count bad events in the log (PANIC, WDT, BROWNOUT, FAN_STALL)."""
    bad = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if any(x in ev for x in ("PANIC", "WDT", "BROWNOUT", "FAN_STALL",
                                  "KILL_ACTIVE", "KILL")):
            bad += 1

    if bad == 0:
        return {"status": "PASS", "metric": "0 bad", "detail": ""}
    if bad <= 2:
        return {"status": "WARN", "metric": f"{bad} bad", "detail": ""}
    return {"status": "FAIL", "metric": f"{bad} bad", "detail": ""}


def _test_log(rows):
    """Seals per hour — did the device seal as expected?"""
    if not rows:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    # Count only hourly seals (>=30 min apart). Sleep/wake also emit SEAL.
    seal_times = [r["t"] for r in rows
                  if (r.get("event") or "").upper() == "SEAL"]
    seals = 0
    last_t = None
    for t in seal_times:
        if last_t is None or (t - last_t).total_seconds() >= 1800:
            seals += 1
            last_t = t

    # Expected seals = hours in the window
    span_hours = (rows[-1]["t"] - rows[0]["t"]).total_seconds() / 3600.0
    expected = max(1, int(round(span_hours)))

    if seals >= expected - 1:
        return {"status": "PASS", "metric": f"{seals}/{expected}",
                "detail": ""}
    if seals >= expected - 2:
        return {"status": "WARN", "metric": f"{seals}/{expected}",
                "detail": "missing seals"}
    return {"status": "FAIL", "metric": f"{seals}/{expected}",
            "detail": "log rotation broken"}



def _test_drive(rows):
    """UPLOAD ack/nack events in the log confirm the Mac is pulling
    sealed files. Events use ';' not ',' (sanitized for CSV safety)."""
    uploads = 0
    nacks = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if ev.startswith("UPLOAD;") and ";OK" in ev:
            uploads += 1
        elif "NACK" in ev:
            nacks += 1
    if nacks > 0:
        return {"status": "FAIL", "metric": f"{nacks} nacks",
                "detail": "CRC failures"}
    if uploads == 0:
        return {"status": "IDLE", "metric": "no acks",
                "detail": "Mac may not be running"}
    return {"status": "PASS", "metric": f"{uploads} acks", "detail": ""}


def _test_clock(rows):
    """Are all timestamps wall-clock, or are there uptime rows?"""
    wall = 0
    uptime = 0
    for r in rows:
        t = r.get("t")
        if isinstance(t, str) and t.startswith("uptime:"):
            uptime += 1
        else:
            wall += 1
    total = wall + uptime
    if total == 0:
        return {"status": "IDLE", "metric": "no data", "detail": ""}
    if uptime == 0:
        return {"status": "PASS", "metric": "all wall", "detail": ""}
    pct = 100.0 * uptime / total
    if pct < 5:
        return {"status": "WARN", "metric": f"{uptime} uptime",
                "detail": f"{pct:.0f}% no clock"}
    return {"status": "FAIL", "metric": f"{uptime} uptime",
            "detail": f"{pct:.0f}% no clock"}


def _test_boot(rows):
    """Did any reboots leave boot recovery rows?"""
    boots = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if ev in ("BOOT", "SOFTWARE", "POWERON"):
            boots += 1
    if boots == 0:
        return {"status": "IDLE", "metric": "no reboots", "detail": ""}
    if boots <= 10:
        return {"status": "PASS", "metric": f"{boots} boots", "detail": ""}
    return {"status": "WARN", "metric": f"{boots} boots",
            "detail": "frequent reboots"}


def _test_opal_poll(rows):
    """Opal poll should be 15s cadence. Check the net column's continuity."""
    if len(rows) < 10:
        return {"status": "IDLE", "metric": "small window", "detail": ""}
    gaps = 0
    for i in range(1, len(rows)):
        dt = (rows[i]["t"] - rows[i-1]["t"]).total_seconds()
        if dt > 60:
            gaps += 1
    if gaps == 0:
        return {"status": "PASS", "metric": "no gaps", "detail": ""}
    if gaps <= 3:
        return {"status": "PASS", "metric": f"{gaps} gap(s)",
                "detail": "within tolerance"}
    if gaps <= 6:
        return {"status": "WARN", "metric": f"{gaps} gaps", "detail": ""}
    return {"status": "FAIL", "metric": f"{gaps} gaps",
            "detail": "log has multiple >60s gaps"}


def _test_night_cap(rows, night_start=22, night_end=7, night_max=75):
    """Was fan capped at nightMax during night hours?"""
    night_rows = [r for r in rows
                  if _is_night(r["t"], night_start, night_end)]
    if not night_rows:
        return {"status": "IDLE", "metric": "no night rows", "detail": ""}
    over = [r for r in night_rows if r["fan"] > night_max + 2]
    if not over:
        return {"status": "PASS", "metric": f"0/{len(night_rows)}",
                "detail": f"capped at {night_max}%"}
    return {"status": "FAIL", "metric": f"{len(over)} over",
            "detail": f"exceeds {night_max}%"}


def _is_night(t, start, end):
    h = t.hour
    if start < end:
        return start <= h < end
    return h >= start or h < end


def _test_heat_gears(rows, g1=33.0, g2=35.0, g3=37.0, g4=39.0, delta_trigger=5.1):
    """Heat gears + threshold plausibility vs observed room temp.

    If the delta guard's trigger (room+5.1) sits meaningfully below the
    absolute gear-1 threshold (g1), the absolute rule will never fire
    before the delta rule already has — so g1 is too high for the room
    it runs in. Recommend aligning g1 to room + delta_trigger.
    """
    # Fan % from firmware is integer-truncated (see _test_boost comment).
    # gear 2 reports as 49, not 50.
    fired = set()
    for r in rows:
        t = r["temp"]
        f = r["fan"]
        if t >= g4 and f >= 100: fired.add(4)
        elif t >= g3 and f >= 74: fired.add(3)
        elif t >= g2 and f >= 49: fired.add(2)
        elif t >= g1 and f >= 24: fired.add(1)
    peaks = [max((r["temp"] for r in rows), default=0)]
    peak = peaks[0]
    expected = 0
    if peak >= g4: expected = 4
    elif peak >= g3: expected = 3
    elif peak >= g2: expected = 2
    elif peak >= g1: expected = 1
    if expected == 0:
        return {"status": "IDLE", "metric": "no heat",
                "detail": f"peak {peak:.1f}°C below gear1"}
    # Threshold-vs-delta plausibility check
    rooms = [r["room"] for r in rows if r.get("room") is not None and r["room"] > -90]
    avg_room = sum(rooms) / len(rooms) if rooms else None
    if avg_room is not None:
        suggested_g1 = round(avg_room + delta_trigger, 1)
        if abs(g1 - suggested_g1) >= 1.5:
            return {"status": "WARN",
                    "metric": f"g1 {g1:.1f} vs room+{delta_trigger} = {suggested_g1:.1f}",
                    "detail": f"avg room {avg_room:.1f}, suggest {suggested_g1:.1f}"}

    if max(fired) >= expected:
        return {"status": "PASS", "metric": f"up to {max(fired)}",
                "detail": f"peak {peak:.1f}°C"}
    return {"status": "WARN", "metric": f"reached {max(fired) or 0}",
            "detail": f"expected gear {expected}"}


def _test_hysteresis(rows, g1=33.0, hyst=1.0):
    """Count gear1 transitions per heat event — flapping indicates
    missing hysteresis."""
    transitions = 0
    last = None
    for r in rows:
        gear = 0
        if r["fan"] >= 24: gear = 1
        if last is not None and gear != last and gear == 1:
            transitions += 1
        last = gear
    # Normal: one entry per heat event. Flapping: many entries per hour.
    span_h = (rows[-1]["t"] - rows[0]["t"]).total_seconds() / 3600.0
    rate = transitions / max(1, span_h)
    if rate < 4:
        return {"status": "PASS", "metric": f"{transitions} entries",
                "detail": ""}
    return {"status": "WARN", "metric": f"{transitions} entries",
            "detail": f"{rate:.1f}/h — possible flapping"}


def _test_phone(rows):
    """Any PHONE events logged?"""
    present = 0
    removed = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if "PHONE" in ev:
            if "DETECT" in ev or "PRESENT" in ev:
                present += 1
            elif "REMOVED" in ev or "ABSENT" in ev:
                removed += 1
    if present + removed == 0:
        return {"status": "IDLE", "metric": "no transitions", "detail": ""}
    if abs(present - removed) > 2:
        return {"status": "WARN", "metric": f"{present}/{removed}",
                "detail": "unbalanced detect/remove"}
    return {"status": "PASS", "metric": f"{present}/{removed}", "detail": ""}


def _test_sleep(rows):
    """SLEEP/WAKE events should pair up."""
    sleep = 0
    wake = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if ev == "SLEEP": sleep += 1
        elif ev == "WAKE": wake += 1
    if sleep + wake == 0:
        return {"status": "IDLE", "metric": "none", "detail": ""}
    if abs(sleep - wake) <= 1:
        return {"status": "PASS", "metric": f"{sleep}/{wake}", "detail": ""}
    return {"status": "WARN", "metric": f"{sleep}/{wake}",
            "detail": "unbalanced sleep/wake"}


def _test_ntc(rows):
    """Room temp should be in 5–45°C."""
    rooms = [r["room"] for r in rows
             if r.get("room") is not None and r["room"] > -90]
    if not rooms:
        return {"status": "IDLE", "metric": "no room data", "detail": ""}
    lo, hi = min(rooms), max(rooms)
    if lo < 5 or hi > 45:
        return {"status": "FAIL", "metric": f"{lo:.0f}–{hi:.0f}",
                "detail": "out of plausible range"}
    if lo < 15 or hi > 40:
        return {"status": "WARN", "metric": f"{lo:.0f}–{hi:.0f}",
                "detail": "edge of plausible range"}
    return {"status": "PASS", "metric": f"{lo:.0f}–{hi:.0f}", "detail": ""}


def _test_ds18b20(rows):
    """Phone temp: reject 85.0 (power-on-reset) and 0.0."""
    temps = [r["temp"] for r in rows if r["temp"] is not None]
    if not temps:
        return {"status": "IDLE", "metric": "no data", "detail": ""}
    bad = [t for t in temps if t == 85.0 or t == 0.0 or t < -50 or t > 120]
    if not bad:
        return {"status": "PASS", "metric": f"{len(temps)} reads", "detail": ""}
    return {"status": "FAIL", "metric": f"{len(bad)} bad",
            "detail": "85.0 or 0.0 detected"}


def _test_rpm(rows):
    """RPM should never exceed 10,000 (real max ~7500)."""
    rpms = [r["rpm"] for r in rows if r["rpm"] > 0]
    if not rpms:
        return {"status": "IDLE", "metric": "no rpm", "detail": ""}
    bad = [x for x in rpms if x > 10000]
    if not bad:
        return {"status": "PASS", "metric": f"max {max(rpms)}", "detail": ""}
    return {"status": "WARN", "metric": f"{len(bad)} outliers",
            "detail": f"max {max(bad)} — tick artefacts"}


def _test_stall(rows):
    """FAN_STALL without FAN_RECOVERED indicates a stuck stall alarm."""
    stalls = 0
    recovers = 0
    for r in rows:
        ev = (r.get("event") or "").upper()
        if "FAN_STALL" in ev: stalls += 1
        elif "FAN_RECOVERED" in ev: recovers += 1
    if stalls == 0:
        return {"status": "PASS", "metric": "0 stalls", "detail": ""}
    if stalls <= recovers:
        return {"status": "PASS", "metric": f"{stalls}/{recovers}",
                "detail": "all recovered"}
    return {"status": "WARN", "metric": f"{stalls}/{recovers}",
            "detail": "unrecovered stall"}


# ---------- config tests (from live_config) ----------

def _test_gear_order(cfg):
    t = (cfg or {}).get("temp", {})
    g1 = t.get("gear1", 0); g2 = t.get("gear2", 0)
    g3 = t.get("gear3", 0); g4 = t.get("gear4", 0)
    if not all([g1, g2, g3, g4]):
        return {"status": "IDLE", "metric": "no config", "detail": ""}
    if g1 < g2 < g3 < g4:
        return {"status": "PASS", "metric": f"{g1:.0f}<{g2:.0f}<{g3:.0f}<{g4:.0f}",
                "detail": ""}
    return {"status": "FAIL", "metric": f"{g1}<{g2}<{g3}<{g4}",
            "detail": "gear order violated"}


def _test_threshold(cfg):
    b = (cfg or {}).get("boost", {})
    mode = b.get("mode", 1)
    if mode == 2:
        thr = b.get("aggr", {}).get("threshold", 0)
    elif mode == 1:
        thr = b.get("normal", {}).get("threshold", 0)
    else:
        return {"status": "IDLE", "metric": "mode 0", "detail": "boost off"}
    if 200 <= thr <= 10000:
        return {"status": "PASS", "metric": f"{thr} KB/s", "detail": ""}
    return {"status": "FAIL", "metric": f"{thr} KB/s",
            "detail": "outside 200–10000"}


def _test_boost_mode(cfg):
    mode = (cfg or {}).get("boost", {}).get("mode", None)
    if mode is None:
        return {"status": "IDLE", "metric": "no config", "detail": ""}
    if mode in (0, 1, 2):
        names = {0: "off", 1: "normal", 2: "aggr"}
        return {"status": "PASS", "metric": names[mode], "detail": ""}
    return {"status": "FAIL", "metric": str(mode), "detail": "not 0/1/2"}


def _test_night_window(cfg):
    n = (cfg or {}).get("night", {})
    start = n.get("start"); end = n.get("end")
    maxp = n.get("nightMax")
    if start is None or end is None:
        return {"status": "IDLE", "metric": "no config", "detail": ""}
    if start == end:
        return {"status": "WARN", "metric": f"{start}–{end}",
                "detail": "start == end (no night)"}
    if not (0 <= start <= 23 and 0 <= end <= 23):
        return {"status": "FAIL", "metric": f"{start}–{end}",
                "detail": "hour out of 0–23"}
    if maxp is not None and not (0 <= maxp <= 100):
        return {"status": "FAIL", "metric": f"max {maxp}",
                "detail": "nightMax out of 0–100"}
    return {"status": "PASS", "metric": f"{start}–{end} @ {maxp}%", "detail": ""}


def _test_storage(rows, log_info=None):
    """If /log/info is available, check free space trend."""
    if log_info is None:
        return {"status": "IDLE", "metric": "no info", "detail": ""}
    free = log_info.get("free_bytes", 0)
    total = 1408 * 1024
    used_pct = 100.0 * (total - free) / max(1, total)
    if used_pct < 75:
        return {"status": "PASS", "metric": f"{used_pct:.0f}% used", "detail": ""}
    if used_pct < 90:
        return {"status": "WARN", "metric": f"{used_pct:.0f}% used",
                "detail": "approaching cap"}
    return {"status": "FAIL", "metric": f"{used_pct:.0f}% used",
            "detail": "rotation pausing imminent"}


def analyse(rows, boost_thr=700, live_status=None, live_config=None,
            log_info=None):
    """Run all tests. Sections:
      core     — boost / cooldown / delta / lag / events / log
      data     — drive / clock / boot / opal_poll
      device   — night_cap / heat_gears / hysteresis / storage
      hardware — phone / sleep / ntc / ds18b20 / rpm / stall
      config   — gear_order / threshold / boost_mode / night_window
    """
    cfg = live_config or {}
    night = cfg.get("night", {}) if cfg else {}
    n_start = night.get("start", 22)
    n_end   = night.get("end", 7)
    n_max   = night.get("nightMax", 75)
    t_cfg   = cfg.get("temp", {}) if cfg else {}
    g1 = t_cfg.get("gear1", 33.0)
    g2 = t_cfg.get("gear2", 35.0)
    g3 = t_cfg.get("gear3", 37.0)
    g4 = t_cfg.get("gear4", 39.0)

    result = {
        "core": {
            "boost":    _test_boost(rows, boost_thr),
            "cooldown": _test_cooldown(rows),
            "delta":    _test_delta(rows),
            "lag":      _test_lag(rows, boost_thr),
            "events":   _test_events(rows),
            "log":      _test_log(rows),
        },
        "data": {
            "drive":     _test_drive(rows),
            "clock":     _test_clock(rows),
            "boot":      _test_boot(rows),
            "opal_poll": _test_opal_poll(rows),
        },
        "device": {
            "night_cap":  _test_night_cap(rows, n_start, n_end, n_max),
            "heat_gears": _test_heat_gears(rows, g1, g2, g3, g4,
                                           t_cfg.get("delta_trigger", 5.1)),
            "hysteresis": _test_hysteresis(rows, g1, 1.0),
            "storage":    _test_storage(rows, log_info),
        },
        "hardware": {
            "phone":   _test_phone(rows),
            "sleep":   _test_sleep(rows),
            "ntc":     _test_ntc(rows),
            "ds18b20": _test_ds18b20(rows),
            "rpm":     _test_rpm(rows),
            "stall":   _test_stall(rows),
        },
        "config": {
            "gear_order":   _test_gear_order(cfg),
            "threshold":    _test_threshold(cfg),
            "boost_mode":   _test_boost_mode(cfg),
            "night_window": _test_night_window(cfg),
        },
    }

    msgs = {
        "boost":        "Boost stalled — check threshold / on_hold",
        "cooldown":     "Cooldown episodes — review hold time",
        "delta":        "Delta guard active — check phone temp",
        "lag":          "Thermal lag detected",
        "events":       "Bad events detected — check serial log",
        "log":          "Log seals missing — check clock / FS",
        "drive":        "Drive upload failures",
        "clock":        "Timestamps using uptime — Opal clock failing",
        "boot":         "Frequent reboots",
        "opal_poll":    "Log has >60s gaps — Opal poll dropping",
        "night_cap":    "Night cap not enforced",
        "heat_gears":   "Heat gears not firing as expected",
        "hysteresis":   "Possible gear flapping",
        "storage":      "Storage approaching cap",
        "phone":        "Phone detect imbalance",
        "sleep":        "Sleep/wake imbalance",
        "ntc":          "Room temp out of range",
        "ds18b20":      "Phone temp sensor errors",
        "rpm":          "RPM outliers",
        "stall":        "Fan stall not recovering",
        "gear_order":   "Heat gear order invalid",
        "threshold":    "Boost threshold out of range",
        "boost_mode":   "Boost mode invalid",
        "night_window": "Night window invalid",
    }

    warns = []
    for section_name, section in result.items():
        if not isinstance(section, dict):
            continue
        for k, v in section.items():
            if isinstance(v, dict) and v.get("status") in ("WARN", "FAIL"):
                warns.append(k)

    if not warns:
        result["recommendation"] = ""
    else:
        parts = [msgs.get(k, k.upper()) for k in warns]
        result["recommendation"] = "⚠  " + " · ".join(parts)

    return result
