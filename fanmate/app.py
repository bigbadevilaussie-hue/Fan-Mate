# Fan-Mate main application

import tkinter as tk
from tkinter import messagebox

import threading
import time
import requests

from .config import *
from . import state
from .state import (
    temp_hist,
    download_hist,
    latest,
    latest_config,
    status_msg,
    status_lock,
    FONT_TITLE,
    FONT_SECTION,
    FONT_BIG,
    FONT_VALUE,
    FONT_LABEL,
    FONT_TINY,
)
from .state import (
    FONT_TITLE,
    FONT_SECTION,
    FONT_BIG,
    FONT_VALUE,
    FONT_LABEL,
    FONT_TINY,
)
from .helpers import *
from .weather import weather, weather_thread_loop
from .http_client import *
from .log_sync import *
from .widgets import *
from .dialogs import *
from .reports import *


class App:
    def __init__(self, root):
        self.root = root
        root.title(f"🌀 Fan-Mate v{GUI_VERSION}")
        root.resizable(False, False)

        try:
            icon_path = os.path.join(FANMATE_DIR, "fanmate.png")
            if os.path.exists(icon_path):
                _icon = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, _icon)
                root._icon_ref = _icon
                print("[ICON] loaded")
        except Exception as e:
            print(f"[ICON] {e}")

        self.theme = current_theme()
        self.is_day = is_daytime()
        self.turbo_phase = 0

        mb = tk.Menu(root)
        am = tk.Menu(mb, tearoff=0)
        am.add_command(label="⚙️  Settings", command=self.menu_settings)
        am.add_command(label="🌐  Open Serial Page", command=self.open_serial_page)
        am.add_command(label="📍  Open Dashboard", command=self.open_dashboard)
        am.add_separator()
        reports = tk.Menu(am, tearoff=0)
        reports.add_command(label="Last 2 Hours", command=self.menu_report_2h)
        reports.add_command(label="Daily",        command=self.menu_report_daily)
        reports.add_command(label="Weekly",       command=self.menu_report_weekly)
        am.add_cascade(label="📊  Reports", menu=reports)
        am.add_separator()
        am.add_command(label="🎛️  Dyna Tune", command=self.menu_dyna_tune)
        am.add_separator()
        am.add_command(label="📡  Update Firmware", command=self.menu_ota)
        am.add_separator()
        am.add_command(label="🌗  Toggle Day/Night", command=self.toggle_theme)
        am.add_separator()
        am.add_command(label="❌  Quit", command=root.quit)
        mb.add_cascade(label="🌀 Fan-Mate", menu=am)
        root.config(menu=mb)

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
        self.fan_lbl = self._col(fr, "💨 FAN", "--")
        self._divider(fr)
        self.rpm_lbl = self._col(fr, "⚙️ RPM", "--")

        self.boost_temp_card = Card(root, self)
        self.boost_temp_card.pack(fill="x", padx=18, pady=8)
        bt = tk.Frame(self.boost_temp_card)
        bt.pack(fill="x", pady=10)
        self.boost_lbl = self._col(bt, "🏎️ BOOST", "Parked")
        self._divider(bt)
        self.temp_level_lbl = self._col(bt, "🌡️ TEMP", "Normal")

        self.bottom_card = Card(root, self)
        self.bottom_card.pack(fill="x", padx=18, pady=8)
        br = tk.Frame(self.bottom_card)
        br.pack(fill="x", pady=10)
        self.outdoor_lbl = self._col(br, "📍 OUT", "--.-°")
        self._divider(br)
        self.room_lbl = self._col(br, "🏠 ROOM", "--.-°")
        self._divider(br)
        self.phone_lbl = self._col(br, "📱 PHONE", "--")
        self._divider(br)
        self.time_lbl = self._col(br, "🕐 TIME", "--:--")

        self.data_card = Card(root, self)
        self.data_card.pack(fill="x", padx=18, pady=8)
        self.data_title = tk.Label(self.data_card, text="📥 NETWORK RATE", font=FONT_LABEL)
        self.data_title.pack(pady=(8, 0))
        self.rate_lbl = tk.Label(self.data_card, text="-- KB/s", font=FONT_VALUE)
        self.rate_lbl.pack(pady=(2, 6))
        self.data_graph = Graph(self.data_card, self, y_min=0, y_max=2048, w=380, h=100)
        self.data_graph.pack(padx=6, pady=(0, 8))

        self.graph_card = Card(root, self)
        self.graph_card.pack(fill="x", padx=18, pady=8)
        self.graph_title = tk.Label(self.graph_card, text="📈 TEMPERATURE HISTORY", font=FONT_LABEL)
        self.graph_title.pack(pady=(8, 0))
        self.temp_graph = Graph(self.graph_card, self, y_min=15, y_max=55)
        self.temp_graph.pack(padx=6, pady=(4, 8))

        self.footer_lbl = tk.Label(
            root,
            text=f"GUI v{GUI_VERSION}  ·  FW {latest.get('fv', '?')}",
            font=FONT_TINY,
        )
        self.footer_lbl.pack(pady=(2, 10))

        self.apply_theme()

        threading.Thread(target=http_poll_loop, daemon=True).start()
        threading.Thread(target=log_sync_loop, daemon=True).start()
        threading.Thread(target=weather_thread_loop, daemon=True).start()

        self.theme_check()
        self.tick()

    def menu_settings(self):
        SettingsDialog(self.root, self)

    def open_serial_page(self):
        import webbrowser
        webbrowser.open(f"{FANMATE_URL}/serial")

    def open_dashboard(self):
        import webbrowser
        webbrowser.open(f"{FANMATE_URL}/")

    def menu_report_2h(self):
        Report2H(self.root, self)

    def menu_report_daily(self):
        ReportDaily(self.root, self)

    def menu_report_weekly(self):
        ReportWeekly(self.root, self)

    def menu_dyna_tune(self):
        DynaTune(self.root, self)

    def menu_ota(self):
        if not os.path.isfile(BUILD_BIN):
            messagebox.showerror(
                "OTA",
                f"Firmware not found:\n{BUILD_BIN}\n\n"
                f"Run Sketch → Export Compiled Binary in Arduino IDE first."
            )
            return

        src_ver = read_target_version()
        try:
            bin_mtime = os.path.getmtime(BUILD_BIN)
            cfg_mtime = os.path.getmtime(CONFIG_H)
            stale = cfg_mtime > bin_mtime
        except Exception:
            stale = False
            bin_mtime = 0

        size = os.path.getsize(BUILD_BIN)
        md5 = compute_md5(BUILD_BIN) or "?"
        dev_ver = read_device_version()
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

        threading.Thread(target=self._ota_worker,
                         args=(src_ver,),
                         daemon=True).start()

    def _ota_worker(self, src_ver):
        print("=" * 50)
        print(f"[OTA] starting")
        print(f"[OTA] version: {src_ver}")
        print(f"[OTA] size:    {os.path.getsize(BUILD_BIN):,} bytes")

        try:
            import shutil
            fw_dir = os.path.join(LOG_DIR, "firmware")
            os.makedirs(fw_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M")
            archived = os.path.join(fw_dir, f"fanmate-v{src_ver}-{ts}.bin")
            shutil.copy2(BUILD_BIN, archived)
            shutil.copy2(BUILD_BIN, os.path.join(fw_dir, "fanmate-latest.bin"))
            print(f"[OTA] archived: {archived}")
        except Exception as e:
            print(f"[OTA] archive failed: {e}")

        print(f"[OTA] uploading...")
        t0 = time.time()
        try:
            with open(BUILD_BIN, "rb") as f:
                r = requests.post(f"{FANMATE_URL}/ota",
                                  files={"firmware": f},
                                  timeout=120)
            dt = time.time() - t0
            print(f"[OTA] HTTP {r.status_code} ({dt:.1f}s)")

            if r.status_code != 200:
                self.root.after(0, lambda: messagebox.showerror(
                    "OTA", f"Failed: HTTP {r.status_code}"))
        except Exception as e:
            print(f"[OTA] EXCEPTION: {e}")
            err = str(e)
            self.root.after(0, lambda m=err: messagebox.showerror(
                "OTA", f"Failed:\n{m}"))

        print("[OTA] done")
        print("=" * 50)

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
        for card in (self.temp_card, self.fan_card,
                     self.boost_temp_card, self.bottom_card,
                     self.data_card, self.graph_card):
            card.apply_theme()
        self.footer_lbl.configure(bg=t["bg"], fg=t["muted"])
        for lbl in (self.temp_title, self.graph_title, self.data_title):
            lbl.configure(bg=t["card"], fg=t["muted"])
        self.temp_lbl.configure(bg=t["card"])
        self.rate_lbl.configure(bg=t["card"], fg=t["fg"])
        for holder in (self.fan_card, self.boost_temp_card, self.bottom_card):
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

    def tick(self):
        t = self.theme
        d = latest

        self.turbo_phase = (self.turbo_phase + 1) % 4
        sleep = d.get("sleep", 0)
        countdown = d.get("sleep_countdown", 0)
        boost = d.get("boost", 0)
        opal = d.get("opal", 1)
        alert = d.get("alert", 0)
        stall = d.get("fan_stall", 0)
        temp_lvl  = d.get("temp_lvl", 0)
        boost_lvl = d.get("boost_lvl", 0)

        temp = d.get("temp")
        if temp is None:
            self.temp_lbl.config(text="--.-°C  ❔", fg=t["muted"])
        else:
            em = phone_temp_emoji(temp)
            c = (t["green"] if temp < 25 else t["blue"] if temp < 35
                 else t["yellow"] if temp < 45 else t["red"])
            self.temp_lbl.config(text=f"{temp:.1f}°C  {em}", fg=c)

        fan_pct = int(d.get("fan", 0))
        night_now = is_night_now()
        if night_now and fan_pct > 0:
            fe = "💤"
            fcolor = t["blue"]
        else:
            fe = fan_emoji(fan_pct)
            fcolor = t["muted"] if fan_pct == 0 else t["green"]
        self.fan_lbl.config(
            text=f"OFF {fe}" if fan_pct == 0 else f"{fan_pct}% {fe}",
            fg=fcolor,
        )
        rpm = int(d.get("rpm", 0))
        self.rpm_lbl.config(text=f"{rpm}", fg=t["green"] if rpm > 0 else t["muted"])

        phone_mode = latest_config.get("phone", {}).get("mode", "off")
        if phone_mode == "off":
            self.phone_lbl.config(text="BENCH 🧪", fg=t["muted"])
        else:
            phone = bool(d.get("phone", 0))
            self.phone_lbl.config(
                text="YES 📱" if phone else "NO  📴",
                fg=t["green"] if phone else t["muted"],
            )

        # BOOST level name
        bl = int(d.get("boost_lvl", 0))
        boost_names  = ["Parked", "Cruising", "Fast", "Racing", "Nitro"]
        boost_colors = [t["muted"], t["green"], t["yellow"], t["orange"], t["red"]]
        self.boost_lbl.config(text=boost_names[bl], fg=boost_colors[bl])

        # TEMP level name
        tl = int(d.get("temp_lvl", 0))
        temp_names  = ["Normal", "Warm", "Hot", "Hotter", "Critical"]
        temp_colors = [t["green"], t["yellow"], t["orange"], t["orange"], t["red"]]
        self.temp_level_lbl.config(text=temp_names[tl], fg=temp_colors[tl])

        # weather card removed; outdoor temp goes into bottom card
        od = d.get("outdoor_c")
        if od is not None and od > -90:
            self.outdoor_lbl.config(text=f"{od:.1f}°")
        else:
            self.outdoor_lbl.config(text="--.-°")

        rc = d.get("room_c")
        if rc is not None and rc > -90:
            self.room_lbl.config(text=f"{rc:.1f}°")
        else:
            self.room_lbl.config(text="--.-°")

        self.time_lbl.config(text=f"{local_time_str()}  {time_emoji()}")

        rate_kbps = float(d.get("net_kbps", 0.0))
        if rate_kbps >= 1024:
            self.rate_lbl.config(text=f"{rate_kbps/1024:.2f} MB/s")
        else:
            self.rate_lbl.config(text=f"{rate_kbps:.1f} KB/s")

        self.footer_lbl.config(
            text=f"GUI v{GUI_VERSION}  ·  FW {d.get('fv', '?')}"
        )
        self.temp_graph.trigger = latest_config.get("temp", {}).get("warning", None)
        self.temp_graph.set_data(temp_hist)

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

