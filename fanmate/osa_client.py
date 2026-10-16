"""OSA Server client for the Tk GUI.

All file transfers to/from the Mac now route through OSA.
OSA is the single store; the GUI no longer talks to GitHub.
"""
import os
import requests

OSA_URL = "http://192.168.8.187:9999"
OSA_TIMEOUT = 10


def post_log(name, raw_bytes):
    """POST a sealed log CSV to OSA. Returns True on success."""
    try:
        r = requests.post(f"{OSA_URL}/fan/log",
                          params={"name": name},
                          data=raw_bytes,
                          headers={"Content-Type": "application/octet-stream"},
                          timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"[OSA] post_log {name}: {e}")
        return False


def post_bin(name, raw_bytes):
    """POST a firmware .bin to OSA. OSA archives + forwards OTA."""
    try:
        r = requests.post(f"{OSA_URL}/fan/bin",
                          params={"name": name},
                          data=raw_bytes,
                          headers={"Content-Type": "application/octet-stream"},
                          timeout=180)
        return r.status_code == 200
    except Exception as e:
        print(f"[OSA] post_bin {name}: {e}")
        return False


def post_config(name, raw_bytes):
    """POST a config snapshot CSV to OSA."""
    try:
        r = requests.post(f"{OSA_URL}/fan/config",
                          params={"name": name},
                          data=raw_bytes,
                          headers={"Content-Type": "application/octet-stream"},
                          timeout=30)
        return r.status_code == 200
    except Exception as e:
        print(f"[OSA] post_config {name}: {e}")
        return False


def list_files(kind):
    """GET the file list for a kind (logs|config|firmware|hb)."""
    try:
        r = requests.get(f"{OSA_URL}/fan/files/list",
                         params={"kind": kind},
                         timeout=OSA_TIMEOUT)
        if r.status_code == 200:
            return r.json().get("files", [])
    except Exception as e:
        print(f"[OSA] list_files {kind}: {e}")
    return []


def get_file(kind, name):
    """GET raw bytes of a file. Returns bytes or None."""
    try:
        r = requests.get(f"{OSA_URL}/fan/files",
                         params={"kind": kind, "name": name},
                         timeout=30)
        if r.status_code == 200:
            return r.content
    except Exception as e:
        print(f"[OSA] get_file {kind}/{name}: {e}")
    return None


def push_now():
    try:
        requests.post(f"{OSA_URL}/fan/push_now", timeout=5)
    except Exception:
        pass
