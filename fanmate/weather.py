# Fan-Mate weather

import json
import time
import urllib.request

from .config import (
    WEATHER_LAT,
    WEATHER_LON,
    WEATHER_TZ,
    WEATHER_REFRESH_SEC,
    DEBUG_GUI,
)

from . import state


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
        if DEBUG_GUI:
            print(f"[WEATHER] {e}")


def weather_thread_loop():
    while True:
        fetch_weather()
        time.sleep(WEATHER_REFRESH_SEC)
