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

    nets = [r["net"] for r in rows if r["net"] is not None]
    peak = max(nets) if nets else 0

    # The log's boost column is binary (0/1), not the gear number.
    # Infer max gear from fan % — firmware maps gear N to fan %:
    # gear 1 = 25, gear 2 = 50, gear 3 = 75, gear 4 = 100.
    max_gear = 0
    for r in rows:
        f = r["fan"]
        if f >= 100:   max_gear = max(max_gear, 4)
        elif f >= 75:  max_gear = max(max_gear, 3)
        elif f >= 50:  max_gear = max(max_gear, 2)
        elif f >= 25:  max_gear = max(max_gear, 1)

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
    """How did cooldown events release — temperature or timeout?

    We can infer cooldown events from the log: when boost drops to 0
    but fan stays at 25% for a while. Without explicit event logging
    we approximate: count periods where boost=0 and fan in {24,25,26}
    lasting 2+ rows. Called "cooling episodes". Hard to distinguish
    temperature-release from timeout in the log; for now just count.
    """
    if not rows:
        return {"status": "IDLE", "metric": "no data", "detail": ""}

    episodes = 0
    in_episode = False
    for r in rows:
        cooling = (r["boost"] == 0 and 24 <= r["fan"] <= 26)
        if cooling and not in_episode:
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
    events = 0
    above = False
    for d in deltas:
        if d > 5.0 and not above:
            events += 1
            above = True
        elif d <= 5.0:
            above = False

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

    thr = boost_thr
    high = thr * 2.5
    low = thr * 0.6

    for i in range(20, len(rows) - 25):
        prev = [r["net"] for r in rows[i - 15:i] if r["net"] is not None]
        after = [r["net"] for r in rows[i:i + 12] if r["net"] is not None]
        if prev and after and max(prev) > high and max(after) < low:
            t_drop = rows[i]["temp"]
            later = [r["temp"] for r in rows[i:i + 35] if r["temp"] > 0]
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
        if any(x in ev for x in ("PANIC", "WDT", "BROWNOUT", "FAN_STALL")):
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

    seals = sum(1 for r in rows
                if (r.get("event") or "").upper() == "SEAL")

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

    # Build a single-line recommendation if any KPI is WARN/FAIL.
    warns = [k for k, v in result.items()
             if v["status"] in ("WARN", "FAIL")]
    if not warns:
        result["recommendation"] = ""
    elif "cooldown" in warns:
        result["recommendation"] = "⚠  Cooldown activity — review boost hold time"
    elif "boost" in warns:
        result["recommendation"] = "⚠  Boost stalled — check threshold / on_hold"
    elif "events" in warns:
        result["recommendation"] = "⚠  Bad events detected — check serial log"
    elif "log" in warns:
        result["recommendation"] = "⚠  Log seals missing — check NTP / FS"
    else:
        result["recommendation"] = f"⚠  {', '.join(warns).upper()} warnings"

    return result
