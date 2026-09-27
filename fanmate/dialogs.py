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

        section("🌙", "NIGHT")
        self.night_start = tk.StringVar(value=str(latest_config["night"].get("start", 22)))
        field("Start hour (0-23)", self.night_start)
        self.night_end = tk.StringVar(value=str(latest_config["night"].get("end", 7)))
        field("End hour (0-23)", self.night_end)
        self.night_max = tk.StringVar(value=str(latest_config["night"].get("nightMax", 75)))
        field("Night max (%)", self.night_max)

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
                "night": {
                    "start":    int(self.night_start.get()),
                    "end":      int(self.night_end.get()),
                    "nightMax": int(self.night_max.get()),
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
    """Health check for fan + turbo performance. Reads ALL log files."""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Dyna Tune — Health Check")
        self.resizable(False, False)
        self.transient(parent)

        self._rows = []
        self._files = []
        self._score_colors = []
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
        self._files = files
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
                        net  = float(parts[2])
                        boost = int(parts[3])
                        fan  = int(parts[4])
                        rpm  = int(parts[5])
                    except Exception:
                        continue
                    out.append({
                        "t": ts, "temp": temp, "net": net,
                        "boost": boost, "fan": fan, "rpm": rpm,
                    })
        except Exception as e:
            print(f"[DYNA] parse {path}: {e}")
        return out

    def _score_fan(self):
        rows = self._rows
        issues = []
        score = 10

        fan_on = [r for r in rows if r["fan"] > 0]
        if not fan_on:
            return 10, ["No fan activity in window — nothing to grade"]

        stall_frames = [r for r in rows if r["fan"] > 0 and r["rpm"] == 0]
        if stall_frames:
            score -= min(8, 5 + len(stall_frames) // 10)
            issues.append(f"{len(stall_frames)} frames at fan>0 with rpm=0 — possible stall")

        full_fan = [r for r in rows if r["fan"] >= 95]
        if full_fan:
            peak = max(r["rpm"] for r in full_fan)
            if peak < 2000:
                score -= 4
                issues.append(f"Peak RPM {peak} at 100% fan — very low")
            elif peak < 3500:
                score -= 2
                issues.append(f"Peak RPM {peak} at 100% fan — a bit low")

        if max(r["fan"] for r in rows) < 100 and max(r["net"] for r in rows) > 2000:
            score -= 1
            issues.append("Fan never reached 100% despite heavy traffic")

        pairs = [(r["fan"], r["rpm"]) for r in rows if r["rpm"] > 0]
        if len(pairs) > 20:
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            mx = sum(xs)/len(xs); my = sum(ys)/len(ys)
            num = sum((x-mx)*(y-my) for x,y in pairs)
            dx = (sum((x-mx)**2 for x in xs))**0.5
            dy = (sum((y-my)**2 for y in ys))**0.5
            r = num / (dx*dy) if dx*dy > 0 else 0
            if r < 0.3:
                score -= 2
                issues.append(f"Fan% and RPM weakly correlated (r={r:.2f})")
            elif r < 0.6:
                score -= 1
                issues.append(f"Fan% and RPM loosely correlated (r={r:.2f})")

        return max(0, min(10, score)), issues

    def _score_turbo(self):
        rows = self._rows
        issues = []
        score = 10

        boost_frames = [r for r in rows if r["boost"] > 0]
        max_net = max((r["net"] for r in rows), default=0)

        if not boost_frames:
            if max_net > 700:
                score = 0
                issues.append(f"Traffic peaked at {max_net:.0f} KB/s but boost never fired")
            else:
                issues.append("No load in window — boost untested")
            return score, issues

        gears = [r["boost"] for r in boost_frames]
        max_gear = max(gears)
        peak_net = max(r["net"] for r in rows)
        if max_gear == 1:
            if peak_net > 2000:
                score -= 3
                issues.append(f"Boost only reached gear 1 despite peak {peak_net:.0f} KB/s")
            elif peak_net > 1000:
                score -= 1
                issues.append(f"Boost only reached gear 1 (peak {peak_net:.0f} KB/s — moderate load)")

        changes = 0
        prev = None
        prev_t = None
        for r in rows:
            if prev is not None and r["boost"] != prev:
                if prev_t is not None and (r["t"] - prev_t).total_seconds() < 20:
                    changes += 1
                prev = r["boost"]
                prev_t = r["t"]
            elif prev is None:
                prev = r["boost"]
                prev_t = r["t"]
        if changes > 10:
            score -= 4
            issues.append(f"{changes} rapid gear changes — possible chatter")
        elif changes > 5:
            score -= 2
            issues.append(f"{changes} gear changes close together — mild chatter")

        stuck = 0
        prev = None
        for r in rows:
            if prev and prev["boost"] >= 3 and r["net"] < 200:
                stuck += 1
            prev = r
        if stuck > 20:
            score -= 2
            issues.append(f"Gear stayed ≥3 for {stuck} frames after traffic dropped")

        return max(0, min(10, score)), issues

    def _build_ui(self):
        pad = 16
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=pad, pady=pad)

        span = (self._rows[-1]["t"] - self._rows[0]["t"]).total_seconds() / 60.0
        tk.Label(wrap, text="🩺  Dyna Tune Health Check",
                 font=("Helvetica Neue", 15, "bold")).pack(anchor="w")
        tk.Label(wrap,
                 text=f"{len(self._files)} files  ·  {len(self._rows)} rows  ·  span {span:.0f} min",
                 font=("Helvetica Neue", 10)).pack(anchor="w", pady=(0, 12))

        fan_score, fan_issues = self._score_fan()
        turbo_score, turbo_issues = self._score_turbo()

        self._section(wrap, "🌀 FAN", fan_score, fan_issues)
        self._section(wrap, "🔥 TURBO", turbo_score, turbo_issues)

        total = fan_score + turbo_score
        verdict = "HEALTHY" if total >= 18 else "NEEDS ATTENTION" if total >= 12 else "PROBLEM"
        color_key = "green" if total >= 18 else "orange" if total >= 12 else "red"

        tk.Frame(wrap, height=1).pack(fill="x", pady=8)

        self.total_lbl = tk.Label(wrap,
                                  text=f"🩺  OVERALL: {total}/20  ·  {verdict}",
                                  font=("Helvetica Neue", 14, "bold"))
        self.total_lbl.pack(anchor="w")
        self._total_color = color_key

        tk.Button(wrap, text="Refresh", width=12,
                  font=("Helvetica Neue", 11),
                  command=self._refresh).pack(pady=(14, 0))
        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(pady=(6, 0))

    def _section(self, parent, title, score, issues):
        fr = tk.Frame(parent)
        fr.pack(fill="x", pady=(8, 4))

        score_color = "green" if score >= 9 else "yellow" if score >= 6 else "red"

        head = tk.Frame(fr)
        head.pack(fill="x")
        tk.Label(head, text=title, font=("Helvetica Neue", 13, "bold"),
                 anchor="w").pack(side="left")
        sl = tk.Label(head, text=f"{score}/10",
                      font=("Helvetica Neue", 13, "bold"), anchor="e")
        sl.pack(side="right")
        self._score_colors.append((sl, score_color))

        if not issues:
            tk.Label(fr, text="   ✅ No issues detected",
                     font=("Helvetica Neue", 11), anchor="w").pack(fill="x")
            return

        for issue in issues:
            tk.Label(fr, text="   💡 " + issue,
                     font=("Helvetica Neue", 11), anchor="w",
                     wraplength=560, justify="left").pack(fill="x")

    def _refresh(self):
        for w in self.winfo_children():
            w.destroy()
        self._rows = []
        self._files = []
        self._score_colors = []
        self._load_all()
        if not self._rows:
            tk.Label(self, text="No log files found.",
                     font=("Helvetica Neue", 13), padx=30, pady=30).pack()
            tk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 20))
        else:
            self._build_ui()
        self._apply_theme()

    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        self._theme_recursive(self, t)
        for lbl, ck in self._score_colors:
            lbl.configure(bg=t["bg"], fg=t[ck])
        if hasattr(self, "total_lbl") and hasattr(self, "_total_color"):
            self.total_lbl.configure(bg=t["bg"], fg=t[self._total_color])

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


