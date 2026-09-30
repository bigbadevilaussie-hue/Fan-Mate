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
    otaProgress = Signal(int)
    otaStatus   = Signal(str)
    otaError    = Signal(str)

    def __init__(self):
        super().__init__()
        self._threads_started = False
        self._last = {}

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
        if self._changed("boost_threshold", self._get("boost_threshold", 700)):
            self.boostThresholdChanged.emit()

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
        import os
        try:
            size = os.path.getsize(path)
            self.otaStatus.emit("Uploading {} bytes...".format(size))

            def progress_hook(monitor):
                # called by requests during upload
                try:
                    pct = int(100 * monitor.bytes_read / monitor.len)
                    self.otaProgress.emit(pct)
                except Exception:
                    pass

            with open(path, "rb") as f:
                files = {"firmware": ("fanmate.ino.bin", f, "application/octet-stream")}
                r = requests.post(
                    "http://fan-mate.local/ota",
                    files=files,
                    timeout=120
                )

            if r.status_code == 200:
                self.otaStatus.emit("Done — device rebooting")
                self.otaProgress.emit(100)
            else:
                self.otaError.emit("HTTP {}".format(r.status_code))

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
        return int(self._get("boost_threshold", 700))
