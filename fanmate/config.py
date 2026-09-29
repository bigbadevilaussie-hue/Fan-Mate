# Fan-Mate configuration/constants

import os

GUI_VERSION = "3.81"
FANMATE_URL = "http://fan-mate.local"
FANMATE_DIR = os.path.expanduser("~/Documents/Arduino/fanmate")
BUILD_DIR   = os.path.join(FANMATE_DIR, "build", "esp32.esp32.esp32c3")
BUILD_BIN   = os.path.join(BUILD_DIR, "fanmate.ino.bin")
CONFIG_H    = os.path.join(FANMATE_DIR, "Config.h")
LOG_DIR     = os.path.expanduser("~/Documents/FanMate_logs")

POLL_INTERVAL = 10.0
DEBUG_GUI = False

WEATHER_LAT = -27.4219
WEATHER_LON = 152.4339
WEATHER_TZ  = "Australia%2FBrisbane"
WEATHER_REFRESH_SEC = 300
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

NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 7
NIGHT_MAX_PCT = 75
