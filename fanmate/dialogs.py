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

        latest_config = fetch_config()

        pad = 16
        root = tk.Frame(self)
        root.pack(fill="both", expand=True, padx=pad, pady=pad)

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
        field("Warm (36%)", self.temp_g1)
        self.temp_g2 = tk.StringVar(value=str(latest_config["temp"].get("gear2", 32.0)))
        field("Hot (57%)", self.temp_g2)
        self.temp_g3 = tk.StringVar(value=str(latest_config["temp"].get("gear3", 34.0)))
        field("Hotter (78%)", self.temp_g3)
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

        section("📱", "PHONE")
        self.phone_mode = tk.StringVar(
            value=latest_config["phone"].get("mode", "off"))
        segmented("Mode", self.phone_mode, ["off", "auto"])

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

                "phone": {
                    "mode": self.phone_mode.get(),
                },
            }
        except ValueError as e:
            messagebox.showerror("Settings", f"Invalid value:\n{e}")
            return

        self.destroy()

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
        except Exception as e:
            msg = str(e)
            self.app.root.after(0, lambda m=msg: messagebox.showerror("Settings", f"Failed:\n{m}"))


class DynaTune(tk.Toplevel):
    """
    Improved diagnostic view.
    Three stacked ReportPlots (Network / Fan% / Temp) so thermal lag is obvious.
    """

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
        out = []
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("timestamp"):
                        continue
                    parts = line.split(",")
                    if len(parts) < 6:
                        continue

                    try:
                        ts = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
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

                    out.append({
                        "t": ts, "temp": temp, "net": net,
                        "boost": boost, "fan": fan, "rpm": rpm,
                        "room": room,
                    })
        except Exception as e:
            print(f"[DynaTune] parse {path}: {e}")
        return out

    # ------------------------------------------------------------------
    def _build_ui(self):
        pad = 16
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=pad, pady=pad)

        start = self.rows[0]["t"]
        end   = self.rows[-1]["t"]
        span_h = (end - start).total_seconds() / 3600.0

        tk.Label(wrap,
                 text=f"Dyna Tune  ·  {start.strftime('%a %d %b  %H:%M')} → {end.strftime('%H:%M')}  ·  {span_h:.1f} h",
                 font=("Helvetica Neue", 15, "bold")).pack(anchor="w")
        tk.Label(wrap, text=f"{len(self.rows)} samples",
                 font=("Helvetica Neue", 10)).pack(anchor="w", pady=(0, 10))

        plot_w, plot_h = 620, 110

        net_peak = max((r["net"] for r in self.rows), default=0)
        self.net_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                   y_min=0, y_max=max(2048, net_peak * 1.15),
                                   color_key="blue")
        self.net_plot.pack(pady=(0, 6))
        self.net_plot.set_series(self.rows, "net", "NETWORK (KB/s)")

        self.fan_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                   y_min=0, y_max=100,
                                   color_key="green")
        self.fan_plot.pack(pady=(0, 6))
        self.fan_plot.set_series(self.rows, "fan", "FAN (%)")

        self.temp_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                    y_min=15, y_max=45,
                                    color_key="orange")
        self.temp_plot.pack(pady=(0, 12))
        self.temp_plot.set_series(self.rows, "temp", "TEMP (°C)")

        s = self._analyse()

        summary = tk.Frame(wrap)
        summary.pack(fill="x")

        def col(label, value):
            c = tk.Frame(summary)
            c.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(c, text=label, font=("Helvetica Neue", 9, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(c, text=value, font=("Helvetica Neue", 13, "bold"),
                     anchor="w").pack(fill="x")

        col("PEAK NET",   self._fmt_rate(s['net_peak']))
        col("AVG NET",    self._fmt_rate(s['net_avg']))
        col("TEMP",       f"{s['temp_start']:.1f} → {s['temp_end']:.1f}°C")
        col("TEMP MAX",   f"{s['temp_max']:.1f}°C")
        col("FAN ON",     f"{s['fan_on_pct']:.0f}%")

        lag_frame = tk.Frame(wrap)
        lag_frame.pack(fill="x", pady=(10, 0))
        tk.Label(lag_frame, text=s["lag_text"],
                 font=("Helvetica Neue", 11),
                 anchor="w", justify="left", wraplength=600).pack(anchor="w")

        foot = tk.Frame(wrap)
        foot.pack(fill="x", pady=(12, 0))
        tk.Label(foot,
                 text=f"rows: {len(self.rows)}  ·  span: {span_h:.1f} h  ·  boost thr: {s['boost_thr']} KB/s",
                 font=("Helvetica Neue", 10)).pack(anchor="w")

        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(pady=(14, 0))

    # ------------------------------------------------------------------
    @staticmethod
    def _fmt_rate(kbps):
        if kbps >= 1024:
            return f"{kbps/1024:.2f} MB/s"
        return f"{kbps:.0f} KB/s"

    def _boost_threshold(self):
        try:
            from . import state
            b = state.latest_config.get("boost", {})
            mode = b.get("mode", 1)
            if mode == 1:
                return int(b.get("normal", {}).get("threshold", 700))
            if mode == 2:
                return int(b.get("aggr", {}).get("threshold", 400))
        except Exception:
            pass
        return 700

    def _analyse(self):
        nets  = [r["net"] for r in self.rows]
        fans  = [r["fan"] for r in self.rows]
        temps = [r["temp"] for r in self.rows if r["temp"] > 0]

        net_peak = max(nets) if nets else 0.0
        net_avg  = sum(nets) / len(nets) if nets else 0.0
        temp_max = max(temps) if temps else 0.0

        first = self.rows[0]["temp"]
        last  = self.rows[-1]["temp"]
        temp_start = first if first > 0 else (temps[0] if temps else 0.0)
        temp_end   = last  if last  > 0 else (temps[-1] if temps else 0.0)

        fan_on = sum(1 for f in fans if f > 0)
        fan_on_pct = 100.0 * fan_on / len(fans) if fans else 0.0

        thr = self._boost_threshold()
        high = thr * 2.5
        low  = thr * 0.6

        lag_text = "No clear thermal-lag event found in this window."
        if len(self.rows) > 40:
            for i in range(20, len(self.rows) - 25):
                prev  = [r["net"] for r in self.rows[i-15:i]]
                after = [r["net"] for r in self.rows[i:i+12]]
                if max(prev) > high and max(after) < low:
                    t_drop = self.rows[i]["temp"]
                    later = [r["temp"] for r in self.rows[i:i+35] if r["temp"] > 0]
                    if later:
                        peak = max(later)
                        rise = peak - t_drop
                        if rise >= 1.5:
                            lag_text = (f"Thermal lag detected: after traffic dropped, "
                                        f"temperature still rose {rise:.1f}°C "
                                        f"({t_drop:.1f}° → {peak:.1f}°)")
                            break

        return {
            "net_peak": net_peak,
            "net_avg": net_avg,
            "temp_start": temp_start,
            "temp_end": temp_end,
            "temp_max": temp_max,
            "fan_on_pct": fan_on_pct,
            "lag_text": lag_text,
            "boost_thr": thr,
        }

    # ------------------------------------------------------------------
    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        def walk(w):
            try:
                cls = w.winfo_class()
                if cls in ("Frame", "Toplevel"):
                    w.configure(bg=t["bg"])
                elif cls == "Label":
                    w.configure(bg=t["bg"], fg=t["fg"])
                elif cls == "Button":
                    w.configure(bg=t["card"], fg=t["fg"],
                                activebackground=t["accent"],
                                activeforeground=t["fg"])
            except Exception:
                pass
            for c in w.winfo_children():
                walk(c)
        walk(self)
