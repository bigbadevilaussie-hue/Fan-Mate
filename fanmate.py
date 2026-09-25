"""
FAN-MATE GUI V3.01
- Full HTTP. No BLE. No local logging.
- Telemetry polled from ESP32 /status every 10s.
- Settings pushed to ESP32 /config.
- Logs live on ESP32. GUI can sync/clear/reboot.
- Same layout as V3.00, plus:
  - Boost section with Advanced (threshold/on/off)
  - Phone test_delay field
  - Alarm three levels (Warning / Oh Shit / Kill)
  - Sleep countdown + sleeping state
  - Opal offline indicator
  - Dyna Tune menu (stub)
"""

import json, threading, time, urllib.request, os, re
from collections import deque
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import requests

GUI_VERSION = "3.01"
FANMATE_URL = "http://fan-mate.local"
FANMATE_DIR = os.path.expanduser("~/Documents/Arduino/fanmate")
BUILD_DIR   = os.path.join(FANMATE_DIR, "build", "esp32.esp32.esp32c3")
BUILD_BIN   = os.path.join(BUILD_DIR, "fanmate.ino.bin")
CONFIG_H    = os.path.join(FANMATE_DIR, "Config.h")
LOG_DIR     = os.path.expanduser("~/Documents/FanMate_logs")

POLL_INTERVAL = 10.0

WEATHER_LAT = -27.28
WEATHER_LON = 152.51
WEATHER_TZ  = "Australia%2FBrisbane"
WEATHER_REFRESH_SEC = 1800
DAY_START_HOUR = 6
DAY_END_HOUR   = 18

THEME_DAY = {
    "bg": "#eef1f7", "card": "#ffffff", "card_border": "#d8dde8",
    "grid": "#e6e9f0", "fg": "#1e1e2e", "muted": "#7a8194",
    "accent": "#1e66f5", "blue": "#1e66f5", "green": "#2f9e44",
    "yellow": "#d99a00", "orange": "#e8590c", "red": "#d20f39",
    "fill": "#cfe0ff",
}
THEME_NIGHT = {
    "bg": "#181825", "card": "#232334", "card_border": "#313145",
    "grid": "#2a2a3a", "fg": "#cdd6f4", "muted": "#9399b2",
    "accent": "#89b4fa", "blue": "#89b4fa", "green": "#a6e3a1",
    "yellow": "#f9e2af", "orange": "#fab387", "red": "#e64553",
    "fill": "#2c3f5e",
}

HIST_LEN = 60
temp_hist     = deque([None] * HIST_LEN, maxlen=HIST_LEN)
download_hist = deque([None] * HIST_LEN, maxlen=HIST_LEN)

latest = {
    "temp": None, "fan": 0, "rpm": 0, "phone": 0, "alert": 0,
    "boost": 0, "fv": "?", "net_kbps": 0.0,
    "sleep": 0, "sleep_countdown": 0, "opal": 1,
}
latest_config = {
    "boost": {
        "mode": 1,
        "normal": {"threshold": 768, "on_hold": 4, "off_hold": 4},
        "aggr":   {"threshold": 256, "on_hold": 2, "off_hold": 8},
    },
    "alarm": {"mode": "auto", "warning": 45.0, "panic": 50.0, "kill": 55.0},
    "night": {"mode": "auto", "start": 22, "end": 7, "nightMax": 75},
    "phone": {"mode": "off", "test_delay": 120},
}
connected = False
time_synced = False
status_msg = ""
status_lock = threading.RLock()

FONT_TITLE   = ("Helvetica Neue", 24, "bold")
FONT_SECTION = ("Helvetica Neue", 10)
FONT_BIG     = ("Helvetica Neue", 34, "bold")
FONT_VALUE   = ("Helvetica Neue", 15, "bold")
FONT_LABEL   = ("Helvetica Neue", 9, "bold")
FONT_TINY    = ("Helvetica Neue", 9)


# ── Helpers ──────────────────────────────────────────────────

def is_daytime():
    return DAY_START_HOUR <= datetime.now().hour < DAY_END_HOUR

def current_theme():
    return THEME_DAY if is_daytime() else THEME_NIGHT

def set_status(m):
    global status_msg
    with status_lock:
        status_msg = m

def get_status():
    with status_lock:
        return status_msg

def read_firmware_version():
    try:
        with open(CONFIG_H) as f:
            m = re.search(r'#define\s+FAN_MATE_VERSION\s+"([^"]+)"', f.read())
            return m.group(1) if m else None
    except Exception:
        return None

def compute_md5(path):
    import hashlib
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def local_time_str():
    n = datetime.now()
    h = n.hour % 12 or 12
    return f"{h}:{n.minute:02d} {'AM' if n.hour < 12 else 'PM'}"

def time_emoji():
    h = datetime.now().hour
    return ("🌙" if h < 5 else "🌅" if h < 7 else "🌄" if h < 10 else
            "☀️" if h < 12 else "🌞" if h < 14 else "🌤️" if h < 17 else
            "🌇" if h < 19 else "🌆" if h < 21 else "🌙")

def temp_emoji(t):
    if t is None: return "❔"
    if t < 20: return "🥶"
    if t < 25: return "❄️"
    if t < 30: return "🌤️"
    if t < 35: return "☀️"
    if t < 42: return "🥵"
    if t < 48: return "🔥"
    return "💀"

def fan_emoji(p):
    if p == 0:  return "💤"
    if p < 30:  return "🍃"
    if p < 70:  return "💨"
    return "🌪️"

def weather_code_to_desc(code, is_day):
    if code == 0:
        return "Sunny" if is_day else "Clear Night"
    return {
        1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Fog", 48: "Fog", 51: "Light Drizzle", 53: "Drizzle",
        55: "Heavy Drizzle", 61: "Light Rain", 63: "Rain",
        65: "Heavy Rain", 71: "Light Snow", 73: "Snow", 75: "Heavy Snow",
        80: "Light Showers", 81: "Showers", 82: "Heavy Showers",
        95: "Thunderstorm", 96: "Thunderstorm + Hail", 99: "Thunderstorm + Hail",
    }.get(code, "Unknown")


# ── HTTP telemetry ───────────────────────────────────────────

def http_poll_loop():
    global latest, connected, time_synced
    poll_count = 0
    while True:
        poll_count += 1
        try:
            r = requests.get(f"{FANMATE_URL}/status", timeout=5)
            if r.status_code == 200:
                raw = r.text
                try:
                    d = r.json()
                except Exception as e:
                    print(f"[POLL #{poll_count}] JSON PARSE FAIL: {e}")
                    print(f"[POLL #{poll_count}] RAW: {raw[:300]}")
                    time.sleep(POLL_INTERVAL)
                    continue

                print(f"[POLL #{poll_count}] keys={sorted(d.keys())}")
                print(f"[POLL #{poll_count}] net_kbps={d.get('net_kbps','MISSING')} "
                      f"temp={d.get('temp')} fan={d.get('fan')} boost={d.get('boost')}")
                latest["temp"]     = d.get("temp")
                latest["fan"]      = d.get("fan", 0)
                latest["rpm"]      = d.get("rpm", 0)
                latest["phone"]    = d.get("phone", 0)
                latest["alert"]    = d.get("alert", 0)
                latest["boost"]    = d.get("boost", 0)
                latest["fv"]       = d.get("fw", "?")
                latest["net_kbps"] = float(d.get("net_kbps", 0.0))
                latest["sleep"]    = d.get("sleep", 0)
                latest["sleep_countdown"] = d.get("sleep_countdown", 0)
                latest["opal"]     = d.get("opal", 1)

                if latest["temp"] is not None:
                    temp_hist.append(float(latest["temp"]))
                download_hist.append(latest["net_kbps"])

                if not connected:
                    connected = True
                    print(f"[HTTP] connected {FANMATE_URL}")
                    fetch_config()
                    if not time_synced:
                        sync_time_once()

                set_status("connected")
            else:
                if connected:
                    print(f"[HTTP] bad status {r.status_code}")
                connected = False
                set_status(f"HTTP {r.status_code}")
        except Exception as e:
            if connected:
                print(f"[HTTP] {e}")
            connected = False
            set_status("disconnected")
            latest["boost"] = 0
            latest["sleep"] = 0
            latest["sleep_countdown"] = 0
        time.sleep(POLL_INTERVAL)


def sync_time_once():
    global time_synced
    try:
        r = requests.post(
            f"{FANMATE_URL}/time",
            json={"epoch": int(time.time())},
            timeout=3,
        )
        if r.status_code == 200:
            time_synced = True
            print("[TIME] synced to ESP32")
    except Exception as e:
        print(f"[TIME] failed: {e}")


def fetch_config():
    global latest_config
    try:
        r = requests.get(f"{FANMATE_URL}/config", timeout=5)
        if r.status_code != 200:
            return None
        d = r.json()
        for sec in ("boost", "alarm", "night", "phone"):
            if sec in d:
                latest_config.setdefault(sec, {}).update(d[sec])
        return latest_config
    except Exception as e:
        print(f"[CFG] fetch failed: {e}")
        return None


def post_config(payload):
    try:
        r = requests.post(f"{FANMATE_URL}/config", json=payload, timeout=5)
        if r.status_code == 200:
            print("[CFG] applied")
            return True
        print(f"[CFG] HTTP {r.status_code}")
    except Exception as e:
        print(f"[CFG] post failed: {e}")
    return False


# ── Weather ──────────────────────────────────────────────────

weather = {"temp": 0.0, "high": 0.0, "low": 0.0, "desc": "Loading...", "updated": 0}

def fetch_weather():
    global weather
    url = (
        f"http://api.open-meteo.com/v1/forecast?"
        f"latitude={WEATHER_LAT}&longitude={WEATHER_LON}"
        f"&current=temperature_2m,weather_code,is_day"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone={WEATHER_TZ}"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = json.loads(r.read().decode())
        cur = data["current"]
        day = data["daily"]
        weather["temp"] = float(cur.get("temperature_2m", 0.0))
        weather["high"] = float(day["temperature_2m_max"][0])
        weather["low"]  = float(day["temperature_2m_min"][0])
        weather["desc"] = weather_code_to_desc(
            int(cur.get("weather_code", -1)), int(cur.get("is_day", 1))
        )
        weather["updated"] = time.time()
    except Exception as e:
        print(f"[WEATHER] {e}")


def weather_thread_loop():
    while True:
        fetch_weather()
        time.sleep(WEATHER_REFRESH_SEC)


# ── Widgets ──────────────────────────────────────────────────

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


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("Fan-Mate Settings")
        self.resizable(False, False)
        self.grab_set()

        fetch_config()

        row = 0
        pad = {"padx": 10, "pady": 4}

        def section(label):
            nonlocal row
            tk.Label(self, text=label, font=("Helvetica", 11, "bold")).grid(
                row=row, column=0, columnspan=3, sticky="w", pady=(12, 4), padx=10)
            row += 1

        def radio(label, var, options):
            nonlocal row
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w", **pad)
            fr = tk.Frame(self)
            fr.grid(row=row, column=1, columnspan=2, sticky="w")
            for v in options:
                tk.Radiobutton(fr, text=v.upper(), variable=var, value=v).pack(side="left")
            row += 1

        def entry(label, var, width=8):
            nonlocal row
            tk.Label(self, text=label).grid(row=row, column=0, sticky="w", **pad)
            tk.Entry(self, textvariable=var, width=width).grid(row=row, column=1, sticky="w")
            row += 1

        # ── BOOST ────────────────────────────────────────────
        section("⚡  BOOST")
        mode_map = {0: "off", 1: "normal", 2: "aggressive"}
        self.boost_mode = tk.StringVar(value=mode_map.get(latest_config["boost"].get("mode", 1), "normal"))
        radio("Mode:", self.boost_mode, ["off", "normal", "aggressive"])

        # Advanced subsection
        adv_lbl = tk.Label(self, text="▾ Advanced", font=("Helvetica", 9, "italic"))
        adv_lbl.grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 2))
        row += 1

        norm = latest_config["boost"].get("normal", {})
        aggr = latest_config["boost"].get("aggr", {})

        self.norm_thr  = tk.StringVar(value=str(norm.get("threshold", 768)))
        self.norm_on   = tk.StringVar(value=str(norm.get("on_hold", 4)))
        self.norm_off  = tk.StringVar(value=str(norm.get("off_hold", 4)))
        self.aggr_thr  = tk.StringVar(value=str(aggr.get("threshold", 256)))
        self.aggr_on   = tk.StringVar(value=str(aggr.get("on_hold", 2)))
        self.aggr_off  = tk.StringVar(value=str(aggr.get("off_hold", 8)))

        tk.Label(self, text="Normal:", font=("Helvetica", 9, "bold")).grid(row=row, column=0, sticky="w", padx=10)
        fr1 = tk.Frame(self); fr1.grid(row=row, column=1, columnspan=2, sticky="w")
        tk.Label(fr1, text="Thr").pack(side="left")
        tk.Entry(fr1, textvariable=self.norm_thr, width=6).pack(side="left", padx=2)
        tk.Label(fr1, text="On").pack(side="left")
        tk.Entry(fr1, textvariable=self.norm_on, width=3).pack(side="left", padx=2)
        tk.Label(fr1, text="Off").pack(side="left")
        tk.Entry(fr1, textvariable=self.norm_off, width=3).pack(side="left", padx=2)
        row += 1

        tk.Label(self, text="Aggressive:", font=("Helvetica", 9, "bold")).grid(row=row, column=0, sticky="w", padx=10)
        fr2 = tk.Frame(self); fr2.grid(row=row, column=1, columnspan=2, sticky="w")
        tk.Label(fr2, text="Thr").pack(side="left")
        tk.Entry(fr2, textvariable=self.aggr_thr, width=6).pack(side="left", padx=2)
        tk.Label(fr2, text="On").pack(side="left")
        tk.Entry(fr2, textvariable=self.aggr_on, width=3).pack(side="left", padx=2)
        tk.Label(fr2, text="Off").pack(side="left")
        tk.Entry(fr2, textvariable=self.aggr_off, width=3).pack(side="left", padx=2)
        row += 1

        # ── ALARM ────────────────────────────────────────────
        section("🚨  ALARM")
        self.alarm_mode = tk.StringVar(value=latest_config["alarm"]["mode"])
        radio("Mode:", self.alarm_mode, ["off", "on", "auto"])
        self.alarm_warn = tk.StringVar(value=str(latest_config["alarm"].get("warning", 45.0)))
        entry("Warning (°C):", self.alarm_warn)
        self.alarm_panic = tk.StringVar(value=str(latest_config["alarm"].get("panic", 50.0)))
        entry("Oh Shit (°C):", self.alarm_panic)
        self.alarm_kill = tk.StringVar(value=str(latest_config["alarm"].get("kill", 55.0)))
        entry("Kill (°C):", self.alarm_kill)

        # ── NIGHT ────────────────────────────────────────────
        section("🌙  NIGHT")
        self.night_mode = tk.StringVar(value=latest_config["night"]["mode"])
        radio("Mode:", self.night_mode, ["off", "on", "auto"])
        self.night_start = tk.StringVar(value=str(latest_config["night"].get("start", 22)))
        entry("Start hour (0-23):", self.night_start)
        self.night_end = tk.StringVar(value=str(latest_config["night"].get("end", 7)))
        entry("End hour (0-23):", self.night_end)
        self.night_max = tk.StringVar(value=str(latest_config["night"].get("nightMax", 75)))
        entry("Night max (%):", self.night_max)

        # ── PHONE ────────────────────────────────────────────
        section("📱  PHONE")
        self.phone_mode = tk.StringVar(value=latest_config["phone"].get("mode", "off"))
        radio("Mode:", self.phone_mode, ["off", "auto"])
        self.test_delay = tk.StringVar(value=str(latest_config["phone"].get("test_delay", 0)))
        entry("Test delay (s):", self.test_delay)

        btn = tk.Frame(self)
        btn.grid(row=row, column=0, columnspan=3, pady=16)
        tk.Button(btn, text="Apply", width=10, command=self.apply).pack(side="left", padx=4)
        tk.Button(btn, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=4)

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
                "alarm": {
                    "mode":    self.alarm_mode.get(),
                    "warning": float(self.alarm_warn.get()),
                    "panic":   float(self.alarm_panic.get()),
                    "kill":    float(self.alarm_kill.get()),
                },
                "night": {
                    "mode":     self.night_mode.get(),
                    "start":    int(self.night_start.get()),
                    "end":      int(self.night_end.get()),
                    "nightMax": int(self.night_max.get()),
                },
                "phone": {
                    "mode":       self.phone_mode.get(),
                    "test_delay": int(self.test_delay.get()),
                },
            }
        except ValueError as e:
            messagebox.showerror("Settings", f"Invalid value:\n{e}")
            return

        if post_config(payload):
            messagebox.showinfo("Settings", "Applied on ESP32")
            self.destroy()
        else:
            messagebox.showerror("Settings", "Failed to apply — check ESP32 connection")


# ── App ──────────────────────────────────────────────────────

class App:
    def __init__(self, root):
        self.root = root
        root.title(f"🌀 Fan-Mate v{GUI_VERSION}")
        root.resizable(False, False)
        self.theme = current_theme()
        self.is_day = is_daytime()
        self.turbo_phase = 0

        mb = tk.Menu(root)
        am = tk.Menu(mb, tearoff=0)
        am.add_command(label="⚙️  Settings", command=self.menu_settings)
        am.add_separator()
        am.add_command(label="🎛️  Dyna Tune Turbo Boost", command=self.menu_dyna_tune)
        am.add_separator()
        am.add_command(label="🌦️  Refresh Weather",
                       command=lambda: threading.Thread(target=fetch_weather, daemon=True).start())
        am.add_separator()
        am.add_command(label="📥  Sync Log", command=self.sync_log)
        am.add_command(label="📂  Open Log Folder", command=self.open_log_folder)
        am.add_command(label="🗑️  Clear Log on Device", command=self.clear_log)
        am.add_separator()
        am.add_command(label="📡  Update Firmware (WiFi)", command=self.menu_ota)
        am.add_separator()
        am.add_command(label="🌗  Toggle Day/Night", command=self.toggle_theme)
        am.add_separator()
        am.add_command(label="❌  Quit", command=root.quit)
        mb.add_cascade(label="🌀 Fan-Mate", menu=am)
        root.config(menu=mb)

        self.title_lbl = tk.Label(root, text="🌀 Fan-Mate", font=FONT_TITLE)
        self.title_lbl.pack(pady=(16, 2))
        self.status_label = tk.Label(root, text="connecting…", font=("Helvetica Neue", 10, "italic"))
        self.status_label.pack(pady=(0, 8))

        # Weather
        self.weather_card = Card(root, self)
        self.weather_card.pack(fill="x", padx=18, pady=(0, 8))
        self.weather_title = tk.Label(self.weather_card, text="📍 Atkinsons Dam", font=("Helvetica Neue", 11, "bold"))
        self.weather_title.pack(pady=(10, 0))
        self.weather_temp_lbl = tk.Label(self.weather_card, text="--.-°", font=("Helvetica Neue", 28, "bold"))
        self.weather_temp_lbl.pack(pady=(2, 0))
        self.weather_desc_lbl = tk.Label(self.weather_card, text="Loading…", font=FONT_SECTION)
        self.weather_desc_lbl.pack(pady=(0, 2))
        self.weather_range_lbl = tk.Label(self.weather_card, text="", font=FONT_TINY)
        self.weather_range_lbl.pack(pady=(0, 10))

        # Phone temp
        self.temp_card = Card(root, self)
        self.temp_card.pack(fill="x", padx=18, pady=8)
        self.temp_title = tk.Label(self.temp_card, text="🌡️ PHONE TEMPERATURE", font=FONT_LABEL)
        self.temp_title.pack(pady=(10, 0))
        self.temp_lbl = tk.Label(self.temp_card, text="--.-°C", font=FONT_BIG)
        self.temp_lbl.pack(pady=(0, 10))

        # Fan / RPM
        self.fan_card = Card(root, self)
        self.fan_card.pack(fill="x", padx=18, pady=8)
        fr = tk.Frame(self.fan_card)
        fr.pack(fill="x", pady=10)
        self.fan_lbl = self._col(fr, "💨 FAN", "--")
        self._divider(fr)
        self.rpm_lbl = self._col(fr, "⚙️ RPM", "--")

        # Phone / Alert
        self.status_card = Card(root, self)
        self.status_card.pack(fill="x", padx=18, pady=8)
        sr = tk.Frame(self.status_card)
        sr.pack(fill="x", pady=10)
        self.phone_lbl = self._col(sr, "📱 PHONE", "--")
        self._divider(sr)
        self.alert_lbl = self._col(sr, "🚨 ALERT", "--")

        # Time
        self.time_card = Card(root, self)
        self.time_card.pack(fill="x", padx=18, pady=8)
        self.time_lbl = tk.Label(self.time_card, text="--:--", font=("Helvetica Neue", 14, "bold"))
        self.time_lbl.pack(pady=10)

        # Network rate
        self.data_card = Card(root, self)
        self.data_card.pack(fill="x", padx=18, pady=8)
        self.data_title = tk.Label(self.data_card, text="📥 NETWORK RATE (ESP32)", font=FONT_LABEL)
        self.data_title.pack(pady=(8, 0))
        self.rate_lbl = tk.Label(self.data_card, text="-- KB/s", font=FONT_VALUE)
        self.rate_lbl.pack(pady=(2, 6))
        self.data_graph = Graph(self.data_card, self, y_min=0, y_max=5120, w=380, h=100)
        self.data_graph.pack(padx=6, pady=(0, 8))

        # Temp graph
        self.graph_card = Card(root, self)
        self.graph_card.pack(fill="x", padx=18, pady=8)
        self.graph_title = tk.Label(self.graph_card, text="📈 TEMPERATURE HISTORY", font=FONT_LABEL)
        self.graph_title.pack(pady=(8, 0))
        self.temp_graph = Graph(self.graph_card, self, y_min=15, y_max=55)
        self.temp_graph.pack(padx=6, pady=(4, 8))

        self.footer_lbl = tk.Label(
            root,
            text=f"GUI v{GUI_VERSION}  •  HTTP  •  Logs on ESP32",
            font=FONT_TINY,
        )
        self.footer_lbl.pack(pady=(2, 10))

        self.apply_theme()

        threading.Thread(target=http_poll_loop, daemon=True).start()
        threading.Thread(target=weather_thread_loop, daemon=True).start()

        self.theme_check()
        self.tick()

    # ── Menu actions ─────────────────────────────────────────

    def menu_settings(self):
        SettingsDialog(self.root, self)

    def menu_dyna_tune(self):
        messagebox.showinfo(
            "🎛️ Dyna Tune Turbo Boost",
            "Analyzes all logs in ~/Documents/FanMate_logs/\n\n"
            "Coming soon.\n\n"
            "Minimum 3 days / 20 events needed for reliable suggestions."
        )

    def sync_log(self):
        try:
            r = requests.get(f"{FANMATE_URL}/log.csv", timeout=10)
            if r.status_code != 200:
                messagebox.showerror("Sync Log", f"HTTP {r.status_code}")
                return
            os.makedirs(LOG_DIR, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            path = os.path.join(LOG_DIR, f"log-{ts}.csv")
            with open(path, "wb") as f:
                f.write(r.content)
            lines = r.content.count(b"\n")
            size_kb = len(r.content) / 1024
            messagebox.showinfo("Sync Log", f"Saved {lines} lines ({size_kb:.1f} KB)\n\n{path}")
        except Exception as e:
            messagebox.showerror("Sync Log", f"Failed:\n{e}")

    def open_log_folder(self):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            os.system(f'open "{LOG_DIR}"')
        except Exception as e:
            messagebox.showerror("Log Folder", f"Failed:\n{e}")

    def clear_log(self):
        if not messagebox.askyesno("Clear Log", "Delete log on ESP32?\n\nDownload it first!"):
            return
        try:
            r = requests.post(f"{FANMATE_URL}/log/clear", timeout=5)
            if r.status_code == 200:
                messagebox.showinfo("Clear Log", "Log cleared on device.")
            else:
                messagebox.showerror("Clear Log", f"HTTP {r.status_code}")
        except Exception as e:
            messagebox.showerror("Clear Log", f"Failed:\n{e}")

    def menu_ota(self):
        if not os.path.isfile(BUILD_BIN):
            messagebox.showerror(
                "OTA",
                f"Firmware not found:\n{BUILD_BIN}\n\n"
                f"Run Sketch → Export Compiled Binary in Arduino IDE first."
            )
            return

        src_ver = read_firmware_version() or "?"
        try:
            bin_mtime = os.path.getmtime(BUILD_BIN)
            cfg_mtime = os.path.getmtime(CONFIG_H)
            stale = cfg_mtime > bin_mtime
        except Exception:
            stale = False
            bin_mtime = 0

        size = os.path.getsize(BUILD_BIN)
        md5 = compute_md5(BUILD_BIN) or "?"
        dev_ver = latest.get("fv", "?")
        built_str = (datetime.fromtimestamp(bin_mtime).strftime("%Y-%m-%d %H:%M")
                     if bin_mtime else "?")
        size_mb = size / (1024 * 1024)

        msg = (
            f"File:        fanmate.ino.bin\n"
            f"Size:        {size:,} bytes ({size_mb:.2f} MB)\n"
            f"MD5:         {md5[:16]}...\n"
            f"Source ver:  {src_ver}\n"
            f"Built:       {built_str}\n"
            f"Device ver:  {dev_ver}\n"
        )
        if stale:
            msg += "\n⚠️  Config.h is newer than the .bin.\nRe-export the binary before updating."
        msg += "\n\nProceed with OTA update?"

        if not messagebox.askyesno("Fan-Mate OTA", msg):
            return

        try:
            with open(BUILD_BIN, "rb") as f:
                r = requests.post(
                    f"{FANMATE_URL}/ota",
                    files={"firmware": f},
                    timeout=120,
                )
            if r.status_code == 200:
                messagebox.showinfo("OTA", "Firmware sent. Device rebooting.")
            else:
                messagebox.showerror("OTA", f"Failed: HTTP {r.status_code}\n{r.text}")
        except Exception as e:
            messagebox.showerror("OTA", f"Failed:\n{e}")

    # ── Helpers ──────────────────────────────────────────────

    def _col(self, parent, label, value):
        c = tk.Frame(parent)
        c.pack(side="left", expand=True, fill="both")
        tk.Label(c, text=label, font=FONT_LABEL).pack(pady=(2, 2))
        lbl2 = tk.Label(c, text=value, font=FONT_VALUE)
        lbl2.pack(pady=(0, 2))
        return lbl2

    def _divider(self, parent):
        d = tk.Frame(parent, width=1)
        d.pack(side="left", fill="y", pady=4)

    def toggle_theme(self):
        self.is_day = not self.is_day
        self.theme = THEME_DAY if self.is_day else THEME_NIGHT
        self.apply_theme()

    def apply_theme(self):
        t = self.theme
        self.root.configure(bg=t["bg"])
        for card in (self.weather_card, self.temp_card, self.fan_card,
                     self.status_card, self.time_card, self.data_card, self.graph_card):
            card.apply_theme()
        self.title_lbl.configure(bg=t["bg"], fg=t["accent"])
        self.status_label.configure(bg=t["bg"], fg=t["muted"])
        self.footer_lbl.configure(bg=t["bg"], fg=t["muted"])
        for lbl in (self.weather_title, self.temp_title, self.graph_title, self.data_title):
            lbl.configure(bg=t["card"], fg=t["muted"])
        self.weather_temp_lbl.configure(bg=t["card"], fg=t["fg"])
        self.weather_desc_lbl.configure(bg=t["card"], fg=t["muted"])
        self.weather_range_lbl.configure(bg=t["card"], fg=t["muted"])
        self.temp_lbl.configure(bg=t["card"])
        self.time_lbl.configure(bg=t["card"], fg=t["fg"])
        self.rate_lbl.configure(bg=t["card"], fg=t["fg"])
        for holder in (self.fan_card, self.status_card):
            for child in holder.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=t["card"])
                    for sub in child.winfo_children():
                        if sub.cget("width") == 1:
                            sub.configure(bg=t["card_border"])
                        else:
                            sub.configure(bg=t["card"])
                            for inner in sub.winfo_children():
                                if inner.cget("text").isupper():
                                    inner.configure(bg=t["card"], fg=t["muted"])
                                else:
                                    inner.configure(bg=t["card"], fg=t["fg"])
        self.temp_graph.apply_theme()
        self.temp_graph.redraw()
        self.data_graph.apply_theme()
        self.data_graph.redraw()

    def theme_check(self):
        if is_daytime() != self.is_day:
            self.is_day = is_daytime()
            self.theme = current_theme()
            self.apply_theme()
        self.root.after(60_000, self.theme_check)

    # ── Main tick ────────────────────────────────────────────

    def tick(self):
        t = self.theme
        d = latest

        # ── Status line priority ─────────────────────────────
        self.turbo_phase = (self.turbo_phase + 1) % 4
        sleep = d.get("sleep", 0)
        countdown = d.get("sleep_countdown", 0)
        boost = d.get("boost", 0)
        opal = d.get("opal", 1)

        if not connected:
            self.status_label.config(
                text="disconnected",
                font=("Helvetica Neue", 10, "italic"),
                fg=t["muted"],
            )
        elif sleep:
            self.status_label.config(
                text="💤 sleeping (phone absent)",
                font=("Helvetica Neue", 12, "bold"),
                fg=t["muted"],
            )
        elif countdown > 0:
            self.status_label.config(
                text=f"⚠️  Sleeping in {countdown}s",
                font=("Helvetica Neue", 11, "bold"),
                fg=t["orange"],
            )
        elif boost and connected:
            turbo_colors = ["#00ff00", "#ffff00", "#ff8800", "#ff0000"]
            self.status_label.config(
                text="🏎️💨 TURBO 💨🏎️",
                font=("Helvetica Neue", 13, "bold"),
                fg=turbo_colors[self.turbo_phase],
            )
        elif not opal:
            self.status_label.config(
                text="🔌 opal offline",
                font=("Helvetica Neue", 10, "italic"),
                fg=t["orange"],
            )
        else:
            self.status_label.config(
                text=get_status(),
                font=("Helvetica Neue", 10, "italic"),
                fg=t["muted"],
            )

        # ── Temperature ──────────────────────────────────────
        temp = d.get("temp")
        if temp is None:
            self.temp_lbl.config(text="--.-°C  ❔", fg=t["muted"])
        else:
            em = temp_emoji(temp)
            c = (t["green"] if temp < 25 else t["blue"] if temp < 35
                 else t["yellow"] if temp < 45 else t["red"])
            self.temp_lbl.config(text=f"{temp:.1f}°C  {em}", fg=c)

        # ── Fan / RPM ────────────────────────────────────────
        fan_pct = int(d.get("fan", 0))
        fe = fan_emoji(fan_pct)
        self.fan_lbl.config(
            text=f"OFF {fe}" if fan_pct == 0 else f"{fan_pct}% {fe}",
            fg=t["muted"] if fan_pct == 0 else t["green"],
        )
        rpm = int(d.get("rpm", 0))
        self.rpm_lbl.config(text=f"{rpm}", fg=t["green"] if rpm > 0 else t["muted"])

        # ── Phone ────────────────────────────────────────────
        phone_mode = latest_config.get("phone", {}).get("mode", "off")
        if phone_mode == "off":
            self.phone_lbl.config(text="BENCH 🧪", fg=t["muted"])
        else:
            phone = bool(d.get("phone", 0))
            self.phone_lbl.config(
                text="YES 📱" if phone else "NO  📴",
                fg=t["green"] if phone else t["muted"],
            )

        # ── Alert ────────────────────────────────────────────
        alert = int(d.get("alert", 0))
        if alert >= 3:
            self.alert_lbl.config(text="KILL 💀", fg=t["red"])
        elif alert == 2:
            self.alert_lbl.config(text="OH SHIT 🚨", fg=t["red"])
        elif alert == 1:
            self.alert_lbl.config(text="WARN ⚠️", fg=t["orange"])
        else:
            self.alert_lbl.config(text="OK ✅", fg=t["green"])

        # ── Weather ──────────────────────────────────────────
        self.weather_temp_lbl.config(text=f"{weather['temp']:.1f}°")
        self.weather_desc_lbl.config(text=weather["desc"])
        self.weather_range_lbl.config(
            text=f"⬆️ {weather['high']:.0f}°   ⬇️ {weather['low']:.0f}°"
        )

        # ── Time ─────────────────────────────────────────────
        self.time_lbl.config(text=f"{local_time_str()}  {time_emoji()}")

        # ── Network rate ─────────────────────────────────────
        rate_kbps = float(d.get("net_kbps", 0.0))
        if rate_kbps >= 1024:
            self.rate_lbl.config(text=f"{rate_kbps/1024:.2f} MB/s")
        else:
            self.rate_lbl.config(text=f"{rate_kbps:.1f} KB/s")

        # ── Graphs ───────────────────────────────────────────
        # Temp graph — red line at alarmWarning
        self.temp_graph.trigger = latest_config.get("alarm", {}).get("warning", None)
        self.temp_graph.set_data(temp_hist)

        # Network graph — red line at current boost threshold
        boost_mode = latest_config.get("boost", {}).get("mode", 1)
        if boost_mode == 1:
            thr = latest_config.get("boost", {}).get("normal", {}).get("threshold")
        elif boost_mode == 2:
            thr = latest_config.get("boost", {}).get("aggr", {}).get("threshold")
        else:
            thr = None
        self.data_graph.trigger = thr
        self.data_graph.set_data(download_hist)

        self.root.after(250, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
