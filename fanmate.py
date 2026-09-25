"""
FAN-MATE GUI V2.24
- V2.23 + Sync Log / Open Log Folder / Clear Log on Device
- Only monitors en1
- Boost waits for BLE connection before forcing fan
- Live download + Temp vs Data graph + CSV logging
"""

import asyncio, json, struct, threading, time, urllib.request, os, hashlib, re, csv, subprocess
from collections import deque
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from bleak import BleakScanner, BleakClient
import requests

GUI_VERSION = "2.24"
DEVICE_NAME = "Fan-Mate"
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
DATA_UUID    = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
TIME_UUID    = "beb5483e-36e1-4688-b7f5-ea07361b26a9"
OTA_UUID     = "beb5483e-36e1-4688-b7f5-ea07361b26ac"
PAUSE_UUID   = "beb5483e-36e1-4688-b7f5-ea07361b26af"
CONFIG_UUID  = "beb5483e-36e1-4688-b7f5-ea07361b26b0"

CONFIG_FILE = os.path.expanduser("~/.fanmate_config.json")
LOG_FILE    = os.path.expanduser("~/Documents/FanMate_temp_vs_data.csv")
LOG_DIR     = os.path.expanduser("~/Documents/FanMate_logs")
FANMATE_URL = "http://fan-mate.local"
FANMATE_DIR = os.path.expanduser("~/Documents/Arduino/fanmate")
BUILD_DIR   = os.path.join(FANMATE_DIR, "build", "esp32.esp32.esp32c3")
BUILD_BIN   = os.path.join(BUILD_DIR, "fanmate.ino.bin")
CONFIG_H    = os.path.join(FANMATE_DIR, "Config.h")

WEATHER_LAT = -27.28
WEATHER_LON = 152.51
WEATHER_TZ  = "Australia%2FBrisbane"
WEATHER_REFRESH_SEC = 1800
DAY_START_HOUR = 6
DAY_END_HOUR   = 18

BOOST_THRESHOLD_BPS = 1.0 * 1024 * 1024
BOOST_HOLD_SECONDS  = 12

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
download_hist = deque([None] * HIST_LEN, maxlen=HIST_LEN)

latest = {"temp": None, "fan": 0, "rpm": 0, "phone": 0, "alert": 0, "fv": "?"}
weather = {"temp": 0.0, "high": 0.0, "low": 0.0, "desc": "Loading...", "updated": 0}
status_msg = ""
status_lock = threading.RLock()
last_parse_fail = 0
TIME_WRITE_LOGGED = False
DEVICE_ADDR = None

latest_config = {
    "fan":   {"mode": "auto", "tempOn": 34.0, "tempFull": 42.0, "nightMax": 75},
    "alarm": {"mode": "auto", "warning": 45.0, "panic": 50.0},
    "night": {"mode": "auto", "start": 22, "end": 7},
    "phone": {"mode": "auto"},
}

try:
    with open(CONFIG_FILE) as _f:
        _saved = json.load(_f)
        latest_config.update(_saved)
    print(f"[CFG] loaded from {CONFIG_FILE}")
except FileNotFoundError:
    print("[CFG] no saved config — using defaults")
except Exception as e:
    print(f"[CFG] load failed: {e}")

FONT_TITLE   = ("Helvetica Neue", 24, "bold")
FONT_SECTION = ("Helvetica Neue", 10)
FONT_BIG     = ("Helvetica Neue", 34, "bold")
FONT_VALUE   = ("Helvetica Neue", 15, "bold")
FONT_LABEL   = ("Helvetica Neue", 9, "bold")
FONT_TINY    = ("Helvetica Neue", 9)


def get_rx_bytes(iface="en1"):
    try:
        out = subprocess.check_output(["netstat", "-ibn"], text=True)
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0] == iface and len(parts) > 6 and parts[6].isdigit():
                return int(parts[6])
        return 0
    except Exception:
        return 0


def init_log():
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "temp_c", "download_mb_total", "download_kbps", "boost"])


def log_data(temp, total_bytes, rate_bps, boost_active):
    try:
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"{temp:.2f}" if temp is not None else "",
                f"{total_bytes / (1024*1024):.2f}",
                f"{rate_bps / 1024:.1f}",
                "YES" if boost_active else "NO"
            ])
    except Exception as e:
        print(f"[LOG] {e}")


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
            content = f.read()
        m = re.search(r'#define\s+FAN_MATE_VERSION\s+"([^"]+)"', content)
        return m.group(1) if m else None
    except Exception as e:
        print(f"[OTA] read version failed: {e}")
        return None


def compute_md5(path):
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        print(f"[OTA] md5 failed: {e}")
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


def temp_emoji(temp):
    if temp is None:   return "❔"
    if temp < 20:      return "🥶"
    if temp < 25:      return "❄️"
    if temp < 30:      return "🌤️"
    if temp < 35:      return "☀️"
    if temp < 42:      return "🥵"
    if temp < 48:      return "🔥"
    return "💀"


def fan_emoji(pct):
    if pct == 0:  return "💤"
    if pct < 30:  return "🍃"
    if pct < 70:  return "💨"
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
        self.client = None
        self.loop = None
        self.mtu = 23

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._loop())

    async def _loop(self):
        global latest, last_parse_fail, TIME_WRITE_LOGGED, DEVICE_ADDR, latest_config
        def on_data(sender, data):
            global latest, last_parse_fail, latest_config
            payload = bytes(data)
            if not payload:
                return
            try:
                d = json.loads(payload.decode())
                for k in ("temp", "fan", "rpm", "phone", "alert", "fv"):
                    if k in d:
                        latest[k] = d[k]
                if "config" in d:
                    latest_config = d["config"]
                if "temp" in d and d["temp"] is not None:
                    temp_hist.append(float(d["temp"]))
            except Exception as e:
                if time.time() - last_parse_fail > 10:
                    last_parse_fail = time.time()
                    print(f"[NOTIFY] parse fail: {e}")

        while self.running:
            try:
                set_status("scanning…")
                dev = await BleakScanner.find_device_by_filter(
                    lambda d, ad: (ad.local_name and DEVICE_NAME in ad.local_name) or
                                  (SERVICE_UUID.lower() in [str(u).lower() for u in ad.service_uuids]),
                    timeout=8.0
                )
                if not dev:
                    await asyncio.sleep(1)
                    continue
                DEVICE_ADDR = dev.address
                set_status("connecting…")
                print(f"[BLE] connecting {dev.address}")
                try:
                    async with BleakClient(dev, timeout=10.0) as c:
                        self.client = c
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
                finally:
                    self.client = None
                    self.mtu = 23
            except Exception as e:
                set_status(f"err: {e}")
                print(f"[BLE] loop err: {e}")
                await asyncio.sleep(3)

    def send_config(self, payload):
        if not self.loop:
            print("[CFG] worker not running")
            return
        asyncio.run_coroutine_threadsafe(
            self._send_config_async(payload), self.loop)

    async def _send_config_async(self, payload):
        if not self.client or not self.client.is_connected:
            print("[CFG] not connected – will retry later")
            return False
        try:
            js = json.dumps(payload, separators=(",", ":"))
            print(f"[CFG] sending: {js}")
            await self.client.write_gatt_char(CONFIG_UUID, js.encode())
            print("[CFG] sent")
            return True
        except Exception as e:
            print(f"[CFG] send failed: {e}")
            return False

    def start_ota(self, fw_bytes, result_cb):
        if not self.loop:
            result_cb(False, "worker not running")
            return
        fut = asyncio.run_coroutine_threadsafe(
            self._ota_async(fw_bytes), self.loop)
        def _wait():
            try:
                ok, msg = fut.result(timeout=1800)
            except Exception as e:
                ok, msg = False, str(e)
            result_cb(ok, msg)
        threading.Thread(target=_wait, daemon=True).start()

    def _chunk_size(self):
        if self.mtu >= 247: return 244
        if self.mtu >= 185: return 182
        return 20

    async def _ota_async(self, fw):
        if not self.client or not self.client.is_connected:
            return False, "not connected"
        size = len(fw)
        md5_hex = hashlib.md5(fw).hexdigest().encode()
        try:
            ota_char = self.client.services.get_characteristic(OTA_UUID)
            max_write = ota_char.max_write_without_response_size
            print(f"[MTU] characteristic max_write={max_write}")
            self.mtu = max_write + 3
        except Exception as e:
            print(f"[MTU] could not read max_write: {e}")
        chunk_size = self._chunk_size()
        total_chunks = (size + chunk_size - 1) // chunk_size
        print(f"[OTA] sending {size} bytes, md5={md5_hex.decode()}")
        ready_event = asyncio.Event()
        notify_count = {"n": 0}
        def on_ota_notify(sender, data):
            notify_count["n"] += 1
            ready_event.set()
        try:
            await self.client.start_notify(OTA_UUID, on_ota_notify)
        except Exception as e:
            return False, f"notify sub: {e}"
        try:
            await self.client.write_gatt_char(PAUSE_UUID, bytes([0x00]))
        except Exception as e:
            print(f"[OTA] pause failed: {e}")
        try:
            header = struct.pack("<I", size) + md5_hex
            await self.client.write_gatt_char(OTA_UUID, header)
        except Exception as e:
            try:
                await self.client.stop_notify(OTA_UUID)
            except Exception:
                pass
            return False, f"header: {e}"
        sent = 0
        last_report = 0
        t0 = time.time()
        stall_count = 0
        for i in range(0, size, chunk_size):
            chunk = fw[i:i+chunk_size]
            try:
                await self.client.write_gatt_char(OTA_UUID, chunk, response=True)
            except Exception as e:
                try:
                    await self.client.stop_notify(OTA_UUID)
                except Exception:
                    pass
                return False, f"chunk @ {i}: {e}"
            sent += len(chunk)
            if sent % 2048 < chunk_size:
                try:
                    await asyncio.wait_for(ready_event.wait(), timeout=10.0)
                    ready_event.clear()
                    stall_count = 0
                except asyncio.TimeoutError:
                    stall_count += 1
                    if stall_count >= 3:
                        try:
                            await self.client.stop_notify(OTA_UUID)
                        except Exception:
                            pass
                        return False, f"ESP32 stalled at {sent}"
            if sent - last_report >= 20480:
                last_report = sent
                pct = (sent * 100) // size
                print(f"[OTA] {pct}% ({sent}/{size})")
                set_status(f"OTA {pct}%")
        try:
            await self.client.stop_notify(OTA_UUID)
        except Exception:
            pass
        for _ in range(300):
            await asyncio.sleep(0.1)
            if not self.client or not self.client.is_connected:
                return True, "done"
        return False, "device didn't reboot"


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
    def __init__(self, parent, worker):
        super().__init__(parent)
        self.title("Fan-Mate Settings")
        self.worker = worker
        self.resizable(False, False)
        self.grab_set()
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

        section("🌬️  FAN")
        self.fan_mode = tk.StringVar(value=latest_config["fan"]["mode"])
        radio("Mode:", self.fan_mode, ["off", "on", "auto"])
        self.temp_on = tk.StringVar(value=str(latest_config["fan"]["tempOn"]))
        entry("Start at (°C):", self.temp_on)
        self.temp_full = tk.StringVar(value=str(latest_config["fan"]["tempFull"]))
        entry("Full at (°C):", self.temp_full)
        self.night_max = tk.StringVar(value=str(latest_config["fan"]["nightMax"]))
        entry("Night max (%):", self.night_max)

        section("🚨  ALARM")
        self.alarm_mode = tk.StringVar(value=latest_config["alarm"]["mode"])
        radio("Mode:", self.alarm_mode, ["off", "on", "auto"])
        self.alarm_warn = tk.StringVar(value=str(latest_config["alarm"]["warning"]))
        entry("Warning (°C):", self.alarm_warn)
        self.alarm_panic = tk.StringVar(value=str(latest_config["alarm"]["panic"]))
        entry("Panic (°C):", self.alarm_panic)

        section("🌙  NIGHT")
        self.night_mode = tk.StringVar(value=latest_config["night"]["mode"])
        radio("Mode:", self.night_mode, ["off", "on", "auto"])
        self.night_start = tk.StringVar(value=str(latest_config["night"]["start"]))
        entry("Start hour (0-23):", self.night_start)
        self.night_end = tk.StringVar(value=str(latest_config["night"]["end"]))
        entry("End hour (0-23):", self.night_end)

        section("📱  PHONE")
        self.phone_mode = tk.StringVar(value=latest_config["phone"]["mode"])
        radio("Mode:", self.phone_mode, ["off", "auto"])

        btn = tk.Frame(self)
        btn.grid(row=row, column=0, columnspan=3, pady=16)
        tk.Button(btn, text="Apply", width=10, command=self.apply).pack(side="left", padx=4)
        tk.Button(btn, text="Reset", width=10, command=self.reset).pack(side="left", padx=4)
        tk.Button(btn, text="Cancel", width=10, command=self.destroy).pack(side="left", padx=4)

    def apply(self):
        try:
            payload = {
                "fan": {
                    "mode":     self.fan_mode.get(),
                    "tempOn":   float(self.temp_on.get()),
                    "tempFull": float(self.temp_full.get()),
                    "nightMax": int(self.night_max.get()),
                },
                "alarm": {
                    "mode":    self.alarm_mode.get(),
                    "warning": float(self.alarm_warn.get()),
                    "panic":   float(self.alarm_panic.get()),
                },
                "night": {
                    "mode":  self.night_mode.get(),
                    "start": int(self.night_start.get()),
                    "end":   int(self.night_end.get()),
                },
                "phone": {
                    "mode":  self.phone_mode.get(),
                }
            }
        except ValueError as e:
            messagebox.showerror("Settings", f"Invalid value:\n{e}")
            return
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            print(f"[CFG] save failed: {e}")
        self.worker.send_config(payload)
        self.destroy()

    def reset(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.worker.send_config({"reset": True})
            self.destroy()


class App:
    def __init__(self, root):
        self.root = root
        root.title("🌀 Fan-Mate v2.24")
        root.resizable(False, False)
        self.theme = current_theme()
        self.is_day = is_daytime()

        self.prev_rx = get_rx_bytes("en1")
        self.current_rate = 0
        self.total_rx = self.prev_rx
        self.boost_enabled = tk.BooleanVar(value=True)
        self.boost_active = False
        self.boost_counter = 0
        self.saved_fan_mode = latest_config["fan"]["mode"]
        self.pending_boost = False

        init_log()

        mb = tk.Menu(root)
        am = tk.Menu(mb, tearoff=0)
        am.add_command(label="⚙️  Settings", command=self.menu_settings)
        am.add_separator()
        am.add_command(label="🌦️  Refresh Weather",
                       command=lambda: threading.Thread(target=fetch_weather, daemon=True).start())
        am.add_separator()
        am.add_command(label="📥  Sync Log", command=self.sync_log)
        am.add_command(label="📂  Open Log Folder", command=self.open_log_folder)
        am.add_command(label="🗑️  Clear Log on Device", command=self.clear_log)
        am.add_separator()
        am.add_command(label="📡  Update Firmware (BLE)", command=self.menu_ota)
        am.add_separator()
        am.add_command(label="🌗  Toggle Day/Night", command=self.toggle_theme)
        am.add_separator()
        am.add_command(label="❌  Quit", command=root.quit)
        mb.add_cascade(label="🌀 Fan-Mate", menu=am)
        root.config(menu=mb)

        self.title_lbl = tk.Label(root, text="🌀 Fan-Mate", font=FONT_TITLE)
        self.title_lbl.pack(pady=(16, 2))
        self.status_label = tk.Label(root, text="", font=("Helvetica Neue", 10, "italic"))
        self.status_label.pack(pady=(0, 8))

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

        self.temp_card = Card(root, self)
        self.temp_card.pack(fill="x", padx=18, pady=8)
        self.temp_title = tk.Label(self.temp_card, text="🌡️ PHONE TEMPERATURE", font=FONT_LABEL)
        self.temp_title.pack(pady=(10, 0))
        self.temp_lbl = tk.Label(self.temp_card, text="--.-°C", font=FONT_BIG)
        self.temp_lbl.pack(pady=(0, 10))

        self.fan_card = Card(root, self)
        self.fan_card.pack(fill="x", padx=18, pady=8)
        fr = tk.Frame(self.fan_card)
        fr.pack(fill="x", pady=10)
        self.fan_lbl  = self._col(fr, "💨 FAN",  "--")
        self._divider(fr)
        self.rpm_lbl  = self._col(fr, "⚙️ RPM",  "--")

        self.status_card = Card(root, self)
        self.status_card.pack(fill="x", padx=18, pady=8)
        sr = tk.Frame(self.status_card)
        sr.pack(fill="x", pady=10)
        self.phone_lbl = self._col(sr, "📱 PHONE", "--")
        self._divider(sr)
        self.alert_lbl = self._col(sr, "🚨 ALERT", "--")

        self.time_card = Card(root, self)
        self.time_card.pack(fill="x", padx=18, pady=8)
        self.time_lbl = tk.Label(self.time_card, text="--:--", font=("Helvetica Neue", 14, "bold"))
        self.time_lbl.pack(pady=10)

        self.data_card = Card(root, self)
        self.data_card.pack(fill="x", padx=18, pady=8)
        self.data_title = tk.Label(self.data_card, text="📥 DOWNLOAD (en1) + BOOST", font=FONT_LABEL)
        self.data_title.pack(pady=(8, 0))
        self.rate_lbl = tk.Label(self.data_card, text="0.0 KB/s", font=FONT_VALUE)
        self.rate_lbl.pack(pady=(2, 2))
        boost_fr = tk.Frame(self.data_card)
        boost_fr.pack(pady=(0, 6))
        tk.Checkbutton(boost_fr, text="Auto Boost (1.0 MB/s)", variable=self.boost_enabled,
                       font=FONT_TINY, command=self.on_boost_toggle).pack()
        self.boost_status_lbl = tk.Label(self.data_card, text="Boost: Ready", font=FONT_TINY)
        self.boost_status_lbl.pack(pady=(0, 6))
        self.data_graph = Graph(self.data_card, self, y_min=0, y_max=None, w=380, h=100)
        self.data_graph.pack(padx=6, pady=(0, 8))

        self.graph_card = Card(root, self)
        self.graph_card.pack(fill="x", padx=18, pady=8)
        self.graph_title = tk.Label(self.graph_card, text="📈 TEMPERATURE HISTORY", font=FONT_LABEL)
        self.graph_title.pack(pady=(8, 0))
        self.temp_graph = Graph(self.graph_card, self, y_min=15, y_max=55)
        self.temp_graph.pack(padx=6, pady=(4, 8))

        self.footer_lbl = tk.Label(root, text=f"GUI v{GUI_VERSION}  •  Interface: en1  •  Log: Documents/FanMate_temp_vs_data.csv",
                                   font=FONT_TINY)
        self.footer_lbl.pack(pady=(2, 10))

        self.apply_theme()
        self.worker = BLEWorker()
        self.worker.start()
        threading.Thread(target=weather_thread_loop, daemon=True).start()
        self.theme_check()
        self.tick()

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
            size_kb = len(r.content) / 1024
            lines = r.content.count(b"\n")
            print(f"[SYNC] {lines} lines, {size_kb:.1f} KB → {path}")
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
        if not messagebox.askyesno("Clear Log",
                "Delete log on ESP32?\n\nDownload it first!"):
            return
        try:
            r = requests.post(f"{FANMATE_URL}/log/clear", timeout=5)
            if r.status_code == 200:
                print("[LOG] cleared on device")
                messagebox.showinfo("Clear Log", "Log cleared on device.")
            else:
                messagebox.showerror("Clear Log", f"HTTP {r.status_code}")
        except Exception as e:
            messagebox.showerror("Clear Log", f"Failed:\n{e}")

    def on_boost_toggle(self):
        if not self.boost_enabled.get() and self.boost_active:
            self._set_fan_mode(self.saved_fan_mode)
            self.boost_active = False
            self.pending_boost = False
            self.boost_status_lbl.config(text="Boost: Off")

    def _set_fan_mode(self, mode):
        payload = {
            "fan": {
                "mode": mode,
                "tempOn": latest_config["fan"]["tempOn"],
                "tempFull": latest_config["fan"]["tempFull"],
                "nightMax": latest_config["fan"]["nightMax"],
            }
        }
        self.worker.send_config(payload)
        print(f"[BOOST] Fan mode → {mode}")

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
        self.boost_status_lbl.configure(bg=t["card"], fg=t["muted"])
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

    def menu_settings(self):
        SettingsDialog(self.root, self.worker)

    def menu_ota(self):
        if not os.path.isfile(BUILD_BIN):
            messagebox.showerror("OTA", f"Firmware not found:\n{BUILD_BIN}")
            return
        messagebox.showinfo("OTA", "OTA function is the same as previous version.")

    def tick(self):
        now_rx = get_rx_bytes("en1")
        diff = max(0, now_rx - self.prev_rx)
        self.current_rate = diff
        self.total_rx = now_rx
        self.prev_rx = now_rx
        download_hist.append(self.current_rate / 1024.0)

        if self.boost_enabled.get():
            if self.current_rate >= BOOST_THRESHOLD_BPS:
                self.boost_counter += 1
            else:
                self.boost_counter = max(0, self.boost_counter - 2)

            if self.boost_counter >= BOOST_HOLD_SECONDS and not self.boost_active:
                self.saved_fan_mode = latest_config["fan"]["mode"]
                self.pending_boost = True
                self.boost_active = True
                self.boost_status_lbl.config(text="Boost: Waiting for BLE…")
                print("[BOOST] Triggered – waiting for connection")

            if self.pending_boost and self.worker.client and self.worker.client.is_connected:
                self._set_fan_mode("on")
                self.pending_boost = False
                self.boost_status_lbl.config(text="Boost: ACTIVE 🔥")
                print("[BOOST] Fan forced ON")

            elif self.boost_counter == 0 and self.boost_active and not self.pending_boost:
                self._set_fan_mode(self.saved_fan_mode)
                self.boost_active = False
                self.boost_status_lbl.config(text="Boost: Ready")
                print("[BOOST] Returned to previous mode")
        else:
            self.boost_status_lbl.config(text="Boost: Off")

        if int(time.time()) % 5 == 0:
            log_data(latest.get("temp"), self.total_rx, self.current_rate, self.boost_active)

        t = self.theme
        d = latest
        temp = d.get("temp")
        if temp is None:
            self.temp_lbl.config(text="--.-°C  ❔", fg=t["muted"])
        else:
            em = temp_emoji(temp)
            c = t["green"] if temp < 25 else t["blue"] if temp < 35 else t["yellow"] if temp < 45 else t["red"]
            self.temp_lbl.config(text=f"{temp:.1f}°C  {em}", fg=c)

        fan_pct = int(d.get("fan", 0))
        fe = fan_emoji(fan_pct)
        self.fan_lbl.config(text=f"OFF {fe}" if fan_pct == 0 else f"{fan_pct}% {fe}",
                            fg=t["muted"] if fan_pct == 0 else t["green"])

        rpm = int(d.get("rpm", 0))
        self.rpm_lbl.config(text=f"{rpm}", fg=t["green"] if rpm > 0 else t["muted"])

        phone_mode = latest_config.get("phone", {}).get("mode", "auto")
        if phone_mode == "off":
            self.phone_lbl.config(text="DISABLED ⚙️", fg=t["muted"])
        else:
            phone = bool(d.get("phone", 0))
            self.phone_lbl.config(text="YES 📱" if phone else "NO  📴",
                                  fg=t["green"] if phone else t["muted"])

        alert = int(d.get("alert", 0))
        if alert == 2:
            self.alert_lbl.config(text="PANIC 🚨", fg=t["red"])
        elif alert == 1:
            self.alert_lbl.config(text="WARN ⚠️", fg=t["orange"])
        else:
            self.alert_lbl.config(text="OK ✅", fg=t["green"])

        self.weather_temp_lbl.config(text=f"{weather['temp']:.1f}°")
        self.weather_desc_lbl.config(text=weather["desc"])
        self.weather_range_lbl.config(text=f"⬆️ {weather['high']:.0f}°   ⬇️ {weather['low']:.0f}°")
        self.time_lbl.config(text=f"{local_time_str()}  {time_emoji()}")

        rate_kb = self.current_rate / 1024.0
        self.rate_lbl.config(text=f"{rate_kb/1024:.2f} MB/s" if rate_kb >= 1024 else f"{rate_kb:.1f} KB/s")

        self.temp_graph.trigger = latest_config.get("fan", {}).get("tempOn", None)
        self.temp_graph.set_data(temp_hist)
        self.data_graph.set_data(download_hist)

        self.status_label.config(text=get_status())
        self.root.after(1000, self.tick)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()