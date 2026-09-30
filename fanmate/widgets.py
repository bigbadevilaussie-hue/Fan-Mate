# Fan-Mate GUI widgets

import tkinter as tk
from collections import deque

from .config import *
from .state import (
    FONT_TITLE,
    FONT_SECTION,
    FONT_BIG,
    FONT_VALUE,
    FONT_LABEL,
    FONT_TINY,
)
from . import state
from .helpers import current_theme


class Card(tk.Frame):
    def __init__(self, parent, app, **kw):
        super().__init__(parent, highlightthickness=1, bd=0, **kw)
        self.app = app
        self.apply_theme()

    def apply_theme(self):
        t = self.app.theme
        self.configure(bg=t["card"],
                       highlightbackground=t["card_border"],
                       highlightcolor=t["card_border"])


class Graph(tk.Canvas):
    def __init__(self, parent, app, y_min=None, y_max=None, w=380, h=130):
        super().__init__(parent, width=w, height=h, highlightthickness=0, bd=0)
        self.app = app
        self.y_min, self.y_max = y_min, y_max
        self.w, self.h = w, h
        self.pad_l, self.pad_r, self.pad_t, self.pad_b = 30, 8, 8, 8
        self.data = deque([None] * HIST_LEN, maxlen=HIST_LEN)
        self.trigger = None
        self.apply_theme()

    def apply_theme(self):
        self.configure(bg=self.app.theme["card"])

    def set_data(self, d):
        self.data = d
        self.redraw()

    def redraw(self):
        t = self.app.theme
        self.delete("all")
        self.configure(bg=t["card"])
        pts = [p for p in self.data if p is not None]
        pw = self.w - self.pad_l - self.pad_r
        ph = self.h - self.pad_t - self.pad_b
        if self.y_min is not None and self.y_max is not None:
            lo, hi = self.y_min, self.y_max
        elif pts:
            lo, hi = min(pts), max(pts)
            if hi - lo < 2:
                m = (hi + lo) / 2
                lo, hi = m - 1, m + 1
            lo -= 0.5; hi += 0.5
        else:
            lo, hi = -1, 1
        rng = (hi - lo) or 1
        for i in range(5):
            v = hi - (i / 4) * rng
            y = self.pad_t + (i / 4) * ph
            self.create_line(self.pad_l, y, self.w - self.pad_r, y, fill=t["grid"], width=1)
            self.create_text(self.pad_l - 5, y, text=f"{v:.0f}", fill=t["muted"], font=FONT_TINY, anchor="e")
        if self.trigger is not None and lo <= self.trigger <= hi:
            ty = self.pad_t + ph - ((self.trigger - lo) / rng) * ph
            self.create_line(self.pad_l, ty, self.w - self.pad_r, ty, fill=t["red"], width=1, dash=(4, 3))
            self.create_text(self.w - self.pad_r - 4, ty - 6, text=f"{self.trigger:.0f}", fill=t["red"], font=FONT_TINY, anchor="e")
        if not pts:
            self.create_text(self.w / 2, self.h / 2, text="waiting…", fill=t["muted"], font=FONT_TINY)
            return
        first = next((i for i, p in enumerate(self.data) if p is not None), 0)
        trim = [p for p in list(self.data)[first:] if p is not None]
        m = len(trim)
        if m < 1:
            return
        coords = []
        for i, v in enumerate(trim):
            x = self.pad_l + pw if m == 1 else self.pad_l + (i / (m - 1)) * pw
            y = self.pad_t + ph - ((v - lo) / rng) * ph
            coords.extend([x, y])
        if m >= 2:
            poly = [self.pad_l, self.pad_t + ph] + coords + [self.pad_l + pw, self.pad_t + ph]
            self.create_polygon(poly, fill=t["fill"], outline="")
            self.create_line(*coords, fill=t["blue"], width=2, capstyle=tk.ROUND, joinstyle=tk.ROUND)
        lx, ly = coords[-2], coords[-1]
        self.create_oval(lx - 4, ly - 4, lx + 4, ly + 4, fill=t["blue"], outline=t["card"], width=2)


class ReportPlot(tk.Canvas):
    """Simple line plot with title and x-axis time labels.
    Optionally plots a second series (e.g. room temp behind phone temp)."""

    def __init__(self, parent, app, w, h, y_min, y_max, color_key):
        super().__init__(parent, width=w, height=h, highlightthickness=1, bd=0)
        self.app = app
        self.w, self.h = w, h
        self.y_min, self.y_max = y_min, y_max
        self.color_key = color_key
        self.pad_l, self.pad_r, self.pad_t, self.pad_b = 46, 10, 20, 26
        self.series = []
        self.series2 = None
        self.color2_key = None
        self.label = ""
        self._t0 = None
        self._t1 = None

    def set_series(self, rows, key, label, key2=None, color2_key=None):
        self.series = [r.get(key) for r in rows]
        if key2 is not None:
            self.series2 = [r.get(key2) for r in rows]
            self.color2_key = color2_key or "blue"
        else:
            self.series2 = None
            self.color2_key = None
        self.label = label
        if rows:
            self._t0 = rows[0].get("t")
            self._t1 = rows[-1].get("t")
        self.redraw()

    def redraw(self):
        t = self.app.theme
        self.delete("all")
        self.configure(bg=t["card"],
                       highlightbackground=t["card_border"])
        if not self.series:
            return

        pw = self.w - self.pad_l - self.pad_r
        ph = self.h - self.pad_t - self.pad_b
        lo, hi = self.y_min, self.y_max
        rng = (hi - lo) or 1
        n = len(self.series)

        for i in range(4):
            v = hi - (i / 3) * rng
            y = self.pad_t + (i / 3) * ph
            self.create_line(self.pad_l, y, self.w - self.pad_r, y, fill=t["grid"])
            self.create_text(self.pad_l - 4, y, text=f"{v:.0f}",
                             fill=t["muted"], font=("Helvetica Neue", 9), anchor="e")

        self.create_text(self.pad_l, 8, text=self.label,
                         fill=t["muted"], font=("Helvetica Neue", 10, "bold"), anchor="w")

        if self.series2 and self.color2_key:
            pts2 = []
            for i, v in enumerate(self.series2):
                if v is None:
                    continue
                x = self.pad_l + (i / max(1, n - 1)) * pw
                y = self.pad_t + ph - ((v - lo) / rng) * ph
                pts2.extend([x, y])
            if len(pts2) >= 4:
                self.create_line(*pts2, fill=t[self.color2_key], width=1,
                                 capstyle=tk.ROUND, joinstyle=tk.ROUND,
                                 dash=(3, 2))

        pts = []
        for i, v in enumerate(self.series):
            if v is None:
                continue
            x = self.pad_l + (i / max(1, n - 1)) * pw
            y = self.pad_t + ph - ((v - lo) / rng) * ph
            pts.extend([x, y])
        if len(pts) >= 4:
            self.create_line(*pts, fill=t[self.color_key], width=2,
                             capstyle=tk.ROUND, joinstyle=tk.ROUND)

        # x-axis time labels (start / mid / end)
        if self._t0 and self._t1:
            for frac in (0.0, 0.5, 1.0):
                x = self.pad_l + frac * pw
                tt = self._t0 + (self._t1 - self._t0) * frac
                anchor = "sw" if frac == 0.0 else ("s" if frac == 0.5 else "se")
                self.create_text(x, self.h - 2, text=tt.strftime("%H:%M"),
                                 fill=t["muted"], font=("Helvetica Neue", 8),
                                 anchor=anchor)


