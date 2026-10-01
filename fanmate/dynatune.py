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
    max_gear = 0
    for r in rows:
        f = r["fan"]
        if f >= 100:   max_gear = max(max_gear, 4)
        elif f >= 74:  max_gear = max(max_gear, 3)
        elif f >= 50:  max_gear = max(max_gear, 2)
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
    """Detect post-burst thermal lag (already implemented in DynaTune)."""
    if len(rows) < 40:
        return {"status": "IDLE", "metric": "window small", "detail": ""}

    from datetime import timedelta
    thr = boost_thr
    high = thr * 2.5
    low = thr * 0.6

    # Timestamp-based windows: 4 min before, 3 min after, 9 min for rise.
    for i in range(len(rows)):
        ti = rows[i]["t"]
        prev = [r["net"] for r in rows
                if ti - timedelta(minutes=4) <= r["t"] < ti
                and r["net"] is not None]
        after = [r["net"] for r in rows
                 if ti <= r["t"] < ti + timedelta(minutes=3)
                 and r["net"] is not None]
        if prev and after and max(prev) > high and max(after) < low:
            t_drop = rows[i]["temp"]
            later = [r["temp"] for r in rows
                     if ti <= r["t"] < ti + timedelta(minutes=9)
                     and r["temp"] > 0]
            if later:
                peak = max(later)
                rise = peak - t_drop
                if rise >= 1.5:
                    return {"status": "PASS", "metric": f"+{rise:.1f}°C",
                            "detail": f"{t_drop:.1f} → {peak:.1f}"}
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


def analyse(rows, boost_thr=700):
    """Run all six tests. rows is a list of dicts with keys
    t, temp, net, boost, fan, rpm, room, event (optional).
    Returns a dict of KPI results plus a recommendation string.
    """
    result = {
        "boost":    _test_boost(rows, boost_thr),
        "cooldown": _test_cooldown(rows),
        "delta":    _test_delta(rows),
        "lag":      _test_lag(rows, boost_thr),
        "events":   _test_events(rows),
        "log":      _test_log(rows),
    }

    # Collect all WARN/FAIL recommendations.
    msgs = {
        "boost":    "Boost stalled — check threshold / on_hold",
        "cooldown": "Cooldown episodes — review hold time",
        "delta":    "Delta guard active — check phone temp",
        "lag":      "Thermal lag detected",
        "events":   "Bad events detected — check serial log",
        "log":      "Log seals missing — check NTP / FS",
    }
    warns = [k for k, v in result.items()
             if v["status"] in ("WARN", "FAIL")]

    if not warns:
        result["recommendation"] = ""
    else:
        parts = [msgs.get(k, k.upper()) for k in warns]
        result["recommendation"] = "⚠  " + " · ".join(parts)

    return result
