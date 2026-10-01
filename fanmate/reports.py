# Fan-Mate report windows

import os
import glob
import tkinter as tk
from datetime import datetime

from .config import *
from . import state
from .helpers import current_theme, local_time_str
from .widgets import ReportPlot


class Report2H(tk.Toplevel):
    """Two-hour report: last two sealed logs, plots + exec summary."""

    _TITLE = "Fan-Mate Report — Last 2 Hours"
    _HEADER = "Last 2 Hours"

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title(self._TITLE)
        self.resizable(False, False)
        self.transient(parent)

        files = self._find_files()
        if not files:
            tk.Label(self, text="No log files found in\n" + LOG_DIR,
                     font=("Helvetica Neue", 13), padx=30, pady=30).pack()
            tk.Button(self, text="Close", command=self.destroy).pack(pady=(0, 20))
            self._apply_theme()
            return

        rows = []
        for path in files:
            rows.extend(self._parse(path))

        summary = self._summarise(rows, files)
        self._build_ui(rows, summary)
        self._apply_theme()

    def _find_files(self):
        return self._find_files_since(2)

    def _find_recent_files(self, n):
        import glob
        pattern = os.path.join(LOG_DIR, "log-*.csv")
        files = [p for p in glob.glob(pattern) if not p.endswith(".part")]
        files.sort()
        return files[-n:]

    def _find_files_since(self, hours):
        """Walk back from newest until cumulative coverage >= hours."""
        import glob
        from datetime import datetime, timedelta
        pattern = os.path.join(LOG_DIR, "log-*.csv")
        files = sorted(p for p in glob.glob(pattern)
                       if not p.endswith(".part"))
        if not files:
            return []
        # Parse the date-time from each filename (after firmware prefix)
        out = []
        cutoff = datetime.now() - timedelta(hours=hours)
        for p in reversed(files):
            out.append(p)
            # Try to derive start time from filename
            try:
                base = os.path.basename(p).rsplit(".", 1)[0]
                parts = base.split("-")
                # log-<fw>-<YYYYMMDD>-<HHMM>.csv
                date_s = parts[-2]
                time_s = parts[-1]
                t = datetime.strptime(date_s + time_s, "%Y%m%d%H%M")
                if t <= cutoff:
                    break
            except Exception:
                break
        out.sort()
        return out

    def _parse(self, path):
        """Parse a sealed CSV via csv.reader — handles quoted fields and
        tolerates 8-column (pre-room_c) and 9-column rows."""
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
                    net = None
                    if len(parts) > 2 and parts[2].strip():
                        try: net = float(parts[2])
                        except: pass
                    try:
                        boost = int(parts[3]) if parts[3].strip() else 0
                        fan   = int(parts[4]) if parts[4].strip() else 0
                        rpm   = int(parts[5]) if parts[5].strip() else 0
                    except Exception:
                        continue
                    room = None
                    if len(parts) > 8 and parts[8].strip():
                        try: room = float(parts[8])
                        except: pass
                    event = parts[6].strip() if len(parts) > 6 else ""
                    out.append({
                        "t": ts, "temp": temp, "net": net,
                        "boost": boost, "fan": fan, "rpm": rpm,
                        "room": room, "event": event,
                    })
        except Exception as e:
            print(f"[REPORT] parse {path}: {e}")
        return out

    def _summarise(self, rows, files):
        if not rows:
            return {}
        temps = [r["temp"] for r in rows if r["temp"] > 0]
        nets  = [r["net"] for r in rows if r["net"] is not None]
        fans  = [r["fan"] for r in rows]
        rpms  = [r["rpm"] for r in rows if r["rpm"] > 0]
        boosts = [r["boost"] for r in rows]

        start = rows[0]["t"]
        end = rows[-1]["t"]
        span_min = (end - start).total_seconds() / 60.0

        # Expected rows: 15s cadence, minus gaps where the device was
        # asleep or the log was paused. Count actual gaps > 30s.
        expected = 0
        if len(rows) >= 2:
            for i in range(1, len(rows)):
                dt = (rows[i]["t"] - rows[i-1]["t"]).total_seconds()
                if dt <= 30:
                    expected += max(1, int(round(dt / 15)))
                else:
                    expected += 1
        missing = max(0, expected - len(rows))

        gear0  = sum(1 for b in boosts if b == 0)
        gear12 = sum(1 for b in boosts if 1 <= b <= 2)
        gear34 = sum(1 for b in boosts if 3 <= b <= 4)
        fan_on = sum(1 for f in fans if f > 0)

        return {
            "start": start, "end": end,
            "span_min": span_min,
            "rows": len(rows),
            "missing": missing,
            "files": [os.path.basename(p) for p in files],
            "temp_first": temps[0] if temps else 0,
            "temp_last":  temps[-1] if temps else 0,
            "temp_min":   min(temps) if temps else 0,
            "temp_max":   max(temps) if temps else 0,
            "temp_avg":   sum(temps)/len(temps) if temps else 0,
            "net_peak":   max(nets) if nets else 0,
            "net_avg":    sum(nets)/len(nets) if nets else 0,
            "fan_peak":   max(fans) if fans else 0,
            "rpm_peak":   max(rpms) if rpms else 0,
            "fan_on_pct": 100*fan_on/len(fans) if fans else 0,
            "gear0_pct":  100*gear0/len(boosts) if boosts else 0,
            "gear12_pct": 100*gear12/len(boosts) if boosts else 0,
            "gear34_pct": 100*gear34/len(boosts) if boosts else 0,
            "gear0_count":  gear0,
            "gear12_count": gear12,
            "gear34_count": gear34,
        }

    def _build_ui(self, rows, s):
        pad = 16
        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=pad, pady=pad)

        tk.Label(wrap, text=f"{self._HEADER}  ·  {s['start'].strftime('%H:%M')}–{s['end'].strftime('%H:%M')}",
                 font=("Helvetica Neue", 15, "bold")).pack(anchor="w")
        tk.Label(wrap, text=f"{len(s['files'])} file(s)",
                 font=("Helvetica Neue", 10)).pack(anchor="w", pady=(0, 10))

        plot_w, plot_h = 620, 120
        self.net_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                   y_min=0, y_max=max(2048, s["net_peak"]*1.1),
                                   color_key="blue")
        self.net_plot.pack(pady=(0, 6))
        self.net_plot.set_series(rows, "net", "NETWORK (KB/s)")

        self.fan_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                   y_min=0, y_max=100,
                                   color_key="green")
        self.fan_plot.pack(pady=(0, 6))
        self.fan_plot.set_series(rows, "fan", "FAN (%)")

        self.temp_plot = ReportPlot(wrap, self.app, plot_w, plot_h,
                                    y_min=15, y_max=45,
                                    color_key="orange")
        self.temp_plot.pack(pady=(0, 12))
        self.temp_plot.set_series(rows, "temp", "TEMP (°C) — phone (orange), room (cyan)",
                                  key2="room", color2_key="blue")

        summary = tk.Frame(wrap)
        summary.pack(fill="x")

        def col(label, value):
            c = tk.Frame(summary)
            c.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(c, text=label, font=("Helvetica Neue", 9, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(c, text=value, font=("Helvetica Neue", 13, "bold"),
                     anchor="w").pack(fill="x")

        col("TEMP START",  f"{s['temp_first']:.1f}°C")
        col("TEMP END",    f"{s['temp_last']:.1f}°C")
        col("TEMP MIN",    f"{s['temp_min']:.1f}°C")
        col("TEMP MAX",    f"{s['temp_max']:.1f}°C")
        col("TEMP AVG",    f"{s['temp_avg']:.1f}°C")

        summary2 = tk.Frame(wrap)
        summary2.pack(fill="x", pady=(10, 0))

        def col2(label, value):
            c = tk.Frame(summary2)
            c.pack(side="left", expand=True, fill="x", padx=6)
            tk.Label(c, text=label, font=("Helvetica Neue", 9, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(c, text=value, font=("Helvetica Neue", 13, "bold"),
                     anchor="w").pack(fill="x")

        col2("NET PEAK",   f"{s['net_peak']:.0f} KB/s")
        col2("NET AVG",    f"{s['net_avg']:.0f} KB/s")
        col2("FAN PEAK",   f"{s['fan_peak']}%")
        col2("RPM PEAK",   f"{s['rpm_peak']}")
        col2("FAN ON",     f"{s['fan_on_pct']:.0f}%")

        foot = tk.Frame(wrap)
        foot.pack(fill="x", pady=(16, 0))
        tk.Label(foot,
                 text=(f"rows: {s['rows']}  ·  missing: {s['missing']}  ·  "
                       f"span: {s['span_min']:.0f} min  ·  "
                       f"gear 0: {s['gear0_count']}  "
                       f"1-2: {s['gear12_count']}  "
                       f"3-4: {s['gear34_count']}"),
                 font=("Helvetica Neue", 10)).pack(anchor="w")

        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(pady=(14, 0))

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


class ReportDaily(Report2H):
    """Daily report — all sealed logs for today (local date)."""

    _TITLE = "Fan-Mate Report — Daily"
    _HEADER = "Today"

    def _find_files(self):
        import glob
        from datetime import date
        today = date.today().strftime("%Y%m%d")
        pattern = os.path.join(LOG_DIR, f"log-*-{today}-*.csv")
        files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
        if not files:
            # nothing yet today — fall back to last 2 files
            files = self._find_recent_files(2)
        return files


class ReportWeekly(Report2H):
    """Weekly report — last 7 days of sealed logs."""

    _TITLE = "Fan-Mate Report — Weekly"
    _HEADER = "Last 7 Days"

    def _find_files(self):
        import glob
        from datetime import date, timedelta
        days = [(date.today() - timedelta(days=i)).strftime("%Y%m%d")
                for i in range(7)]
        files = []
        for d in days:
            pattern = os.path.join(LOG_DIR, f"log-*-{d}-*.csv")
            files.extend(p for p in glob.glob(pattern)
                         if not p.endswith(".part"))
        files.sort()
        if not files:
            files = self._find_recent_files(2)
        return files

