# Fan-Mate ESP32 HTTP client

import json
import time
import urllib.request
import requests

from .config import FANMATE_URL, POLL_INTERVAL, DEBUG_GUI
from . import state
from .state import latest, latest_config, temp_hist, download_hist, connected, _http_ever_connected, time_synced, status_lock
from .helpers import set_status


def http_poll_loop():
    poll_count = 0
    last_config_fetch = 0.0
    while True:
        poll_count += 1
        try:
            r = requests.get(f"{FANMATE_URL}/status", timeout=10)
            if r.status_code == 200:
                try:
                    d = r.json()
                except Exception as e:
                    if DEBUG_GUI:
                        print(f"[POLL #{poll_count}] JSON FAIL: {e}")
                    time.sleep(POLL_INTERVAL)
                    continue

                if DEBUG_GUI:
                    print(f"[POLL #{poll_count}] net={d.get('net_kbps')} "
                          f"temp={d.get('temp')} fan={d.get('fan')} boost={d.get('boost')}")

                latest["temp"]      = d.get("temp")
                latest["fan"]       = d.get("fan", 0)
                latest["rpm"]       = d.get("rpm", 0)
                latest["phone"]     = d.get("phone", 0)
                latest["alert"]     = d.get("alert", 0)
                latest["boost"]     = d.get("boost", 0)
                latest["boost_lvl"] = d.get("boost_lvl", 0)
                latest["fv"]        = d.get("fw", "?")
                latest["net_kbps"]  = float(d.get("net_kbps", 0.0))
                latest["sleep"]     = d.get("sleep", 0)
                latest["sleep_countdown"] = d.get("sleep_countdown", 0)
                latest["opal"]      = d.get("opal", 1)
                latest["outdoor_c"] = d.get("outdoor_c", 0.0)
                latest["room_c"]    = d.get("room_c", -99.0)
                latest["fan_stall"] = d.get("fan_stall", 0)
                latest["temp_lvl"]  = d.get("temp_lvl", 0)

                if latest["temp"] is not None:
                    temp_hist.append(float(latest["temp"]))
                download_hist.append(latest["net_kbps"])

                if not state.connected:
                    state.connected = True
                    if not state._http_ever_connected:
                        state._http_ever_connected = True
                        print(f"[HTTP] connected {FANMATE_URL}")
                    fetch_config()
                    last_config_fetch = time.time()
                    if not state.time_synced:
                        sync_time_once()
                elif time.time() - last_config_fetch >= 300:
                    fetch_config()
                    last_config_fetch = time.time()

                set_status("connected")
            else:
                state.connected = False
                set_status(f"HTTP {r.status_code}")
        except Exception as e:
            state.connected = False
            set_status("disconnected")
            latest["boost"] = 0
            latest["sleep"] = 0
            latest["sleep_countdown"] = 0
            latest["fan_stall"] = 0
            latest["room_c"] = -99.0
            latest["temp_lvl"] = 0
        time.sleep(POLL_INTERVAL)


def sync_time_once():
    try:
        r = requests.post(
            f"{FANMATE_URL}/time",
            json={"epoch": int(time.time())},
            timeout=3,
        )
        if r.status_code == 200:
            state.time_synced = True
            print("[TIME] synced to ESP32")
    except Exception as e:
        if DEBUG_GUI:
            print(f"[TIME] failed: {e}")


def fetch_config():
    try:
        r = requests.get(f"{FANMATE_URL}/config", timeout=10)
        if r.status_code != 200:
            return None
        d = r.json()
        for sec in ("temp", "boost", "night"):
            if sec in d:
                latest_config.setdefault(sec, {}).update(d[sec])
        if "temp" not in latest_config:
            latest_config["temp"] = {"warning": 32.0, "panic": 34.0, "kill": 36.0}
        return latest_config
    except Exception as e:
        if DEBUG_GUI:
            print(f"[CFG] fetch failed: {e}")
        return None


