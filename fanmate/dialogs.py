import threading
import os
import requests
from datetime import datetime

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
        self.temp_warn = tk.StringVar(value=str(latest_config["temp"].get("warning", 32.0)))
        field("Warning (°C)", self.temp_warn)
        self.temp_panic = tk.StringVar(value=str(latest_config["temp"].get("panic", 34.0)))
        field("Panic (°C)", self.temp_panic)
        self.temp_kill = tk.StringVar(value=str(latest_config["temp"].get("kill", 36.0)))
        field("Kill (°C)", self.temp_kill)

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
                    "warning": float(self.temp_warn.get()),
                    "panic":   float(self.temp_panic.get()),
                    "kill":    float(self.temp_kill.get()),
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
    """Traffic and phone temp on one time axis — dual y-axis overlay."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Dyna Tune")
        self.resizable(False, False)
        self.transient(parent)

        self._rows = []
        self._load_all()

        if not self._rows:
            tk.Label(self, text="No log files found in\n" + LOG_DIR,
                     font=("Helvetica Neue", 13), padx=30, pady=30).pack()
            tk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 20))
            self._apply_theme()
            return

        self._build_ui()
        self._apply_theme()

    def _load_all(self):
        import glob
        pattern = os.path.join(LOG_DIR, "log-*.csv")
        files = [p for p in glob.glob(pattern) if not p.endswith(".part")]
        files.sort()
        for path in files:
            self._rows.extend(self._parse(path))
        self._rows.sort(key=lambda r: r["t"])

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
                    net = None
                    if len(parts) > 2 and parts[2].strip():
                        try: net = float(parts[2])
                        except: pass
                    out.append({"t": ts, "temp": temp, "net": net})
        except Exception as e:
            print(f"[DYNA] parse {path}: {e}")
        return out

    def _build_ui(self):
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        t0 = self._rows[0]["t"]
        t1 = self._rows[-1]["t"]
        span_min = (t1 - t0).total_seconds() / 60.0

        tk.Label(wrap, text="🎛️  Dyna Tune",
                 font=("Helvetica Neue", 15, "bold")).pack(anchor="w")
        tk.Label(wrap,
                 text=f"{t0.strftime('%a %d %b')}  ·  "
                      f"{t0.strftime('%H:%M')} → {t1.strftime('%H:%M')}  ·  "
                      f"{span_min/60:.1f} h",
                 font=("Helvetica Neue", 10)).pack(anchor="w", pady=(0, 12))

        plot_w, plot_h = 760, 320
        self.canvas = tk.Canvas(wrap, width=plot_w, height=plot_h,
                                 highlightthickness=1, bd=0)
        self.canvas.pack(pady=(0, 12))
        self._draw(plot_w, plot_h)

        # Summary — 5 numbers, two lines
        nets = [r["net"] for r in self._rows if r["net"] is not None]
        temps = [r["temp"] for r in self._rows if r["temp"] > 0]

        peak_net = max(nets) if nets else 0
        avg_net  = sum(nets)/len(nets) if nets else 0
        temp_first = temps[0] if temps else 0
        temp_last  = temps[-1] if temps else 0
        temp_max   = max(temps) if temps else 0

        def fmt_rate(v):
            if v >= 1024:
                return f"{v/1024:.2f} MB/s"
            return f"{v:.0f} KB/s"

        row1 = tk.Frame(wrap)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text=f"Peak net:  {fmt_rate(peak_net)}",
                 font=("Helvetica Neue", 11), anchor="w").pack(side="left", padx=(0, 30))
        tk.Label(row1, text=f"Avg net:  {fmt_rate(avg_net)}",
                 font=("Helvetica Neue", 11), anchor="w").pack(side="left")

        row2 = tk.Frame(wrap)
        row2.pack(fill="x", pady=2)
        arrow = "▲" if temp_last > temp_first + 0.1 else ("▼" if temp_last < temp_first - 0.1 else "▬")
        tk.Label(row2,
                 text=f"Temp:  {temp_first:.1f} → {temp_last:.1f}°C  {arrow}",
                 font=("Helvetica Neue", 11), anchor="w").pack(side="left", padx=(0, 30))
        tk.Label(row2, text=f"Max:  {temp_max:.1f}°C",
                 font=("Helvetica Neue", 11), anchor="w").pack(side="left")

        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(pady=(14, 0))

    def _draw(self, w, h):
        t = self.app.theme
        c = self.canvas
        c.configure(bg=t["card"])
        c.delete("all")

        pad_l, pad_r, pad_t, pad_b = 60, 60, 20, 30
        pw = w - pad_l - pad_r
        ph = h - pad_t - pad_b
        n = len(self._rows)

        nets = [r["net"] for r in self._rows if r["net"] is not None]
        temps = [r["temp"] for r in self._rows if r["temp"] > 0]

        if not nets: nets = [0]
        if not temps: temps = [0]

        # Net axis (left)
        net_lo, net_hi = 0, max(nets) * 1.1
        if net_hi < 1: net_hi = 1
        net_rng = net_hi - net_lo

        # Temp axis (right)
        temp_lo = min(temps) - 1
        temp_hi = max(temps) + 1
        if temp_hi - temp_lo < 3:
            m = (temp_hi + temp_lo) / 2
            temp_lo, temp_hi = m - 1.5, m + 1.5
        temp_rng = temp_hi - temp_lo

        # --- Horizontal grid ---
        for i in range(5):
            y = pad_t + (i / 4) * ph
            c.create_line(pad_l, y, w - pad_r, y, fill=t["grid"], width=1)

            # Left axis: net
            v = net_hi - (i / 4) * net_rng
            if v >= 1024:
                ltxt = f"{v/1024:.1f}M"
            else:
                ltxt = f"{v:.0f}K"
            c.create_text(pad_l - 6, y, text=ltxt, fill=t["blue"],
                          font=("Helvetica Neue", 9), anchor="e")

            # Right axis: temp
            tv = temp_hi - (i / 4) * temp_rng
            c.create_text(w - pad_r + 6, y, text=f"{tv:.0f}",
                          fill=t["orange"],
                          font=("Helvetica Neue", 9), anchor="w")

        # --- Axis labels ---
        c.create_text(pad_l - 6, pad_t - 8, text="NET", fill=t["blue"],
                      font=("Helvetica Neue", 9, "bold"), anchor="e")
        c.create_text(w - pad_r + 6, pad_t - 8, text="°C", fill=t["orange"],
                      font=("Helvetica Neue", 9, "bold"), anchor="w")

        # --- Net line (blue) ---
        net_pts = []
        for i, r in enumerate(self._rows):
            if r["net"] is None: continue
            x = pad_l + (i / max(1, n - 1)) * pw
            y = pad_t + ph - ((r["net"] - net_lo) / net_rng) * ph
            net_pts.extend([x, y])
        if len(net_pts) >= 4:
            c.create_line(*net_pts, fill=t["blue"], width=2,
                          capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # --- Temp line (orange) ---
        temp_pts = []
        for i, r in enumerate(self._rows):
            if r["temp"] <= 0: continue
            x = pad_l + (i / max(1, n - 1)) * pw
            y = pad_t + ph - ((r["temp"] - temp_lo) / temp_rng) * ph
            temp_pts.extend([x, y])
        if len(temp_pts) >= 4:
            c.create_line(*temp_pts, fill=t["orange"], width=2,
                          capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # --- X-axis time labels ---
        if n >= 2:
            t0 = self._rows[0]["t"]
            t1 = self._rows[-1]["t"]
            for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
                x = pad_l + frac * pw
                tt = t0 + (t1 - t0) * frac
                anchor = "n" if frac in (0.0, 1.0) else "n"
                c.create_text(x, h - 4, text=tt.strftime("%H:%M"),
                              fill=t["muted"],
                              font=("Helvetica Neue", 9), anchor=anchor)

    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        self._theme_recursive(self, t)

    def _theme_recursive(self, w, t):
        try:
            cls = w.winfo_class()
        except Exception:
            return
        if cls in ("Frame", "Toplevel"):
            w.configure(bg=t["bg"])
        elif cls == "Label":
            w.configure(bg=t["bg"], fg=t["fg"])
        elif cls == "Button":
            w.configure(bg=t["card"], fg=t["fg"],
                        activebackground=t["accent"], activeforeground=t["fg"])
        for c in w.winfo_children():
            self._theme_recursive(c, t)
