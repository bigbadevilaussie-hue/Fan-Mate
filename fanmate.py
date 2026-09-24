"""
FAN-MATE GUI V1.11
Synchronized with Fan-Mate Firmware V1.10 (.ino)

Requirements:
    pip install bleak
"""

import asyncio, json, threading, time, urllib.request
from collections import deque
from datetime import datetime
import tkinter as tk
from bleak import BleakScanner, BleakClient

GUI_VERSION = "1.11"
DEVICE_NAME = "Fan-Mate"
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
DATA_UUID   = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
TIME_UUID   = "beb5483e-36e1-4688-b7f5-ea07361b26a9"

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
temp_hist = deque([None] * HIST_LEN, maxlen=HIST_LEN)

latest = {"temp": None, "fan": 0, "rpm": 0, "phone": 0, "alert": 0}
weather = {"temp": 0.0, "high": 0.0, "low": 0.0, "desc": "Loading...", "updated": 0}

status_msg = ""
status_lock = threading.RLock()
last_parse_fail = 0
TIME_WRITE_LOGGED = False

FONT_TITLE = ("Helvetica Neue", 24, "bold")
FONT_SECTION = ("Helvetica Neue", 10)
FONT_BIG = ("Helvetica Neue", 34, "bold")
FONT_VALUE = ("Helvetica Neue", 15, "bold")
FONT_LABEL = ("Helvetica Neue", 9, "bold")
FONT_TINY = ("Helvetica Neue", 9)


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


def local_time_str():
    n = datetime.now()
    h = n.hour % 12 or 12
    return f"{h}:{n.minute:02d} {'AM' if n.hour < 12 else 'PM'}"


def time_emoji():
    h = datetime.now().hour
    return ("🌙" if h < 5 else "🌅" if h < 7 else "🌄" if h < 10 else
            "☀️" if h < 12 else "🌞" if h < 14 else "🌤" if h < 17 else
            "🌇" if h < 19 else "🌆" if h < 21 else "🌙")


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
        print(f"[WEATHER] {weather['temp']:.1f}°C {weather['desc']}")
    except Exception as e:
        print(f"[WEATHER] fetch failed: {e}")


def weather_thread_loop():
    while True:
        fetch_weather()
        time.sleep(WEATHER_REFRESH_SEC)


class BLEWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.running = True

    def run(self):
        asyncio.run(self._loop())

    async def _loop(self):
        global latest, last_parse_fail, TIME_WRITE_LOGGED

        def on_data(sender, data):
            global latest, last_parse_fail
            payload = bytes(data)
            if not payload:
                return
            try:
                d = json.loads(payload.decode())
                for k in ("temp", "fan", "rpm", "phone", "alert"):
                    if k in d:
                        latest[k] = d[k]
                if "temp" in d:
                    temp_hist.append(float(d["temp"]))
            except Exception as e:
                if time.time() - last_parse_fail > 10:
                    last_parse_fail = time.time()
                    print(f"[NOTIFY] parse fail: {e}")

        while self.running:
            try:
                set_status("scanning...")
                # macOS-compatible filter combining device name and service UUID check
                dev = await BleakScanner.find_device_by_filter(
                    lambda d, ad: (ad.local_name and DEVICE_NAME in ad.local_name) or
                                  (SERVICE_UUID.lower() in [str(u).lower() for u in ad.service_uuids]),
                    timeout=8.0
                )
                if not dev:
                    await asyncio.sleep(1)
                    continue

                set_status("connecting…")
                print(f"[BLE] connecting {dev.address}")
                try:
                    async with BleakClient(dev, timeout=10.0) as c:
                        set_status("connected")
                        print("[BLE] connected")
                        try:
                            await c.write_gatt_char(
                                TIME_UUID, int(time.time()).to_bytes(4, "little"))
                            if not TIME_WRITE_LOGGED:
                                TIME_WRITE_LOGGED = True
                                print("[TIME] wrote Unix time")
                        except Exception as e:
                            print(f"[TIME] {e}")
                        try:
                            await c.start_notify(DATA_UUID, on_data)
                            print("[BLE] subscribed DATA")
                        except Exception as e:
                            print(f"[DATA-SUB] {e}")
                        try:
                            v = await c.read_gatt_char(DATA_UUID)
                            on_data(None, v)
                        except Exception as e:
                            print(f"[DATA-READ] {e}")
                        while c.is_connected:
                            await asyncio.sleep(1.0)
                except Exception as e:
                    print(f"[BLE] conn err: {e}")
                    set_status(f"err: {e}")
                    await asyncio.sleep(2)
            except Exception as e:
                set_status(f"err: {e}")
                print(f"[BLE] loop err: {e}")
                await asyncio.sleep(3)


class Card(tk.Frame):
    """A themed card container with a 1px border accent."""
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
            self.create_line(self.pad_l, y, self.w - self.pad_r, y,
                             fill=t["grid"], width=1)
            self.create_text(self.pad_l - 5, y, text=f"{v:.0f}",
                             fill=t["muted"], font=FONT_TINY, anchor="e")

        if not pts:
            self.create_text(self.w / 2, self.h / 2, text="waiting…",
                             fill=t["muted"], font=FONT_TINY)
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
            poly = [self.pad_l, self.pad_t + ph] + coords + \
                   [self.pad_l + pw, self.pad_t + ph]
            self.create_polygon(poly, fill=t["fill"], outline="")
            self.create_line(*coords, fill=t["blue"], width=2,
                             capstyle=tk.ROUND, joinstyle=tk.ROUND)

        lx, ly = coords[-2], coords[-1]
        self.create_oval(lx - 4, ly - 4, lx + 4, ly + 4,
                         fill=t["blue"], outline=t["card"], width=2)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Fan-Mate")
        root.resizable(False, False)
        self.theme = current_theme()
        self.is_day = is_daytime()

        mb = tk.Menu(root)
        am = tk.Menu(mb, tearoff=0)
        am.add_command(label="Refresh Weather",
                       command=lambda: threading.Thread(
                           target=fetch_weather, daemon=True).start())
        am.add_separator()
        am.add_command(label="Toggle Day/Night", command=self.toggle_theme)
        am.add_separator()
        am.add_command(label="Quit", command=root.quit)
        mb.add_cascade(label="🌀 Fan-Mate", menu=am)
        root.config(menu=mb)

        # ---- Header ----
        self.title_lbl = tk.Label(root, text="🌀 Fan-Mate", font=FONT_TITLE)
        self.title_lbl.pack(pady=(16, 2))
        self.status_label = tk.Label(root, text="",
                                     font=("Helvetica Neue", 10, "italic"))
        self.status_label.pack(pady=(0, 10))

        # ---- Weather ----
        self.weather_card = Card(root, self)
        self.weather_card.pack(fill="x", padx=18, pady=(0, 8))
        self.weather_title = tk.Label(self.weather_card, text="Atkinsons Dam",
                                      font=("Helvetica Neue", 11, "bold"))
        self.weather_title.pack(pady=(10, 0))
        self.weather_temp_lbl = tk.Label(self.weather_card, text="--.-°",
                                         font=("Helvetica Neue", 28, "bold"))
        self.weather_temp_lbl.pack(pady=(2, 0))
        self.weather_desc_lbl = tk.Label(self.weather_card, text="Loading...",
                                         font=FONT_SECTION)
        self.weather_desc_lbl.pack(pady=(0, 2))
        self.weather_range_lbl = tk.Label(self.weather_card, text="",
                                        font=FONT_TINY)
        self.weather_range_lbl.pack(pady=(0, 10))

        # ---- Phone temperature ----
        self.temp_card = Card(root, self)
        self.temp_card.pack(fill="x", padx=18, pady=8)
        self.temp_title = tk.Label(self.temp_card, text="PHONE TEMPERATURE",
                                   font=FONT_LABEL)
        self.temp_title.pack(pady=(10, 0))
        self.temp_lbl = tk.Label(self.temp_card, text="--.-°C", font=FONT_BIG)
        self.temp_lbl.pack(pady=(0, 10))

        # ---- Fan / RPM ----
        self.fan_card = Card(root, self)
        self.fan_card.pack(fill="x", padx=18, pady=8)
        fr = tk.Frame(self.fan_card)
        fr.pack(fill="x", pady=10)
        self.fan_lbl = self._col(fr, "FAN", "--")
        self._divider(fr)
        self.rpm_lbl = self._col(fr, "RPM", "--")

        # ---- Phone / Alert ----
        self.status_card = Card(root, self)
        self.status_card.pack(fill="x", padx=18, pady=8)
        sr = tk.Frame(self.status_card)
        sr.pack(fill="x", pady=10)
        self.phone_lbl = self._col(sr, "PHONE", "--")
        self._divider(sr)
        self.alert_lbl = self._col(sr, "ALERT", "--")

        # ---- Time ----
        self.time_card = Card(root, self)
        self.time_card.pack(fill="x", padx=18, pady=8)
        self.time_lbl = tk.Label(self.time_card, text="--:--",
                                 font=("Helvetica Neue", 14, "bold"))
        self.time_lbl.pack(pady=10)

        # ---- Graph ----
        self.graph_card = Card(root, self)
        self.graph_card.pack(fill="x", padx=18, pady=8)
        self.graph_title = tk.Label(self.graph_card,
                                    text="TEMPERATURE HISTORY",
                                    font=FONT_LABEL)
        self.graph_title.pack(pady=(8, 0))
        self.temp_graph = Graph(self.graph_card, self, y_min=15, y_max=55)
        self.temp_graph.pack(padx=6, pady=(4, 8))

        # ---- Footer ----
        self.footer_lbl = tk.Label(root, text=f"GUI v{GUI_VERSION}",
                                   font=FONT_TINY)
        self.footer_lbl.pack(pady=(2, 10))

        self.apply_theme()

        self.worker = BLEWorker()
        self.worker.start()
        threading.Thread(target=weather_thread_loop, daemon=True).start()

        self.theme_check()
        self.tick()

    def _col(self, parent, label, value):
        c = tk.Frame(parent)
        c.pack(side="left", expand=True, fill="both")
        lbl1 = tk.Label(c, text=label, font=FONT_LABEL)
        lbl1.pack(pady=(2, 2))
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
                     self.status_card, self.time_card, self.graph_card):
            card.apply_theme()

        self.title_lbl.configure(bg=t["bg"], fg=t["accent"])
        self.status_label.configure(bg=t["bg"], fg=t["muted"])
        self.footer_lbl.configure(bg=t["bg"], fg=t["muted"])

        for lbl in (self.weather_title, self.temp_title, self.graph_title):
            lbl.configure(bg=t["card"], fg=t["muted"])

        self.weather_temp_lbl.configure(bg=t["card"], fg=t["fg"])
        self.weather_desc_lbl.configure(bg=t["card"], fg=t["muted"])
        self.weather_range_lbl.configure(bg=t["card"], fg=t["muted"])
        self.temp_lbl.configure(bg=t["card"])
        self.time_lbl.configure(bg=t["card"], fg=t["fg"])

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

    def theme_check(self):
        if is_daytime() != self.is_day:
            self.is_day = is_daytime()
            self.theme = current_theme()
            self.apply_theme()
        self.root.after(60_000, self.theme_check)

    def tick(self):
        t = self.theme
        d = latest

        temp = d.get("temp")
        if temp is None:
            self.temp_lbl.config(text="--.-°C", fg=t["muted"])
        else:
            if temp < 25:
                c, emoji = t["green"], "❄️"
            elif temp < 35:
                c, emoji = t["blue"], "🌤️"
            elif temp < 45:
                c, emoji = t["yellow"], "🔥"
            else:
                c, emoji = t["red"], "💀"
            self.temp_lbl.config(text=f"{temp:.1f}°C  {emoji}", fg=c)

        fan_pct = int(d.get("fan", 0))
        if fan_pct == 0:
            self.fan_lbl.config(text="OFF", fg=t["muted"])
        else:
            self.fan_lbl.config(text=f"{fan_pct}%", fg=t["green"])

        rpm = int(d.get("rpm", 0))
        self.rpm_lbl.config(text=f"{rpm}",
                            fg=t["green"] if rpm > 0 else t["muted"])

        phone = bool(d.get("phone", 0))
        self.phone_lbl.config(text="YES" if phone else "NO",
                              fg=t["green"] if phone else t["muted"])

        alert = int(d.get("alert", 0))
        if alert == 2:
            self.alert_lbl.config(text="PANIC", fg=t["red"])
        elif alert == 1:
            self.alert_lbl.config(text="WARN", fg=t["orange"])
        else:
            self.alert_lbl.config(text="OK", fg=t["green"])

        self.weather_temp_lbl.config(text=f"{weather['temp']:.1f}°")
        self.weather_desc_lbl.config(text=weather["desc"])
        self.weather_range_lbl.config(
            text=f"H {weather['high']:.0f}°  ·  L {weather['low']:.0f}°")

        self.time_lbl.config(text=f"{local_time_str()}  {time_emoji()}")

        self.temp_graph.set_data(temp_hist)

        self.status_label.config(text=get_status())

        self.root.after(1000, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()