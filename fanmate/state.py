# Fan-Mate shared runtime state

from collections import deque
import threading

from .config import HIST_LEN

temp_hist     = deque([None] * HIST_LEN, maxlen=HIST_LEN)
download_hist = deque([None] * HIST_LEN, maxlen=HIST_LEN)

latest = {
    "temp": None, "fan": 0, "rpm": 0, "phone": 0, "alert": 0,
    "boost": 0, "fv": "?", "net_kbps": 0.0,
    "sleep": 0, "sleep_countdown": 0, "opal": 1, "fan_stall": 0,
}
latest_config = {
    "temp": {"gear1": 30.0, "gear2": 32.0, "gear3": 34.0, "gear4": 36.0, "hysteresis": 1.0},
    "boost": {
        "mode": 1,
        "normal": {"threshold": 700, "on_hold": 4, "off_hold": 4},
        "aggr":   {"threshold": 400, "on_hold": 2, "off_hold": 8},
    },
    "night": {"start": 22, "end": 7, "nightMax": 75},
    "phone": {"mode": "off"},
}
connected = False
time_synced = False
_http_ever_connected = False
status_msg = ""
status_lock = threading.RLock()

FONT_TITLE   = ("Helvetica Neue", 24, "bold")
FONT_SECTION = ("Helvetica Neue", 10)
FONT_BIG     = ("Helvetica Neue", 34, "bold")
FONT_VALUE   = ("Helvetica Neue", 15, "bold")
FONT_LABEL   = ("Helvetica Neue", 9, "bold")
FONT_TINY    = ("Helvetica Neue", 9)

