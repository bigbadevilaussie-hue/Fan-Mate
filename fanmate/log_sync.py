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
from . import osa_client


def log_sync_loop():
    """Pull sealed logs from ESP32, forward to OSA, delete local.

    v4.64: OSA is the single store. After a successful POST to OSA's
    /fan/log, the local file is removed so ~/Documents/FanMate_logs/
    stays empty. If OSA is down, the file is kept and retried next cycle.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    while True:
        # v4.64: forward any sealed CSVs sitting locally that OSA hasn't
        # seen. The ESP32 only serves files still in LittleFS, but we have
        # history back to Oct 11 in ~/Documents/FanMate_logs/ that needs
        # pushing too. Do this every cycle.
        try:
            for fname in sorted(os.listdir(LOG_DIR)):
                if not fname.startswith("log-") or not fname.endswith(".csv"):
                    continue
                local_path = os.path.join(LOG_DIR, fname)
                if not os.path.isfile(local_path):
                    continue
                try:
                    with open(local_path, "rb") as fh:
                        payload = fh.read()
                except Exception as e:
                    print(f"[LOG] read {fname}: {e}")
                    continue
                if not osa_client.post_log(fname, payload):
                    print(f"[LOG] OSA down, keeping {fname} locally")
                    continue
                try:
                    os.remove(local_path)
                except Exception:
                    pass
                print(f"[LOG] {fname} -> OSA ({len(payload)} bytes, backlog)")
        except Exception as e:
            print(f"[LOG] backlog pass: {e}")

        try:
            r = requests.get(f"{FANMATE_URL}/log/list", timeout=10)
            if r.status_code == 200:
                for entry in r.json():
                    fname = entry.get("name")
                    remote_crc = int(entry.get("crc", "0"), 16)
                    if not fname:
                        continue
                    local_path = os.path.join(LOG_DIR, fname)
                    payload = None

                    # Already have it locally? verify crc.
                    if os.path.exists(local_path):
                        with open(local_path, "rb") as fh:
                            local_crc = zlib.crc32(fh.read()) & 0xFFFFFFFF
                        if local_crc == remote_crc:
                            with open(local_path, "rb") as fh:
                                payload = fh.read()
                        else:
                            os.remove(local_path)

                    # Fetch from ESP32 if we don't have a valid local copy.
                    if payload is None:
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
                        payload = fr.content
                        # stage locally first so retries are cheap
                        tmp = local_path + ".part"
                        with open(tmp, "wb") as fh:
                            fh.write(payload)
                        os.rename(tmp, local_path)

                    # Forward to OSA
                    if not osa_client.post_log(fname, payload):
                        print(f"[LOG] OSA down, keeping {fname} locally")
                        continue

                    # OSA has it. ack the ESP32 and delete local copy.
                    requests.post(f"{FANMATE_URL}/log/ack",
                                  json={"name": fname}, timeout=5)
                    try:
                        os.remove(local_path)
                    except Exception:
                        pass
                    print(f"[LOG] {fname} -> OSA ({len(payload)} bytes)")
        except Exception as e:
            if DEBUG_GUI:
                print(f"[LOG] sync error: {e}")
        time.sleep(30)
