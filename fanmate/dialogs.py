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
        try:
            r = requests.post(f"{FANMATE_URL}/config", json=payload, timeout=10)
            if r.status_code != 200:
                msg = f"HTTP {r.status_code}"
                self.app.root.after(0, lambda m=msg: messagebox.showerror("Settings", m))
            else:
                self.app.root.after(0, self.destroy)
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
    def _load_recent_rows(self, hours=18):
        pattern = os.path.join(LOG_DIR, "log-*.csv")
        files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
        if not files:
            return []
        cutoff = datetime.now() - timedelta(hours=hours)
        rows = []
        for path in files[-18:]:
            rows.extend(self._parse(path))
        rows = [r for r in rows if r["t"] >= cutoff]
        rows.sort(key=lambda r: r["t"])
        return rows

    def _parse(self, path):
        """Parse via csv.reader. Tolerates 8-col (pre-room_c) and 9-col rows."""
        import csv
        out = []
        try:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                for parts in reader:
                    if not parts or len(parts) < 6:
                        continue
                    if parts[0].strip() == "timestamp" or parts[0].startswith("#"):
                        continue
                    try:
                        ts = datetime.strptime(parts[0].strip(), "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        continue
                    try:
                        temp = float(parts[1])
                    except Exception:
                        continue
                    try: net = float(parts[2]) if parts[2].strip() else 0.0
                    except Exception: net = 0.0
                    try: boost = int(parts[3]) if parts[3].strip() else 0
                    except Exception: boost = 0
                    try: fan = int(parts[4]) if parts[4].strip() else 0
                    except Exception: fan = 0
                    try: rpm = int(parts[5]) if parts[5].strip() else 0
                    except Exception: rpm = 0
                    try:
                        room = float(parts[8]) if len(parts) > 8 and parts[8].strip() else None
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
            print(f"[DynaTune] parse {path}: {e}")
        return out

    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = 20
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=pad, pady=pad)

        start = self.rows[0]["t"]
        end   = self.rows[-1]["t"]
        span_h = (end - start).total_seconds() / 3600.0
        ver = state.latest.get("fv", "?")

        tk.Label(wrap,
                 text="Dyna Tune",
                 font=("Helvetica Neue", 22, "bold")).pack(anchor="w")
        tk.Label(wrap,
                 text=f"v{ver}  ·  {start.strftime('%a %d %b  %H:%M')} → {end.strftime('%H:%M')}  ·  {span_h:.1f} h  ·  {len(self.rows)} samples",
                 font=("Helvetica Neue", 12)).pack(anchor="w", pady=(2, 16))

        # ---------- run tests ----------
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

        # Collect failures + recommendations across sections
        fails = []
        recs = []
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
            "boost":    "boost.on_hold 4 → 2  (or lower threshold)",
            "cooldown": "review hold time",
            "delta":    "check phone temp source",
            "lag":      "normal — phone catches up after burst",
            "events":   "check serial log",
            "log":      "check clock / FS",
            "drive":    "check Mac sync path",
            "clock":    "Opal clock not landing",
            "boot":     "frequent reboots — check power",
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
            "threshold":"set 200–10000",
            "boost_mode":"set to 0/1/2",
            "night_window":"fix night hours",
        }

        total = 0
        passed = 0
        warned = 0
        failed = 0
        idle = 0
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
                elif st == "WARN":
                    warned += 1
                    label = LABELS.get(key, key.upper())
                    metric = data.get("metric", "")
                    fails.append((label, metric, "WARN"))
                    recs.append(f"{label}: {RECS.get(key, 'investigate')}")
                elif st == "FAIL":
                    failed += 1
                    label = LABELS.get(key, key.upper())
                    metric = data.get("metric", "")
                    fails.append((label, metric, "FAIL"))
                    recs.append(f"{label}: {RECS.get(key, 'investigate')}")
                else:
                    idle += 1

        parts = [f"{passed} PASS"]
        if warned: parts.append(f"{warned} WARN")
        if failed: parts.append(f"{failed} FAIL")
        if idle:   parts.append(f"{idle} IDLE")
        score_str = "  ·  ".join(parts)

        # ---------- SCORE ----------
        # ---------- SCORE (hero) ----------
        score_frame = tk.Frame(wrap)
        score_frame.pack(fill="x", pady=(0, 6))
        if failed:
            hero_color = "#d20f39"
        elif warned:
            hero_color = "#d99a00"
        else:
            hero_color = "#2f9e44"
        tk.Label(score_frame, text=score_str,
                 font=("Helvetica Neue", 28, "bold"),
                 fg=hero_color, anchor="w").pack(side="left")

        # divider
        tk.Frame(wrap, height=1, bg="#d8dde8").pack(fill="x", pady=(14, 0))

        # ---------- FAILURES ----------
        head = tk.Frame(wrap)
        head.pack(fill="x", pady=(14, 6))
        fail_header_color = "#d20f39" if failed else ("#d99a00" if warned else "#2f9e44")
        tk.Label(head, text="FAILURES",
                 font=("Helvetica Neue", 13, "bold"),
                 fg=fail_header_color, anchor="w").pack(side="left")
        tk.Label(head, text=f"  ({len(fails)})",
                 font=("Helvetica Neue", 13),
                 fg=fail_header_color, anchor="w").pack(side="left")

        if not fails:
            tk.Label(wrap, text="none — everything passing",
                     font=("Helvetica Neue", 14),
                     fg="#2f9e44", anchor="w").pack(fill="x", pady=(0, 8))
        else:
            for (label, metric, sev) in fails:
                row = tk.Frame(wrap)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=label,
                         font=("Menlo", 13, "bold"),
                         fg="#d20f39" if sev == "FAIL" else "#d99a00",
                         width=10, anchor="w").pack(side="left")
                tk.Label(row, text=metric,
                         font=("Helvetica Neue", 14),
                         anchor="w").pack(side="left")

        # divider
        tk.Frame(wrap, height=1, bg="#d8dde8").pack(fill="x", pady=(14, 0))

        # ---------- RECOMMENDATIONS ----------
        head2 = tk.Frame(wrap)
        head2.pack(fill="x", pady=(14, 6))
        tk.Label(head2, text="RECOMMENDATIONS",
                 font=("Helvetica Neue", 13, "bold"),
                 fg="#1e66f5", anchor="w").pack(side="left")
        tk.Label(head2, text=f"  ({len(recs)})",
                 font=("Helvetica Neue", 13),
                 fg="#1e66f5", anchor="w").pack(side="left")

        if not recs:
            tk.Label(wrap, text="none — system healthy",
                     font=("Helvetica Neue", 14),
                     fg="#2f9e44", anchor="w").pack(fill="x", pady=(0, 8))
        else:
            for r in recs:
                tk.Label(wrap, text=r,
                         font=("Helvetica Neue", 14),
                         anchor="w", justify="left",
                         wraplength=460).pack(fill="x", pady=2)

        # ---------- footer ----------
        tk.Label(wrap,
                 text=f"rows: {len(self.rows)}  ·  span: {span_h:.1f} h  ·  boost thr: {thr} KB/s",
                 font=("Helvetica Neue", 10)).pack(anchor="w", pady=(20, 4))

        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 12),
                  command=self.destroy).pack(pady=(10, 0))

        # ---------- append to history ----------
        try:
            self._append_history(start, end, ver, score_str, fails, recs)
        except Exception as e:
            print(f"[DynaTune] history append failed: {e}")

    # ------------------------------------------------------------------
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

        def walk(w):
            try:
                cls = w.winfo_class()
            except Exception:
                return
            if cls in ("Frame", "Toplevel"):
                if getattr(w, "_kpi_recommendation", False):
                    w.configure(bg=t["yellow"], highlightbackground=t["yellow"])
                else:
                    w.configure(bg=t["bg"], highlightbackground=t["card_border"])
            elif cls == "Label":
                if getattr(w.master, "_kpi_recommendation", False):
                    w.configure(bg=t["yellow"], fg=t["bg"])
                else:
                    w.configure(bg=t["bg"], fg=t["fg"])
            elif cls == "Canvas":
                filled = getattr(w, "dot_filled", None)
                if filled is True:
                    # colour matches parent's status
                    status = getattr(w.master.master, "_kpi_status", "IDLE")
                    w.configure(bg=t["bg"])
                    w.itemconfig("fill", fill=status_color.get(status, t["muted"]))
                elif filled is False:
                    w.configure(bg=t["bg"])
                    w.itemconfig("fill", fill=t["card_border"])
            elif cls == "Button":
                w.configure(bg=t["card"], fg=t["fg"],
                            activebackground=t["accent"], activeforeground=t["fg"])
            for c in w.winfo_children():
                walk(c)
        walk(self)
