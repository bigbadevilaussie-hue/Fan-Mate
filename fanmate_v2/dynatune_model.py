"""Tk-free Dyna Tune data builder for the QML GUI.

Copies the loading / analysis logic from fanmate/dialogs.py::DynaTune and
returns one plain dict that QML can bind to. No tkinter import.
"""
import glob
import os
from datetime import datetime, timedelta

from fanmate import state
from fanmate.dynatune import analyse


from fanmate.config import LOG_DIR, FANMATE_URL

LABELS = {
    "boost": "BOOST", "cooldown": "COOLDOWN", "delta": "DELTA",
    "lag": "LAG", "events": "EVENTS", "log": "LOG",
    "drive": "DRIVE", "clock": "CLOCK", "boot": "BOOT",
    "opal_poll": "OPAL",
    "night_cap": "NIGHT", "heat_gears": "HEAT", "hysteresis": "HYST",
    "storage": "FS",
    "phone": "PHONE", "sleep": "SLEEP", "ntc": "NTC",
    "ds18b20": "DS18B20", "rpm": "RPM", "stall": "STALL",
    "gear_order": "GEARS", "threshold": "THR",
}
RECS = {
    "boost": "boost.on_hold 4 \u2192 2  (or lower threshold)",
    "cooldown": "review hold time",
    "delta": "check phone temp source",
    "lag": "normal \u2014 phone catches up after burst",
    "events": "check serial log",
    "log": "check clock / FS",
    "drive": "check Mac sync path",
    "clock": "Opal clock not landing",
    "boot": "frequent reboots \u2014 check power",
    "opal_poll": "Opal poll dropping",
    "night_cap": "nightMax not enforced",
    "heat_gears": "heat thresholds may be too high",
    "hysteresis": "increase tempHysteresis",
    "storage": "evict older sealed files",
    "phone": "check hall sensor",
    "sleep": "sleep/wake imbalance",
    "ntc": "check NTC wiring",
    "ds18b20": "check probe wiring",
    "rpm": "clamp RPM at 10k in firmware",
    "stall": "check fan connector",
    "gear_order": "fix gear thresholds in Settings",
    "threshold": "set 200\u201310000",
    "night_window": "fix night hours",
}
SECTIONS = [
    ("CORE", "core", ["boost", "cooldown", "delta", "lag", "events", "log"]),
    ("DATA", "data", ["drive", "clock", "boot", "opal_poll"]),
    ("DEVICE", "device", ["night_cap", "heat_gears", "hysteresis", "storage"]),
    ("HARDWARE", "hardware", ["phone", "sleep", "ntc", "ds18b20", "rpm", "stall"]),
    ("CONFIG", "config", ["gear_order", "threshold"]),
]


# ---------------------------------------------------------------- loaders
def _newest_config_time():
    pattern = os.path.join(LOG_DIR, "config-*.csv")
    files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
    if not files:
        return None
    base = os.path.basename(files[-1]).rsplit(".", 1)[0]
    parts = base.split("-")
    if len(parts) < 3:
        return None
    try:
        return datetime.strptime(parts[-2] + parts[-1], "%Y%m%d%H%M%S")
    except Exception:
        return None


def _log_file_start(path):
    base = os.path.basename(path).rsplit(".", 1)[0]
    parts = base.split("-")
    if len(parts) < 3:
        return None
    try:
        return datetime.strptime(parts[-2] + parts[-1], "%Y%m%d%H%M")
    except Exception:
        return None


def _last_recommendation():
    import csv
    path = os.path.join(LOG_DIR, "dynatune-history.csv")
    if not os.path.exists(path):
        return (None, [])
    try:
        with open(path, newline="") as fh:
            rows = list(csv.DictReader(fh))
    except Exception:
        return (None, [])
    if not rows:
        return (None, [])
    last = rows[-1]
    run_at_s = (last.get("run_at") or "").strip()
    recs_s = (last.get("recs") or "").strip()
    if not run_at_s or not recs_s:
        return (None, [])
    try:
        run_at = datetime.strptime(run_at_s, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return (None, [])
    return (run_at, [r.strip() for r in recs_s.split(";") if r.strip()])


def _parse(path):
    out = []
    try:
        with open(path, "r", errors="ignore") as f:
            first = True
            for line in f:
                if first:
                    first = False
                    if line.startswith("timestamp"):
                        continue
                if len(line) < 20 or line[0] == "#":
                    continue
                try:
                    ts = datetime(int(line[0:4]), int(line[5:7]), int(line[8:10]),
                                  int(line[11:13]), int(line[14:16]), int(line[17:19]))
                except Exception:
                    continue
                parts = line.rstrip("\n").split(",")
                if len(parts) < 6:
                    continue
                try:
                    temp = float(parts[1])
                except Exception:
                    continue
                try: net = float(parts[2]) if parts[2] else 0.0
                except Exception: net = 0.0
                try: boost = int(parts[3]) if parts[3] else 0
                except Exception: boost = 0
                try: fan = int(parts[4]) if parts[4] else 0
                except Exception: fan = 0
                try: rpm = int(parts[5]) if parts[5] else 0
                except Exception: rpm = 0
                try:
                    room = float(parts[8]) if len(parts) > 8 and parts[8] else None
                    if room is not None and room < -90.0:
                        room = None
                except Exception:
                    room = None
                event = parts[6].strip() if len(parts) > 6 else ""
                out.append({"t": ts, "temp": temp, "net": net, "boost": boost,
                            "fan": fan, "rpm": rpm, "room": room, "event": event})
    except Exception as e:
        print("[DynaTune] parse " + path + ": " + str(e))
    return out


def _load_recent_rows():
    """Returns (rows, cfg_time, files_skipped, rows_dropped)."""
    pattern = os.path.join(LOG_DIR, "log-*.csv")
    files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
    if not files:
        return [], None, 0, 0

    cfg_time = _newest_config_time()
    cutoff = cfg_time if cfg_time is not None else datetime.min
    rows = []
    files_skipped = 0
    dropped = 0
    HOUR = timedelta(hours=1)

    for path in files:
        f_start = _log_file_start(path)
        if f_start is None:
            parsed = _parse(path)
            before = len(parsed)
            parsed = [r for r in parsed if r["t"] >= cutoff]
            dropped += before - len(parsed)
            rows.extend(parsed)
            continue
        if f_start + HOUR < cutoff:
            files_skipped += 1
            continue
        if f_start >= cutoff:
            rows.extend(_parse(path))
            continue
        parsed = _parse(path)
        before = len(parsed)
        parsed = [r for r in parsed if r["t"] >= cutoff]
        if parsed:
            dropped += before - len(parsed)
            rows.extend(parsed)
        else:
            files_skipped += 1

    rows.sort(key=lambda r: r["t"])
    return rows, cfg_time, files_skipped, dropped


def _age(dt):
    s = (datetime.now() - dt).total_seconds()
    if s < 3600:
        return "%dm" % int(s / 60)
    if s < 86400:
        return "%.1fh" % (s / 3600)
    return "%.1fd" % (s / 86400)


# ---------------------------------------------------------------- builder
def build_dynatune():
    """Run the analysis and return a QML-friendly dict. Blocking: call from
    a worker thread."""
    rows, cfg_time, files_skipped, rows_dropped = _load_recent_rows()
    if not rows:
        return {"hasData": False, "message": "No log data found"}

    start, end = rows[0]["t"], rows[-1]["t"]
    span_h = (end - start).total_seconds() / 3600.0
    ver = str(state.latest.get("fv", "?"))

    # settings-change line
    if cfg_time is None:
        filter_text = "full window \u2014 no settings change on disk"
        filter_ok = False
    else:
        filter_text = "settings changed " + _age(cfg_time) + " ago"
        if files_skipped or rows_dropped:
            filter_text += " \u00b7 %df/%dr pre-change" % (files_skipped, rows_dropped)
        filter_ok = True

    # last recommendation
    rec_at, rec_list = _last_recommendation()
    last_rec = ""
    if rec_list:
        extra = "  (+%d)" % (len(rec_list) - 1) if len(rec_list) > 1 else ""
        last_rec = "last rec: %s%s \u00b7 %s ago" % (rec_list[0], extra, _age(rec_at))

    # boost threshold
    try:
        b = state.latest_config.get("boost", {})
        if b.get("mode", 1) == 2:
            thr = int(b.get("threshold", 900))
        else:
            thr = int(b.get("normal", {}).get("threshold", 700))
    except Exception:
        thr = 700

    try:
        live_status = dict(state.latest)
    except Exception:
        live_status = None
    try:
        live_config = dict(state.latest_config)
    except Exception:
        live_config = None
    log_info = None
    try:
        import requests
        r = requests.get(FANMATE_URL + "/log/info", timeout=2)
        if r.status_code == 200:
            log_info = r.json()
    except Exception:
        pass

    kpis = analyse(rows, boost_thr=thr, live_status=live_status,
                   live_config=live_config, log_info=log_info)

    passed = warned = failed = idle = 0
    issues, recs = [], []
    for sec_name in ("core", "data", "device", "hardware", "config"):
        sec = kpis.get(sec_name, {})
        if not isinstance(sec, dict):
            continue
        for key, data in sec.items():
            if not isinstance(data, dict):
                continue
            st = data.get("status", "IDLE")
            label = LABELS.get(key, key.upper())
            if st in ("PASS", "IDLE"):
                passed += 1
                idle += (st == "IDLE")
            elif st in ("WARN", "FAIL"):
                if st == "WARN":
                    warned += 1
                else:
                    failed += 1
                issues.append({"label": label, "metric": str(data.get("metric", "")),
                               "severity": st})
                recs.append(label + ": " + RECS.get(key, "investigate"))

    if failed:
        n = failed + warned
        verdict = {"status": "FAIL", "icon": "\u2717",
                   "text": "%d issue%s need attention" % (n, "" if n == 1 else "s")}
    elif warned:
        verdict = {"status": "WARN", "icon": "\u26a0",
                   "text": "%d minor issue%s" % (warned, "" if warned == 1 else "s")}
    else:
        verdict = {"status": "PASS", "icon": "\u2713", "text": "healthy"}

    pills = [{"text": "%d PASS" % passed + ("  (%d idle)" % idle if idle else ""),
              "status": "PASS"}]
    if warned:
        pills.append({"text": "%d WARN" % warned, "status": "WARN"})
    if failed:
        pills.append({"text": "%d FAIL" % failed, "status": "FAIL"})

    sections = []
    for sec_label, sec_key, keys in SECTIONS:
        sec = kpis.get(sec_key, {})
        chips = []
        for k in keys:
            d = sec.get(k, {}) if isinstance(sec, dict) else {}
            st = d.get("status", "IDLE")
            chips.append({"label": LABELS.get(k, k.upper()),
                          "status": "PASS" if st == "IDLE" else st})
        sections.append({"label": sec_label, "chips": chips})

    return {
        "hasData": True,
        "version": "FW v" + ver,
        "window": "%s  \u2192  %s" % (start.strftime("%a %d %b %H:%M"), end.strftime("%H:%M")),
        "span": "%.1f h  \u00b7  %d samples" % (span_h, len(rows)),
        "filterText": filter_text,
        "filterOk": filter_ok,
        "lastRec": last_rec,
        "verdict": verdict,
        "pills": pills,
        "sections": sections,
        "issues": issues,
        "issuesTitle": "FAILURES" if failed else "ISSUES",
        "recs": recs,
        "footer": "rows %d  \u00b7  span %.1fh  \u00b7  boost thr %d KB/s" % (len(rows), span_h, thr),
    }
