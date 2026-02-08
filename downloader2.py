
import signal
import sys

sentinel_file = Path("ts_segments/.shutdown")

def signal_handler(sig, frame):
    print('\n[INFO] Stopping downloader and notifying aggregator...')
    sentinel_file.touch()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

import requests
from pathlib import Path
from urllib.parse import urljoin
import time

# Configuration
m3u8_url = "https://stream.radiofrance.fr/franceinfo/franceinfo_hifi.m3u8?id=radiofrance"
base_url = "https://stream.radiofrance.fr"
ts_folder = Path("ts_segments")
ts_folder.mkdir(exist_ok=True)
seen = set()

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def get_playlist(url):
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    lines = r.text.splitlines()
    print(f"[INFO] Retrieved playlist with {len(lines)} lines")
    return lines

while True:
    try:
        lines = get_playlist(m3u8_url)

        # Pick up all .ts lines
        ts_urls = [line for line in lines if ".ts" in line and not line.startswith("#")]

        if not ts_urls:
            print("[WARN] No .ts segments found in playlist.")
            time.sleep(2)
            continue

        for ts in ts_urls:
            ts_name = ts.split("/")[-1].split("?")[0]  # filename without query string
            if ts_name in seen:
                continue
            seen.add(ts_name)

            ts_full_url = urljoin(base_url, ts)
            ts_path = ts_folder / ts_name

            print(f"[INFO] Downloading {ts_full_url} -> {ts_path}")
            resp = requests.get(ts_full_url, headers=HEADERS, stream=True)
            with open(ts_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"[INFO] Saved {ts_path}")

    except Exception as e:
        print("[ERROR]", e)

    time.sleep(1)
