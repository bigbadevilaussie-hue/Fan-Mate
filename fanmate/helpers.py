# Fan-Mate helper functions

import re
import requests

from .config import (
    CONFIG_H,
    FANMATE_URL,
    DAY_START_HOUR,
    DAY_END_HOUR,
    THEME_DAY,
    THEME_NIGHT,
)
from . import state

from datetime import datetime


def is_daytime():
    return DAY_START_HOUR <= datetime.now().hour < DAY_END_HOUR
def current_theme():
    return THEME_DAY if is_daytime() else THEME_NIGHT
def set_status(m):
    with state.status_lock:
        state.status_msg = m
def get_status():
    with state.status_lock:
        return state.status_msg
def read_target_version():
    try:
        with open(CONFIG_H) as f:
            m = re.search(r'#define\s+FAN_MATE_VERSION\s+"([^"]+)"', f.read())
            return m.group(1) if m else "?"
    except Exception:
        return "?"
def read_device_version():
    try:
        r = requests.get(f"{FANMATE_URL}/status", timeout=3)
        if r.status_code == 200:
            return r.json().get("fw", "?")
    except Exception:
        pass
    return "?"
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
def phone_temp_emoji(t):
    if t is None: return "❔"
    if t < 30: return "🙂"
    if t < 33: return "🌡️"
    if t < 36: return "🥵"
    return "🔥"
def fan_emoji(p):
    if p == 0:  return "💤"
    if p < 30:  return "🍃"
    if p < 70:  return "💨"
    return "🌪️"


def is_night_now():
    """True if current local time is in the night window."""
    from .config import NIGHT_START_HOUR, NIGHT_END_HOUR
    h = datetime.now().hour
    if NIGHT_START_HOUR < NIGHT_END_HOUR:
        return NIGHT_START_HOUR <= h < NIGHT_END_HOUR
    return h >= NIGHT_START_HOUR or h < NIGHT_END_HOUR
