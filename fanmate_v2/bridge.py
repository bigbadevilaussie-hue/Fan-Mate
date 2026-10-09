"""
Fan-Mate GUI v2 — Python <-> QML bridge.
Wraps the existing fanmate/ backend. Does not touch it.
"""

import sys
import os
import threading
import requests

from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QObject, Signal, Property, QTimer, Slot, QUrl

# Reuse existing backend
sys.path.insert(0, os.path.expanduser("~/Documents/Arduino/fanmate"))
from fanmate import state
from fanmate.http_client import http_poll_loop
from fanmate.weather import weather_thread_loop


class Bridge(QObject):
    """Exposes /status fields to QML as properties + notify signals."""

    # Notify signals — QML binds to these for property updates
    tempChanged      = Signal()
    opalChanged      = Signal()
    fanChanged       = Signal()
    rpmChanged       = Signal()
    boostChanged     = Signal()
    boostLvlChanged  = Signal()
    tempLvlChanged   = Signal()
    killModeChanged  = Signal()
    fanStallChanged  = Signal()
    netChanged       = Signal()
    phoneChanged     = Signal()
    alertChanged     = Signal()
    fwChanged        = Signal()
    outdoorChanged   = Signal()
    roomChanged      = Signal()
    tempGear1Changed = Signal()
    tempGear2Changed = Signal()
    tempGear3Changed = Signal()
    tempGear4Changed = Signal()
    boostThresholdChanged = Signal()
    netHistChanged   = Signal()
    tempHistChanged  = Signal()
    rpmHistChanged   = Signal()
    serialChanged = Signal()
    otaProgress = Signal(int)
    otaDone     = Signal()
    otaUploading = Signal()
    otaStatus   = Signal(str)
    otaError    = Signal(str)

    def __init__(self):
        super().__init__()
        self._threads_started = False
        self._last = {}
        self._serial_text = ""

        # Start backend polling threads
        threading.Thread(target=http_poll_loop, daemon=True).start()
        threading.Thread(target=weather_thread_loop, daemon=True).start()

        # 5 Hz refresh — fast enough for smooth UI, light enough to not matter
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(200)

    def _get(self, key, default):
        v = state.latest.get(key, default)
        return default if v is None else v

    def _changed(self, key, value):
        if self._last.get(key) != value:
            self._last[key] = value
            return True
        return False

    def _refresh(self):
        if self._changed("temp", self._get("temp", 0.0)):
            self.tempChanged.emit()
        if self._changed("fan", self._get("fan", 0)):
            self.fanChanged.emit()
        if self._changed("rpm", self._get("rpm", 0)):
            self.rpmChanged.emit()
        if self._changed("boost", self._get("boost", 0)):
            self.boostChanged.emit()
        if self._changed("boost_lvl", self._get("boost_lvl", 0)):
            self.boostLvlChanged.emit()
        if self._changed("temp_lvl", self._get("temp_lvl", 0)):
            self.tempLvlChanged.emit()
        if self._changed("kill_mode", self._get("kill_mode", 0)):
            self.killModeChanged.emit()
        if self._changed("fan_stall", self._get("fan_stall", 0)):
            self.fanStallChanged.emit()
        if self._changed("net_kbps", self._get("net_kbps", 0.0)):
            self.netChanged.emit()
        if self._changed("phone", self._get("phone", 0)):
            self.phoneChanged.emit()
        if self._changed("alert", self._get("alert", 0)):
            self.alertChanged.emit()
        if self._changed("fw", self._get("fv", "?")):
            self.fwChanged.emit()
        if self._changed("opal", self._get("opal", 1)):
            self.opalChanged.emit()
        if self._changed("outdoor_c", self._get("outdoor_c", 0.0)):
            self.outdoorChanged.emit()
        if self._changed("room_c", self._get("room_c", -99.0)):
            self.roomChanged.emit()
        if self._changed("temp_gear1", self._get("temp_gear1", 30.0)):
            self.tempGear1Changed.emit()
        if self._changed("temp_gear2", self._get("temp_gear2", 32.0)):
            self.tempGear2Changed.emit()
        if self._changed("temp_gear3", self._get("temp_gear3", 34.0)):
            self.tempGear3Changed.emit()
        if self._changed("temp_gear4", self._get("temp_gear4", 36.0)):
            self.tempGear4Changed.emit()
        if self._changed("boost_threshold", self._get("boost_threshold", 900)):
            self.boostThresholdChanged.emit()

        # History arrays from device — change detection by last 5 values
        nh = state.latest.get("net_hist") or []
        th = state.latest.get("temp_hist") or []
        rh = state.latest.get("rpm_hist") or []
        nh_key = ",".join(str(x) for x in nh[-5:]) if nh else ""
        th_key = ",".join(str(x) for x in th[-5:]) if th else ""
        rh_key = ",".join(str(x) for x in rh[-5:]) if rh else ""
        if self._changed("net_hist_key", nh_key):
            self.netHistChanged.emit()
        if self._changed("temp_hist_key", th_key):
            self.tempHistChanged.emit()
        if self._changed("rpm_hist_key", rh_key):
            self.rpmHistChanged.emit()

    @Slot(str)
    def open_url(self, url):
        QDesktopServices.openUrl(QUrl(url))

    @Slot()
    def quit_app(self):
        from PySide6.QtWidgets import QApplication
        QApplication.quit()

    @Slot(str)
    def upload_firmware(self, path):
        threading.Thread(target=self._ota_worker, args=(path,), daemon=True).start()

    @Slot()
    def reboot_device(self):
        try:
            requests.get("http://fan-mate.local/reboot", timeout=5)
        except Exception:
            pass

    def _ota_worker(self, path):
        import os, shutil, time, base64, re as _re
        from datetime import datetime

        LOG_DIR = os.path.expanduser("~/Documents/FanMate_logs")
        REPO = os.path.expanduser("~/Documents/Arduino/fanmate")

        def emit(msg):
            self.otaStatus.emit(msg)

        try:
            # --- source version from Config.h ---
            src_ver = "?"
            try:
                cfg = open(os.path.join(REPO, "Config.h")).read()
                m = _re.search(r'#define\s+FAN_MATE_VERSION\s+"([^"]+)"', cfg)
                if m: src_ver = m.group(1)
            except Exception:
                pass

            size = os.path.getsize(path)
            emit("[OTA] version: " + src_ver)
            emit("[OTA] size: " + "{:,}".format(size) + " bytes")

            # --- 1. archive locally ---
            try:
                fw_dir = os.path.join(LOG_DIR, "firmware")
                os.makedirs(fw_dir, exist_ok=True)
                ts = datetime.now().strftime("%Y%m%d-%H%M")
                archived = os.path.join(fw_dir, "fanmate-v" + src_ver + "-" + ts + ".bin")
                shutil.copy2(path, archived)
                shutil.copy2(path, os.path.join(fw_dir, "fanmate-latest.bin"))
                emit("[OTA] archived: " + os.path.basename(archived))
            except Exception as e:
                emit("[OTA] archive failed: " + str(e))

            # --- 2. upload .bin to GitHub ---
            try:
                secrets_path = os.path.join(REPO, "secrets.h")
                secrets_text = open(secrets_path).read()
                def _secret(name):
                    m = _re.search(r'#define\s+' + name + r'\s+"([^"]+)"', secrets_text)
                    return m.group(1) if m else None
                tok = _secret("GITHUB_TOKEN")
                owner = _secret("GITHUB_OWNER")
                repo = _secret("GITHUB_REPO")
                branch = _secret("GITHUB_BRANCH")

                if not (tok and owner and repo and branch):
                    emit("[OTA] GitHub: token/owner/repo missing, skipping")
                else:
                    with open(path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("ascii")
                    bin_name = "fanmate.ino.bin"
                    url = "https://api.github.com/repos/" + owner + "/" + repo + "/contents/firmware/" + bin_name
                    headers = {
                        "Authorization": "Bearer " + tok,
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "Fan-Mate-GUI",
                    }
                    emit("[OTA] GitHub: checking...")
                    head = requests.get(url, headers=headers, timeout=15)
                    payload = {
                        "message": "firmware: v" + src_ver + " (" + bin_name + ")",
                        "content": b64,
                        "branch": branch,
                    }
                    if head.status_code == 200:
                        payload["sha"] = head.json().get("sha")
                    emit("[OTA] GitHub: uploading...")
                    r = requests.put(url, json=payload, headers=headers, timeout=60)
                    if r.status_code in (200, 201):
                        emit("[OTA] GitHub: uploaded (" + str(r.status_code) + ")")
                    else:
                        emit("[OTA] GitHub: failed HTTP " + str(r.status_code))
            except Exception as e:
                emit("[OTA] GitHub error: " + str(e))

            # --- 3. POST .bin to device ---
            emit("[OTA] uploading to device...")
            self.otaUploading.emit()
            t0 = time.time()
            try:
                from requests_toolbelt.multipart.encoder import MultipartEncoder, MultipartEncoderMonitor
                size_b = os.path.getsize(path)

                last_kb = [0]

                def _progress(monitor):
                    kb = monitor.bytes_read // 1024
                    if kb - last_kb[0] >= 128:
                        last_kb[0] = kb
                        pct = int(100 * monitor.bytes_read / size_b)
                        self.otaProgress.emit(pct)
                        emit("[OTA] device " + str(kb) + " KB / " + str(size_b // 1024) + " KB")

                with open(path, "rb") as f:
                    me = MultipartEncoder(fields={
                        "firmware": ("fanmate.ino.bin", f, "application/octet-stream")
                    })
                    mon = MultipartEncoderMonitor(me, _progress)
                    r = requests.post(
                        "http://192.168.8.242/ota",
                        data=mon,
                        headers={"Content-Type": mon.content_type},
                        timeout=120,
                    )
                dt = time.time() - t0
                if r.status_code == 200:
                    emit("[OTA] device HTTP 200 (" + "{:.1f}".format(dt) + "s)")
                    self.otaProgress.emit(100)
                else:
                    emit("[OTA] device HTTP " + str(r.status_code))
                    self.otaError.emit("HTTP " + str(r.status_code))
                    return
            except Exception as e:
                emit("[OTA] device error: " + str(e))
                self.otaError.emit(str(e))
                return

            # --- 4. wait for reboot ---
            emit("[OTA] rebooting...")
            time.sleep(5)
            back = False
            for i in range(30):
                try:
                    r = requests.get("http://192.168.8.242/status", timeout=2)
                    if r.status_code == 200:
                        fw = r.json().get("fw", "?")
                        emit("[OTA] device back, fw=" + str(fw))
                        back = True
                        break
                except Exception:
                    pass
                time.sleep(1)
            if not back:
                emit("[OTA] device did not return in 30s")

            emit("[OTA] done")
            self.otaDone.emit()

        except Exception as e:
            self.otaError.emit(str(e))

    # --- Properties exposed to QML ---

    @Property(float, notify=tempChanged)
    def temp(self):
        return float(self._get("temp", 0.0))

    @Property(int, notify=fanChanged)
    def fan(self):
        return int(self._get("fan", 0))

    @Property(int, notify=rpmChanged)
    def rpm(self):
        return int(self._get("rpm", 0))

    @Property(int, notify=boostChanged)
    def boost(self):
        return int(self._get("boost", 0))

    @Property(int, notify=boostLvlChanged)
    def boostLvl(self):
        return int(self._get("boost_lvl", 0))

    @Property(int, notify=tempLvlChanged)
    def tempLvl(self):
        return int(self._get("temp_lvl", 0))

    @Property(int, notify=killModeChanged)
    def killMode(self):
        return int(self._get("kill_mode", 0))

    @Property(int, notify=fanStallChanged)
    def fanStall(self):
        return int(self._get("fan_stall", 0))

    @Property(float, notify=netChanged)
    def netKbps(self):
        return float(self._get("net_kbps", 0.0))

    @Property(int, notify=phoneChanged)
    def phone(self):
        return int(self._get("phone", 0))

    @Property(int, notify=alertChanged)
    def alert(self):
        return int(self._get("alert", 0))

    @Property(str, notify=fwChanged)
    def fw(self):
        return str(self._get("fv", "?"))

    @Property(int, notify=opalChanged)
    def opal(self):
        return int(self._get("opal", 1))

    @Property(float, notify=outdoorChanged)
    def outdoor(self):
        return float(self._get("outdoor_c", 0.0))

    @Property(float, notify=roomChanged)
    def room(self):
        return float(self._get("room_c", -99.0))

    @Property(float, notify=tempGear1Changed)
    def tempGear1(self):
        return float(self._get("temp_gear1", 30.0))

    @Property(float, notify=tempGear2Changed)
    def tempGear2(self):
        return float(self._get("temp_gear2", 32.0))

    @Property(float, notify=tempGear3Changed)
    def tempGear3(self):
        return float(self._get("temp_gear3", 34.0))

    @Property(float, notify=tempGear4Changed)
    def tempGear4(self):
        return float(self._get("temp_gear4", 36.0))

    @Property(int, notify=boostThresholdChanged)
    def boostThreshold(self):
        return int(self._get("boost_threshold", 900))

    @Property(str, notify=netHistChanged)
    def netHistJson(self):
        import json as _json
        h = state.latest.get("net_hist") or []
        return _json.dumps(h)

    @Property(str, notify=tempHistChanged)
    def tempHistJson(self):
        import json as _json
        h = state.latest.get("temp_hist") or []
        return _json.dumps(h)

    @Property(str, notify=rpmHistChanged)
    def rpmHistJson(self):
        import json as _json
        h = state.latest.get("rpm_hist") or []
        return _json.dumps(h)


    # ---------- Firmware metadata for OTA confirmation dialog ----------

    def _fw_path(self):
        return os.path.expanduser(
            "~/Documents/Arduino/fanmate/build/esp32.esp32.esp32c3/fanmate.ino.bin")

    def _config_h_path(self):
        return os.path.expanduser("~/Documents/Arduino/fanmate/Config.h")

    @Property(str, constant=True)
    def firmwarePath(self):
        p = self._fw_path()
        return p if os.path.exists(p) else ""

    @Property(str, constant=True)
    def firmwareExists(self):
        return "1" if os.path.exists(self._fw_path()) else "0"

    @Property(str, constant=True)
    def firmwareSourceVer(self):
        import re as _re
        try:
            c = open(self._config_h_path()).read()
            m = _re.search(r'#define\s+FAN_MATE_VERSION\s+"([^"]+)"', c)
            return m.group(1) if m else "?"
        except Exception:
            return "?"

    @Property(str, constant=True)
    def firmwareSize(self):
        import os as _os
        p = self._fw_path()
        if not _os.path.exists(p):
            return "?"
        sz = _os.path.getsize(p)
        return "{:,} bytes ({:.2f} MB)".format(sz, sz / (1024 * 1024))

    @Property(str, constant=True)
    def firmwareMd5(self):
        import hashlib, os as _os
        p = self._fw_path()
        if not _os.path.exists(p):
            return "?"
        h = hashlib.md5()
        try:
            with open(p, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()[:16] + "..."
        except Exception:
            return "?"

    @Property(str, constant=True)
    def firmwareBuilt(self):
        import os as _os
        from datetime import datetime
        p = self._fw_path()
        if not _os.path.exists(p):
            return "?"
        return datetime.fromtimestamp(_os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")

    @Property(str, constant=True)
    def firmwareStale(self):
        import os as _os
        p = self._fw_path()
        c = self._config_h_path()
        if not _os.path.exists(p) or not _os.path.exists(c):
            return "0"
        return "1" if _os.path.getmtime(c) > _os.path.getmtime(p) else "0"

    @Property(str, notify=fwChanged)
    def deviceVersion(self):
        return str(self._get("fv", "?"))

    @Slot(str)
    def copyToClipboard(self, text):
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.clipboard().setText(text)


    # ---------- Serial ring buffer ----------

    @Property(str, constant=True)
    def serialUrl(self):
        return "http://192.168.8.242/serial"

    @Slot(result=str)
    def freshSerialUrl(self):
        import time
        return "http://192.168.8.242/serial?t=" + str(int(time.time()))

    @Property(str, notify=serialChanged)
    def serialText(self):
        return self._serial_text

    @Slot()
    def fetchSerial(self):
        try:
            r = requests.get("http://192.168.8.242/serial-raw", timeout=3)
            if r.status_code == 200:
                self._serial_text = r.text
                self.serialChanged.emit()
        except Exception:
            pass
