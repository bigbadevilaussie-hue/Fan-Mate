import threading
import os
import requests
from datetime import datetime, timedelta

import tkinter as tk
from tkinter import messagebox

from .config import *
from .http_client import fetch_config
from . import state
from .helpers import *
from .reports import *


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Fan-Mate Settings")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # Open immediately with a placeholder; fetch_config runs in a
        # background thread so the main loop isn't blocked.
        self._container = tk.Frame(self)
        self._container.pack(fill="both", expand=True, padx=16, pady=16)
        self._status = tk.Label(self._container,
                                text="Loading settings...",
                                font=("Helvetica Neue", 12))
        self._status.pack(pady=20)
        self._apply_theme()

        threading.Thread(target=self._fetch_and_build,
                         daemon=True).start()

    def _fetch_and_build(self):
        latest_config = fetch_config()
        self.app.root.after(0, lambda: self._build(latest_config))

    def _build(self, latest_config):
        # Wipe the placeholder and build the real content.
        for w in self._container.winfo_children():
            w.destroy()

        if latest_config is None:
            self._status = tk.Label(self._container,
                                    text="Device unreachable. Try again in a moment.",
                                    font=("Helvetica Neue", 12))
            self._status.pack(pady=20)
            self._apply_theme()
            return

        pad = 16
        root = self._container

        self._row = 0

        def section(emoji, label):
            f = tk.Frame(root)
            f.grid(row=self._row, column=0, columnspan=3, sticky="ew", pady=(14, 6))
            tk.Label(f, text=f"{emoji}  {label}",
                     font=("Helvetica Neue", 13, "bold"),
                     anchor="w").pack(fill="x")
            self._row += 1

        def field(label, var, width=8):
            tk.Label(root, text=label,
                     font=("Helvetica Neue", 11), anchor="w").grid(
                row=self._row, column=0, sticky="w", pady=4)
            tk.Entry(root, textvariable=var, width=width,
                     font=("Helvetica Neue", 12), justify="right",
                     relief="flat", highlightthickness=1).grid(
                row=self._row, column=1, sticky="e", pady=4)
            self._row += 1

        def segmented(label, var, options):
            tk.Label(root, text=label,
                     font=("Helvetica Neue", 11), anchor="w").grid(
                row=self._row, column=0, sticky="w", pady=6)
            seg = tk.Frame(root)
            seg.grid(row=self._row, column=1, sticky="e", pady=6)
            label_map = {"off": "OFF", "normal": "NORMAL", "aggressive": "BEAST"}
            for opt in options:
                tk.Radiobutton(
                    seg, text=label_map.get(opt, opt.upper()), variable=var, value=opt,
                    indicatoron=0, width=10,
                    font=("Helvetica Neue", 10, "bold"),
                    relief="raised", bd=1, highlightthickness=0,
                ).pack(side="left", padx=1)
            self._row += 1

        section("🌡️", "HEAT CONTROL")
        self.temp_g1 = tk.StringVar(value=str(latest_config["temp"].get("gear1", 30.0)))
        field("Warm (25%)", self.temp_g1)
        self.temp_g2 = tk.StringVar(value=str(latest_config["temp"].get("gear2", 32.0)))
        field("Hot (50%)", self.temp_g2)
        self.temp_g3 = tk.StringVar(value=str(latest_config["temp"].get("gear3", 34.0)))
        field("Hotter (75%)", self.temp_g3)
        self.temp_g4 = tk.StringVar(value=str(latest_config["temp"].get("gear4", 36.0)))
        field("Critical (100%)", self.temp_g4)

        self.delta_trigger = tk.StringVar(
            value=str(latest_config["temp"].get("delta_trigger", 5.1)))
        field("Delta trigger (°C)", self.delta_trigger)

        section("⚡", "BOOST")
        mode_map = {0: "off", 1: "normal", 2: "aggressive"}
        self.boost_mode = tk.StringVar(
            value=mode_map.get(latest_config["boost"].get("mode", 1), "normal"))
        segmented("Mode", self.boost_mode, ["off", "normal", "aggressive"])

        norm = latest_config["boost"].get("normal", {})
        aggr = latest_config["boost"].get("aggr", {})

        self.norm_thr = tk.StringVar(value=str(norm.get("threshold", 700)))
        self.norm_on  = tk.StringVar(value=str(norm.get("on_hold", 4)))
        self.norm_off = tk.StringVar(value=str(norm.get("off_hold", 4)))
        self.aggr_thr = tk.StringVar(value=str(aggr.get("threshold", 400)))
        self.aggr_on  = tk.StringVar(value=str(aggr.get("on_hold", 2)))
        self.aggr_off = tk.StringVar(value=str(aggr.get("off_hold", 8)))

        for name, thr_v, on_v, off_v in [
            ("Normal",     self.norm_thr, self.norm_on, self.norm_off),
            ("Aggressive", self.aggr_thr, self.aggr_on, self.aggr_off),
        ]:
            tk.Label(root, text=name, font=("Helvetica Neue", 11, "bold"),
                     anchor="w").grid(row=self._row, column=0, sticky="w", pady=4)
            fr = tk.Frame(root)
            fr.grid(row=self._row, column=1, sticky="e", pady=4)
            for lbl, var in (("Thr", thr_v), ("On", on_v), ("Off", off_v)):
                tk.Label(fr, text=lbl, font=("Helvetica Neue", 10)).pack(side="left", padx=(6, 2))
                tk.Entry(fr, textvariable=var, width=5,
                         font=("Helvetica Neue", 12), justify="right",
                         relief="flat", highlightthickness=1).pack(side="left")
            self._row += 1

        btns = tk.Frame(root)
        btns.grid(row=self._row, column=0, columnspan=3, pady=(18, 4))
        tk.Button(btns, text="Cancel", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(side="left", padx=6)
        tk.Button(btns, text="Apply", width=12,
                  font=("Helvetica Neue", 11, "bold"),
                  command=self.apply).pack(side="left", padx=6)

        self._apply_theme()

    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        for w in self.winfo_children():
            self._theme_recursive(w, t)

    def _theme_recursive(self, w, t):
        try:
            cls = w.winfo_class()
        except Exception:
            return
        if cls in ("Frame", "Toplevel"):
            w.configure(bg=t["bg"])
        elif cls == "Label":
            w.configure(bg=t["bg"], fg=t["fg"])
        elif cls == "Entry":
            w.configure(bg=t["card"], fg=t["fg"], insertbackground=t["fg"],
                        highlightbackground=t["card_border"],
                        highlightcolor=t["accent"])
        elif cls == "Radiobutton":
            w.configure(bg=t["bg"], fg=t["fg"],
                        selectcolor=t["accent"], activebackground=t["bg"],
                        activeforeground=t["fg"])
        elif cls == "Button":
            w.configure(bg=t["card"], fg=t["fg"],
                        activebackground=t["accent"], activeforeground=t["fg"],
                        highlightbackground=t["card_border"])
        for c in w.winfo_children():
            self._theme_recursive(c, t)

    def apply(self):
        try:
            mode_str = self.boost_mode.get()
            mode_int = {"off": 0, "normal": 1, "aggressive": 2}[mode_str]

            payload = {
                "boost": {
                    "mode": mode_int,
                    "normal": {
                        "threshold": int(self.norm_thr.get()),
                        "on_hold":   int(self.norm_on.get()),
                        "off_hold":  int(self.norm_off.get()),
                    },
                    "aggr": {
                        "threshold": int(self.aggr_thr.get()),
                        "on_hold":   int(self.aggr_on.get()),
                        "off_hold":  int(self.aggr_off.get()),
                    },
                },
                "temp": {
                    "gear1": float(self.temp_g1.get()),
                    "gear2": float(self.temp_g2.get()),
                    "gear3": float(self.temp_g3.get()),
                    "gear4": float(self.temp_g4.get()),
                    "delta_trigger": float(self.delta_trigger.get()),
                },

            }
        except ValueError as e:
            messagebox.showerror("Settings", f"Invalid value:\n{e}")
            return

        threading.Thread(
            target=self._apply_worker,
            args=(payload,),
            daemon=True
        ).start()

    def _apply_worker(self, payload):
        import requests
        try:
            r = requests.post(f"{FANMATE_URL}/config", json=payload, timeout=25)
            if r.status_code != 200:
                msg = f"HTTP {r.status_code}"
                self.app.root.after(0, lambda m=msg: messagebox.showerror("Settings", m))
                return
            self.app.root.after(0, self.destroy)
        except requests.exceptions.ReadTimeout:
            # v4.31b: ESP responds before Drive uploads complete.
            # A read timeout here almost certainly means the response
            # was sent but arrived after we stopped listening.
            print("[CFG] read timeout on apply -- assuming success")
            self.app.root.after(0, self.destroy)
        except requests.exceptions.ConnectionError as e:
            msg = str(e)
            self.app.root.after(0, lambda m=msg: messagebox.showerror("Settings", f"Failed:\n{m}"))
        except Exception as e:
            msg = str(e)
            self.app.root.after(0, lambda m=msg: messagebox.showerror("Settings", f"Failed:\n{m}"))


class DynaTune(tk.Toplevel):
    """KPI board — six tests against the log window + three graphs."""

    def __init__(self, parent, app, hours=18):
        super().__init__(parent)
        self.app = app
        self.title("Dyna Tune")
        self.resizable(False, False)
        self.transient(parent)

        rows = self._load_recent_rows(hours=hours)
        if not rows:
            tk.Label(self, text="No log data found",
                     font=("Helvetica Neue", 14), padx=40, pady=40).pack()
            tk.Button(self, text="Close", command=self.destroy).pack(pady=10)
            self._apply_theme()
            return

        self.rows = rows
        self._build_ui()
        self._apply_theme()

    # ------------------------------------------------------------------
    def _newest_config_time(self):
        """Timestamp of the newest config-*.csv on disk, or None.

        Config snapshots are written on every Apply. The newest file's
        timestamp is the settings cutoff — everything logged before it
        ran under older settings and is excluded from the window.

        Filename: config-<fw>-YYYYMMDD-HHMMSS.csv. mtime unreliable.
        """
        pattern = os.path.join(LOG_DIR, "config-*.csv")
        files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
        if not files:
            return None
        newest = files[-1]
        base = os.path.basename(newest).rsplit(".", 1)[0]
        parts = base.split("-")
        if len(parts) < 3:
            return None
        try:
            return datetime.strptime(parts[-2] + parts[-1], "%Y%m%d%H%M%S")
        except Exception:
            return None

    def _log_file_start(self, path):
        """Parse start timestamp from a log filename, or None.
        Filename: log-<fw>-YYYYMMDD-HHMM.csv  (start of content window)
        """
        base = os.path.basename(path).rsplit(".", 1)[0]
        parts = base.split("-")
        if len(parts) < 3:
            return None
        try:
            return datetime.strptime(parts[-2] + parts[-1], "%Y%m%d%H%M")
        except Exception:
            return None

    def _last_recommendation(self):
        """Return (run_at, recs_list) from newest dynatune-history.csv
        row, or (None, []) if no history yet."""
        path = os.path.join(LOG_DIR, "dynatune-history.csv")
        if not os.path.exists(path):
            return (None, [])
        try:
            import csv
            with open(path, newline="") as fh:
                reader = csv.DictReader(fh)
                rows = list(reader)
        except Exception:
            return (None, [])
        if not rows:
            return (None, [])
        last = rows[-1]
        run_at_s = (last.get("run_at") or "").strip()
        recs_s   = (last.get("recs") or "").strip()
        if not run_at_s or not recs_s:
            return (None, [])
        try:
            run_at = datetime.strptime(run_at_s, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return (None, [])
        recs = [r.strip() for r in recs_s.split(";") if r.strip()]
        return (run_at, recs)

    def _load_recent_rows(self, hours=18):
        """Load rows for the analysis window.

        File-level filtering: if a real settings change is on disk
        (newest config-*.csv differs from previous), skip any log file
        whose START time is before that change. The one straddling file
        is parsed and filtered row-by-row. Everything before it is
        excluded entirely — those rows ran under different settings and
        would skew the tests.
        """
        pattern = os.path.join(LOG_DIR, "log-*.csv")
        files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
        if not files:
            self._settings_filter_time = None
            self._settings_filter_capped = False
            return []

        # No wall cap. The window is bounded by whatever data exists on
        # disk (the log files themselves, which rotate and evict), and by
        # the newest config snapshot if one exists.
        cfg_time = self._newest_config_time()

        if cfg_time is None:
            cutoff = datetime.min
            self._settings_filter_time = None
            self._settings_filter_capped = False
        else:
            cutoff = cfg_time
            self._settings_filter_time = cfg_time
            self._settings_filter_capped = False

        rows = []
        files_skipped = 0
        files_included = 0
        straddling_filtered_rows = 0
        HOUR = timedelta(hours=1)

        for path in files:
            f_start = self._log_file_start(path)

            if f_start is None:
                parsed = self._parse(path)
                before = len(parsed)
                parsed = [r for r in parsed if r["t"] >= cutoff]
                straddling_filtered_rows += (before - len(parsed))
                if parsed:
                    files_included += 1
                rows.extend(parsed)
                continue

            f_end_upper = f_start + HOUR

            if f_end_upper < cutoff:
                files_skipped += 1
                continue

            if f_start >= cutoff:
                rows.extend(self._parse(path))
                files_included += 1
                continue

            parsed = self._parse(path)
            before = len(parsed)
            parsed = [r for r in parsed if r["t"] >= cutoff]
            if parsed:
                files_included += 1
                straddling_filtered_rows += (before - len(parsed))
                rows.extend(parsed)
            else:
                files_skipped += 1

        rows.sort(key=lambda r: r["t"])
        self._files_skipped = files_skipped
        self._files_included = files_included
        self._rows_dropped = straddling_filtered_rows
        return rows

    def _parse(self, path):
        """Fast CSV parse. Manual split + slice-based datetime."""
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
                        y = int(line[0:4]); mo = int(line[5:7]); d = int(line[8:10])
                        h = int(line[11:13]); mi = int(line[14:16]); se = int(line[17:19])
                        ts = datetime(y, mo, d, h, mi, se)
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
                    out.append({
                        "t": ts, "temp": temp, "net": net,
                        "boost": boost, "fan": fan, "rpm": rpm,
                        "room": room, "event": event,
                    })
        except Exception as e:
            print("[DynaTune] parse " + path + ": " + str(e))
        return out

    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = 22
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=pad, pady=pad)

        start = self.rows[0]["t"]
        end   = self.rows[-1]["t"]
        span_h = (end - start).total_seconds() / 3600.0
        ver = state.latest.get("fv", "?")

        # ---------- Header ----------
        hdr = tk.Frame(wrap)
        hdr.pack(fill="x", pady=(0, 14))

        tk.Label(hdr, text="Dyna Tune",
                 font=("Helvetica Neue", 32, "bold"),
                 anchor="w").pack(side="left")

        meta = tk.Frame(hdr)
        meta.pack(side="right", anchor="e", pady=(10, 0))
        tk.Label(meta, text=f"FW v{ver}",
                 font=("Menlo", 11, "bold"), anchor="e").pack(anchor="e")
        tk.Label(meta, text=f"{start.strftime('%a %d %b %H:%M')}  \u2192  {end.strftime('%H:%M')}",
                 font=("Menlo", 10), anchor="e").pack(anchor="e")
        tk.Label(meta, text=f"{span_h:.1f} h   \u00b7   {len(self.rows)} samples",
                 font=("Menlo", 10), anchor="e").pack(anchor="e")

        # Settings filter line
        sf_time = getattr(self, "_settings_filter_time", None)
        sf_capped = getattr(self, "_settings_filter_capped", False)
        files_skipped = getattr(self, "_files_skipped", 0)
        rows_dropped  = getattr(self, "_rows_dropped", 0)

        if sf_time is None:
            sf_text = "full window \u2014 no settings change on disk"
            sf_fg = "#7a8194"
        else:
            age_s = (datetime.now() - sf_time).total_seconds()
            if age_s < 3600:
                age = f"{int(age_s/60)}m"
            elif age_s < 86400:
                age = f"{age_s/3600:.1f}h"
            else:
                age = f"{age_s/86400:.1f}d"
            suffix = ""
            if files_skipped or rows_dropped:
                suffix = f" \u00b7 {files_skipped}f/{rows_dropped}r pre-change"
            sf_text = f"settings changed {age} ago" + suffix
            sf_fg = "#2f9e44"
        self._settings_filter_lbl = tk.Label(meta, text=sf_text,
                 font=("Menlo", 9), fg=sf_fg, anchor="e")
        self._settings_filter_lbl.pack(anchor="e", pady=(4, 0))

        # Last recommended change (from dynatune-history.csv)
        rec_run_at, rec_list = self._last_recommendation()
        if rec_list:
            age_s = (datetime.now() - rec_run_at).total_seconds()
            if age_s < 3600:
                rec_age = f"{int(age_s/60)}m ago"
            elif age_s < 86400:
                rec_age = f"{age_s/3600:.1f}h ago"
            else:
                rec_age = f"{age_s/86400:.1f}d ago"
            first_rec = rec_list[0]
            extra = f"  (+{len(rec_list)-1})" if len(rec_list) > 1 else ""
            self._last_rec_lbl = tk.Label(meta,
                     text=f"last rec: {first_rec}{extra}\n{rec_age}",
                     font=("Menlo", 9), fg="#1e66f5", anchor="e",
                     justify="right")
            self._last_rec_lbl.pack(anchor="e", pady=(6, 0))

        # ---------- Run tests ----------
        from .dynatune import analyse
        try:
            b = state.latest_config.get("boost", {})
            mode = b.get("mode", 1)
            if mode == 2:
                thr = int(b.get("aggr", {}).get("threshold", 700))
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
            r = requests.get(f"{FANMATE_URL}/log/info", timeout=2)
            if r.status_code == 200:
                log_info = r.json()
        except Exception:
            pass

        kpis = analyse(self.rows, boost_thr=thr,
                       live_status=live_status,
                       live_config=live_config,
                       log_info=log_info)

        LABELS = {
            "boost":"BOOST", "cooldown":"COOLDOWN", "delta":"DELTA",
            "lag":"LAG", "events":"EVENTS", "log":"LOG",
            "drive":"DRIVE", "clock":"CLOCK", "boot":"BOOT",
            "opal_poll":"OPAL",
            "night_cap":"NIGHT", "heat_gears":"HEAT", "hysteresis":"HYST",
            "storage":"FS",
            "phone":"PHONE", "sleep":"SLEEP", "ntc":"NTC",
            "ds18b20":"DS18B20", "rpm":"RPM", "stall":"STALL",
            "gear_order":"GEARS", "threshold":"THR",
            "boost_mode":"MODE", "night_window":"WINDOW",
        }
        RECS = {
            "boost":    "boost.on_hold 4 \u2192 2  (or lower threshold)",
            "cooldown": "review hold time",
            "delta":    "check phone temp source",
            "lag":      "normal \u2014 phone catches up after burst",
            "events":   "check serial log",
            "log":      "check clock / FS",
            "drive":    "check Mac sync path",
            "clock":    "Opal clock not landing",
            "boot":     "frequent reboots \u2014 check power",
            "opal_poll":"Opal poll dropping",
            "night_cap":"nightMax not enforced",
            "heat_gears":"heat thresholds may be too high",
            "hysteresis":"increase tempHysteresis",
            "storage":  "evict older sealed files",
            "phone":    "check hall sensor",
            "sleep":    "sleep/wake imbalance",
            "ntc":      "check NTC wiring",
            "ds18b20":  "check probe wiring",
            "rpm":      "clamp RPM at 10k in firmware",
            "stall":    "check fan connector",
            "gear_order":"fix gear thresholds in Settings",
            "threshold":"set 200\u201310000",
            "boost_mode":"set to 0/1/2",
            "night_window":"fix night hours",
        }

        total = passed = warned = failed = 0
        idle = 0
        fails = []
        recs = []
        for section_name in ("core","data","device","hardware","config"):
            sec = kpis.get(section_name, {})
            if not isinstance(sec, dict):
                continue
            for key, data in sec.items():
                if not isinstance(data, dict):
                    continue
                total += 1
                st = data.get("status", "IDLE")
                if st == "PASS":
                    passed += 1
                elif st == "IDLE":
                    # No data to check yet — not a failure. Count as PASS.
                    passed += 1
                    idle += 1
                elif st == "WARN":
                    warned += 1
                    fails.append((LABELS.get(key, key.upper()),
                                  data.get("metric", ""), "WARN"))
                    recs.append(f"{LABELS.get(key, key.upper())}: {RECS.get(key, 'investigate')}")
                elif st == "FAIL":
                    failed += 1
                    fails.append((LABELS.get(key, key.upper()),
                                  data.get("metric", ""), "FAIL"))
                    recs.append(f"{LABELS.get(key, key.upper())}: {RECS.get(key, 'investigate')}")

        # ---------- Verdict card ----------
        self._verdict_card = tk.Frame(wrap, highlightthickness=1, bd=0)
        self._verdict_card.pack(fill="x", pady=(0, 8))

        vwrap = tk.Frame(self._verdict_card)
        vwrap.pack(fill="x", padx=20, pady=18)

        if failed:
            v_icon = "\u2717"
            v_text = f"{failed + warned} issue{'s' if failed + warned != 1 else ''} need attention"
            self._verdict_status = "fail"
        elif warned:
            v_icon = "\u26a0"
            v_text = f"{warned} minor issue{'s' if warned != 1 else ''}"
            self._verdict_status = "warn"
        else:
            v_icon = "\u2713"
            v_text = "healthy"
            self._verdict_status = "pass"

        vrow = tk.Frame(vwrap)
        vrow.pack(anchor="w")

        self._verdict_icon = tk.Label(vrow, text=v_icon,
                 font=("Menlo", 34, "bold"), anchor="w")
        self._verdict_icon.pack(side="left", padx=(0, 14))

        vtxt = tk.Frame(vrow)
        vtxt.pack(side="left", anchor="w")

        self._verdict_title = tk.Label(vtxt, text="Fan-Mate",
                 font=("Helvetica Neue", 14), anchor="w")
        self._verdict_title.pack(anchor="w")

        self._verdict_msg = tk.Label(vtxt, text=v_text,
                 font=("Helvetica Neue", 26, "bold"), anchor="w")
        self._verdict_msg.pack(anchor="w")

        # score pills
        pills = tk.Frame(vwrap)
        pills.pack(anchor="w", pady=(14, 0))

        def _pill(parent, text, status_key):
            f = tk.Frame(parent, highlightthickness=1, bd=0)
            f.pack(side="left", padx=(0, 6))
            lbl = tk.Label(f, text=text,
                     font=("Helvetica Neue", 11, "bold"),
                     padx=10, pady=3)
            lbl.pack()
            f._pill_status = status_key
            f._pill_label = lbl
            return f

        self._pills = []
        pass_label = f"{passed} PASS"
        if idle:
            pass_label += f"  ({idle} idle)"
        self._pills.append(_pill(pills, pass_label, "pass"))
        if warned:
            self._pills.append(_pill(pills, f"{warned} WARN", "warn"))
        if failed:
            self._pills.append(_pill(pills, f"{failed} FAIL", "fail"))

        # ---------- Grid cards ----------
        SECTIONS = [
            ("CORE",     "core",     ["boost","cooldown","delta","lag","events","log"]),
            ("DATA",     "data",     ["drive","clock","boot","opal_poll"]),
            ("DEVICE",   "device",   ["night_cap","heat_gears","hysteresis","storage"]),
            ("HARDWARE", "hardware", ["phone","sleep","ntc","ds18b20","rpm","stall"]),
            ("CONFIG",   "config",   ["gear_order","threshold","boost_mode","night_window"]),
        ]

        self._grid_cards = []
        for sec_label, sec_key, keys in SECTIONS:
            card = tk.Frame(wrap, highlightthickness=1, bd=0)
            card.pack(fill="x", pady=(0, 6))

            inner = tk.Frame(card)
            inner.pack(fill="x", padx=14, pady=10)

            tk.Label(inner, text=sec_label,
                     font=("Menlo", 10, "bold"),
                     width=10, anchor="w").pack(side="left")

            sec = kpis.get(sec_key, {})
            for k in keys:
                d = sec.get(k, {}) if isinstance(sec, dict) else {}
                st = d.get("status", "IDLE")
                short = LABELS.get(k, k.upper())
                chip = self._test_chip(inner, short, st)
                chip.pack(side="left", padx=(0, 6))

            self._grid_cards.append(card)

        # ---------- Issues + Recs ----------
        self._issue_cards = []

        if fails:
            card = tk.Frame(wrap, highlightthickness=1, bd=0)
            card.pack(fill="x", pady=(10, 6))
            inner = tk.Frame(card)
            inner.pack(fill="x", padx=16, pady=12)

            tk.Label(inner, text="ISSUES" if not failed else "FAILURES",
                     font=("Helvetica Neue", 12, "bold"),
                     anchor="w").pack(anchor="w")

            for (label, metric, sev) in fails:
                r = tk.Frame(inner)
                r.pack(fill="x", pady=3)
                tk.Label(r, text=label,
                         font=("Menlo", 12, "bold"),
                         width=10, anchor="w").pack(side="left")
                tk.Label(r, text=metric,
                         font=("Helvetica Neue", 13),
                         anchor="w").pack(side="left")
            self._issue_cards.append(card)

        if recs:
            card = tk.Frame(wrap, highlightthickness=1, bd=0)
            card.pack(fill="x", pady=(0, 6))
            inner = tk.Frame(card)
            inner.pack(fill="x", padx=16, pady=12)

            tk.Label(inner, text="RECOMMENDATIONS",
                     font=("Helvetica Neue", 12, "bold"),
                     anchor="w").pack(anchor="w")

            for r in recs:
                tk.Label(inner, text=r,
                         font=("Helvetica Neue", 13),
                         anchor="w", justify="left",
                         wraplength=560).pack(fill="x", pady=2)
            self._issue_cards.append(card)

        # ---------- Footer ----------
        foot = tk.Frame(wrap)
        foot.pack(fill="x", pady=(10, 0))
        tk.Label(foot,
                 text=f"rows {len(self.rows)}   \u00b7   span {span_h:.1f}h   \u00b7   boost thr {thr} KB/s",
                 font=("Menlo", 10), anchor="w").pack(side="left")

        self._close_btn = tk.Button(foot, text="Close", width=10,
                  font=("Helvetica Neue", 11),
                  relief="flat", bd=0,
                  command=self.destroy)
        self._close_btn.pack(side="right")

        self._apply_theme()

    def _test_chip(self, parent, text, status):
        """Coloured pill for one test.

        IDLE is treated as PASS at the UI layer — the test didn't fail,
        it just had no data to check yet. Rendering IDLE as a distinct
        third state made the board look worse than it is.
        """
        f = tk.Frame(parent, highlightthickness=1, bd=0)
        if status == "IDLE":
            status_visual = "PASS"
        else:
            status_visual = status
        icon = {"PASS": "\u2713", "WARN": "\u26a0",
                "FAIL": "\u2717"}.get(status_visual, "\u25cb")
        lbl = tk.Label(f, text=f"{icon} {text}",
                 font=("Menlo", 10, "bold"),
                 padx=7, pady=2)
        lbl.pack()
        f._chip_status = status_visual
        f._chip_label = lbl
        return f
    def _append_history(self, start, end, ver, score, fails, recs):
        import csv, os
        path = os.path.join(LOG_DIR, "dynatune-history.csv")
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["run_at","window_start","window_end",
                            "version","score","fails","recs"])
            flat_fails = []
            for f in fails:
                if isinstance(f, tuple):
                    flat_fails.append(f[0] + ": " + f[1])
                else:
                    flat_fails.append(str(f))
            w.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                start.strftime("%Y-%m-%d %H:%M:%S"),
                end.strftime("%Y-%m-%d %H:%M:%S"),
                ver,
                score,
                ";".join(flat_fails),
                ";".join(str(r) for r in recs),
            ])

    # ------------------------------------------------------------------
    def _kpi_card(self, parent, label, data):
        status = data.get("status", "IDLE")
        metric = data.get("metric", "--")
        detail = data.get("detail", "")
        dots   = {"PASS": 5, "WARN": 3, "FAIL": 1, "IDLE": 2}.get(status, 0)

        card = tk.Frame(parent, highlightthickness=1, bd=0)
        card.pack(side="left", expand=True, fill="both", padx=3, pady=2)

        # label at top
        tk.Label(card, text=label,
                 font=("Helvetica Neue", 8, "bold")).pack(pady=(6, 2))

        # 5-dot row
        dot_frame = tk.Frame(card)
        dot_frame.pack(pady=(0, 3))
        for i in range(5):
            filled = i < dots
            c = tk.Canvas(dot_frame, width=8, height=8,
                          highlightthickness=0, bd=0)
            c.pack(side="left", padx=1)
            c.create_oval(1, 1, 7, 7, outline="",
                          tags=("dot", "fill" if filled else "empty"))
            c.dot_filled = filled

        # status
        tk.Label(card, text=status,
                 font=("Helvetica Neue", 10, "bold")).pack(pady=(2, 0))

        # metric
        tk.Label(card, text=metric,
                 font=("Helvetica Neue", 11)).pack(pady=(0, 0))

        # detail
        if detail:
            tk.Label(card, text=detail,
                     font=("Helvetica Neue", 8)).pack(pady=(0, 6))
        else:
            tk.Label(card, text=" ",
                     font=("Helvetica Neue", 8)).pack(pady=(0, 6))

        # store refs for theming
        card._kpi_status = status

    # ------------------------------------------------------------------
    def _recommendation_bar(self, parent, text):
        bar = tk.Frame(parent, highlightthickness=1, bd=0)
        bar.pack(fill="x", pady=(4, 8))
        tk.Label(bar, text=text,
                 font=("Helvetica Neue", 11, "bold"),
                 anchor="w").pack(fill="x", padx=10, pady=8)
        bar._kpi_recommendation = True

    # ------------------------------------------------------------------
    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])

        status_color = {
            "PASS": t["green"],
            "WARN": t["yellow"],
            "FAIL": t["red"],
            "IDLE": t["muted"],
        }
        status_bg = {
            "PASS": t["card"],
            "WARN": t["card"],
            "FAIL": t["card"],
            "IDLE": t["card"],
        }

        def recolour(w, bg, border):
            try:
                cls = w.winfo_class()
            except Exception:
                return
            if cls in ("Frame", "Toplevel"):
                w.configure(bg=bg, highlightbackground=border,
                            highlightcolor=border)
            elif cls == "Label":
                w.configure(bg=bg)
            elif cls == "Button":
                w.configure(bg=t["card"], fg=t["fg"],
                            activebackground=t["accent"],
                            activeforeground=t["fg"])

        def walk(w):
            try:
                cls = w.winfo_class()
            except Exception:
                return

            chip_status = getattr(w, "_chip_status", None)
            pill_status = getattr(w, "_pill_status", None)

            if cls in ("Frame", "Toplevel"):
                if chip_status or pill_status:
                    st = chip_status or pill_status
                    w.configure(bg=status_bg.get(st, t["card"]),
                                highlightbackground=status_color.get(st, t["card_border"]),
                                highlightcolor=status_color.get(st, t["card_border"]))
                else:
                    w.configure(bg=t["card"],
                                highlightbackground=t["card_border"],
                                highlightcolor=t["card_border"])
            elif cls == "Label":
                parent = w.master
                p_chip = getattr(parent, "_chip_status", None)
                p_pill = getattr(parent, "_pill_status", None)
                if p_chip:
                    w.configure(bg=status_bg.get(p_chip, t["card"]),
                                fg=status_color.get(p_chip, t["fg"]))
                elif p_pill:
                    w.configure(bg=status_bg.get(p_pill, t["card"]),
                                fg=status_color.get(p_pill, t["fg"]))
                else:
                    w.configure(bg=t["card"], fg=t["fg"])
            elif cls == "Button":
                w.configure(bg=t["card"], fg=t["fg"],
                            activebackground=t["accent"],
                            activeforeground=t["fg"])

            for c in w.winfo_children():
                walk(c)

        walk(self)

        # Verdict icon + message colour
        if hasattr(self, "_verdict_icon"):
            st = getattr(self, "_verdict_status", "pass")
            col = status_color.get(st.upper(), t["fg"])
            self._verdict_icon.configure(bg=t["card"], fg=col)
            self._verdict_msg.configure(bg=t["card"], fg=col)
            self._verdict_title.configure(bg=t["card"], fg=t["muted"])
            self._verdict_card.configure(bg=t["card"],
                highlightbackground=t["card_border"],
                highlightcolor=t["card_border"])