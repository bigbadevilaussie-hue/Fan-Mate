# Fan-Mate ESP32 log synchronisation

import os
import zlib
import json
import time
import urllib.request
import requests

from .config import FANMATE_URL, LOG_DIR, DEBUG_GUI
from . import state
from .helpers import set_status


def log_sync_loop():
    os.makedirs(LOG_DIR, exist_ok=True)
    while True:
        try:
            r = requests.get(f"{FANMATE_URL}/log/list", timeout=10)
            if r.status_code == 200:
                for entry in r.json():
                    fname = entry.get("name")
                    remote_crc = int(entry.get("crc", "0"), 16)
                    if not fname:
                        continue
                    local_path = os.path.join(LOG_DIR, fname)

                    if os.path.exists(local_path):
                        with open(local_path, "rb") as fh:
                            local_crc = zlib.crc32(fh.read()) & 0xFFFFFFFF
                        if local_crc == remote_crc:
                            requests.post(f"{FANMATE_URL}/log/ack",
                                          json={"name": fname}, timeout=5)
                            continue
                        os.remove(local_path)

                    fr = requests.get(f"{FANMATE_URL}/log/file",
                                      params={"name": fname}, timeout=60)
                    if fr.status_code != 200:
                        continue
                    actual_crc = zlib.crc32(fr.content) & 0xFFFFFFFF
                    if actual_crc != remote_crc:
                        requests.post(f"{FANMATE_URL}/log/nack",
                                      json={"name": fname, "reason": "crc"},
                                      timeout=5)
                        continue

                    tmp = local_path + ".part"
                    with open(tmp, "wb") as fh:
                        fh.write(fr.content)
                    os.rename(tmp, local_path)

                    requests.post(f"{FANMATE_URL}/log/ack",
                                  json={"name": fname}, timeout=5)
                    print(f"[LOG] synced {fname} ({len(fr.content)} bytes)")
        except Exception as e:
            if DEBUG_GUI:
                print(f"[LOG] sync error: {e}")
        time.sleep(30)
