# Fan-Mate — settings change history + recommendations

import os
import csv
import glob
from datetime import datetime

import tkinter as tk

from .config import LOG_DIR, FANMATE_URL
from . import state


def _parse_config(path):
    """Return {key: value} from a config-*.csv, or {} if unreadable."""
    out = {}
    try:
        with open(path) as fh:
            for line in fh:
                parts = line.strip().split(",", 2)
                if len(parts) == 3 and parts[0] != "timestamp":
                    out[parts[1]] = parts[2]
    except Exception:
        pass
    return out


def _config_time(path):
    """Parse timestamp from filename config-vX.YY-YYYYMMDD-HHMMSS.csv."""
    base = os.path.basename(path).rsplit(".", 1)[0]
    parts = base.split("-")
    if len(parts) < 3:
        return None
    try:
        return datetime.strptime(parts[-2] + parts[-1], "%Y%m%d%H%M%S")
    except Exception:
        return None


def _dynatune_runs():
    """Return list of dicts from dynatune-history.csv, oldest first."""
    path = os.path.join(LOG_DIR, "dynatune-history.csv")
    if not os.path.exists(path):
        return []
    out = []
    try:
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                try:
                    when = datetime.strptime(row.get("run_at", ""),
                                             "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
                out.append({
                    "when": when,
                    "recs": [r.strip() for r in
                             (row.get("recs") or "").split(";") if r.strip()],
                    "fails": [f.strip() for f in
                              (row.get("fails") or "").split(";") if f.strip()],
                    "score": row.get("score", ""),
                })
    except Exception:
        pass
    out.sort(key=lambda x: x["when"])
    return out


def collect_changes():
    """Return (changes, runs).

    changes: list of dicts
      when, key, old, new, reason (str|None), rec_used (str|None)

    Only real changes (values differ from previous config).
    """
    pattern = os.path.join(LOG_DIR, "config-*.csv")
    files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
    runs = _dynatune_runs()
    changes = []

    prev = None
    for path in files:
        cur = _parse_config(path)
        if not cur:
            continue
        when = _config_time(path)

        # Skip initial-state entirely — handled separately by
        # current_settings() so the changes list only contains real diffs.

        if prev is not None and when is not None:
            # Only diff keys that exist in BOTH files. Schema changes
            # (keys added or removed between firmware versions) are not
            # user-driven settings changes, so don't list them.
            for key in sorted(set(prev) & set(cur)):
                old = prev.get(key, "")
                new = cur.get(key, "")
                if old == new:
                    continue
                reason = None
                rec_used = None
                for run in reversed(runs):
                    if run["when"] >= when:
                        continue
                    short = key.split(".")[-1]
                    for rec in run["recs"]:
                        if short in rec or key in rec:
                            reason = f"DynaTune at {run['when'].strftime('%H:%M')}"
                            rec_used = rec
                            break
                    if reason:
                        break
                changes.append({
                    "when": when, "key": key,
                    "old": old, "new": new,
                    "reason": reason, "rec_used": rec_used,
                })
        prev = cur

    return changes, runs


def current_settings():
    """Newest config-*.csv as {key: value}, or None if no files."""
    pattern = os.path.join(LOG_DIR, "config-*.csv")
    files = sorted(p for p in glob.glob(pattern) if not p.endswith(".part"))
    if not files:
        return None
    path = files[-1]
    vals = _parse_config(path)
    if not vals:
        return None
    return {"when": _config_time(path), "values": vals}


def current_recommendations():
    """Newest DynaTune run's recs, with count of consecutive repeats."""
    runs = _dynatune_runs()
    if not runs:
        return None
    newest = runs[-1]
    recs = newest["recs"]
    if not recs:
        return {"when": newest["when"], "recs": [], "streak": 0}
    streak = 1
    for run in reversed(runs[:-1]):
        if set(run["recs"]) & set(recs):
            streak += 1
        else:
            break
    return {"when": newest["when"], "recs": recs, "streak": streak}


class ChangelogWindow(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Fan-Mate Settings History")
        self.resizable(True, True)
        self.transient(parent)
        self.geometry("720x600")

        wrap = tk.Frame(self)
        wrap.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(wrap, text="Settings History",
                 font=("Helvetica Neue", 22, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(wrap, text="Every settings change, and the recommendation behind it.",
                 font=("Helvetica Neue", 12),
                 anchor="w").pack(fill="x", pady=(0, 16))

        changes, runs = collect_changes()
        snap = current_settings()

        # --- Current settings snapshot ---
        if snap:
            when_s = snap["when"].strftime("%a %d %b  %H:%M") if snap["when"] else "?"
            tk.Label(wrap, text=f"CURRENT SETTINGS  ·  applied {when_s}",
                     font=("Helvetica Neue", 12, "bold"),
                     anchor="w").pack(fill="x", pady=(0, 6))

            grid = tk.Frame(wrap)
            grid.pack(fill="x", pady=(0, 18))

            for i, key in enumerate(sorted(snap["values"])):
                col = i % 2
                row = i // 2
                cell = tk.Frame(grid)
                cell.grid(row=row, column=col, sticky="w", padx=(0, 24), pady=1)
                tk.Label(cell, text=key,
                         font=("Menlo", 10),
                         width=24, anchor="w").pack(side="left")
                tk.Label(cell, text=str(snap["values"][key]),
                         font=("Menlo", 10, "bold"),
                         anchor="w").pack(side="left")

            tk.Frame(wrap, height=1, bg="#d8dde8").pack(fill="x", pady=(4, 0))

        # --- Changes ---
        tk.Label(wrap, text=f"CHANGES  ({len(changes)})",
                 font=("Helvetica Neue", 12, "bold"),
                 anchor="w").pack(fill="x", pady=(16, 6))

        if not changes:
            tk.Label(wrap, text="none yet",
                     font=("Helvetica Neue", 12),
                     anchor="w").pack(fill="x", pady=(0, 12))
        else:
            for ch in reversed(changes):
                row = tk.Frame(wrap)
                row.pack(fill="x", pady=3)

                when = ch["when"].strftime("%a %d %b  %H:%M") if ch["when"] else "?"
                tk.Label(row, text=when,
                         font=("Menlo", 11, "bold"),
                         width=22, anchor="w").pack(side="left")

                tk.Label(row, text=ch["key"],
                         font=("Menlo", 11),
                         width=24, anchor="w").pack(side="left")

                tk.Label(row, text=f"{ch['old']}  →  {ch['new']}",
                         font=("Menlo", 11),
                         anchor="w").pack(side="left")

                if ch["reason"]:
                    tk.Label(row, text=f"  ({ch['reason']})",
                             font=("Menlo", 10),
                             anchor="w").pack(side="left")

        tk.Frame(wrap, height=1, bg="#d8dde8").pack(fill="x", pady=(20, 0))

        recs = current_recommendations()
        if recs and recs["recs"]:
            tk.Label(wrap, text="CURRENT RECOMMENDATIONS",
                     font=("Helvetica Neue", 12, "bold"),
                     anchor="w").pack(fill="x", pady=(16, 6))

            age_s = (datetime.now() - recs["when"]).total_seconds()
            if age_s < 3600:
                age = f"{int(age_s/60)}m ago"
            elif age_s < 86400:
                age = f"{age_s/3600:.1f}h ago"
            else:
                age = f"{age_s/86400:.1f}d ago"

            streak = recs["streak"]
            note = f"from DynaTune {age}"
            if streak > 1:
                note += f"  ·  {streak} runs in a row"

            tk.Label(wrap, text=note,
                     font=("Menlo", 10),
                     anchor="w").pack(fill="x", pady=(0, 6))

            for r in recs["recs"]:
                tk.Label(wrap, text="  ⚠  " + r,
                         font=("Helvetica Neue", 13),
                         anchor="w", justify="left",
                         wraplength=660).pack(fill="x", pady=2)
        else:
            tk.Label(wrap, text="No outstanding recommendations",
                     font=("Helvetica Neue", 12),
                     fg="#2f9e44", anchor="w").pack(fill="x", pady=(16, 0))

        tk.Button(wrap, text="Close", width=12,
                  font=("Helvetica Neue", 11),
                  command=self.destroy).pack(pady=(20, 0))

        self._apply_theme()

    def _apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["bg"])
        for w in self.winfo_children():
            self._walk(w, t)

    def _walk(self, w, t):
        try:
            cls = w.winfo_class()
        except Exception:
            return
        if cls in ("Frame", "Toplevel"):
            w.configure(bg=t["bg"])
        elif cls == "Label":
            if w.cget("fg") not in (t["green"], "#2f9e44"):
                w.configure(bg=t["bg"], fg=t["fg"])
        elif cls == "Button":
            w.configure(bg=t["card"], fg=t["fg"],
                        activebackground=t["accent"], activeforeground=t["fg"])
        for c in w.winfo_children():
            self._walk(c, t)
