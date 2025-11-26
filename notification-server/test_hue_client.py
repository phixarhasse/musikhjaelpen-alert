#!/usr/bin/env python3
"""Simple test runner for `HueClient`.

Usage examples (PowerShell):

# Simulate all requests (safe, no bridge required)
$env:PYTHONPATH="."; python .\test_hue_client.py --simulate

# Run against real bridge using `HUE_IP` and `hue_username` file
$env:PYTHONPATH="."; python .\test_hue_client.py

# Or pass bridge and username explicitly
$env:PYTHONPATH="."; python .\test_hue_client.py --bridge 192.168.1.10 --username mykey
"""
import argparse
import time
import sys

from hue_client import HueClient


class DummyResponse:
    def __init__(self, ok=True, status_code=200, data=None, text=""):
        self.ok = ok
        self.status_code = status_code
        self._data = data if data is not None else {"data": []}
        self.text = text

    def json(self):
        return self._data


def make_mock_functions():
    # Simple mocked behaviour for GET /light and GET /light/{id}
    def mock_get(url, headers=None, verify=None):
        # list lights
        if url.rstrip("/").endswith("/light"):
            return DummyResponse(data={"data": [{"id": "light-1"}, {"id": "light-2"}]})

        # single light
        if "/light/" in url:
            lid = url.rsplit("/", 1)[-1]
            return DummyResponse(data={"data": [{"id": lid, "dimming": {"brightness": 50}, "color": {"xy": {"x": 0.5, "y": 0.5}}}]})

        return DummyResponse()

    def mock_put(url, headers=None, data=None, verify=None):
        print(f"MOCK PUT: {url} -> payload: {data}")
        return DummyResponse(ok=True, status_code=200, text="OK")

    return mock_get, mock_put


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bridge", help="Bridge IP (overrides HUE_IP env var)")
    p.add_argument("--username", help="Hue username (overrides hue_username file)")
    p.add_argument("--simulate", action="store_true", help="Simulate requests (no bridge needed)")
    p.add_argument("--no-flash", action="store_true", help="Skip flashing during test")
    p.add_argument("--no-rainbow", action="store_true", help="Skip rainbow during test")
    args = p.parse_args()

    if args.simulate:
        import requests

        mock_get, mock_put = make_mock_functions()
        # Back up original functions so we can restore later
        requests_get_orig = requests.get
        requests_put_orig = requests.put
        requests.get = mock_get
        requests.put = mock_put
        print("Running in SIMULATE mode — no real network calls will be made.")
    else:
        requests_get_orig = requests_put_orig = None

    try:
        client = HueClient(bridge_ip=args.bridge, appkey=args.username)
    except Exception as e:
        print("Failed to create HueClient:", e)
        if args.simulate and requests_get_orig is not None:
            import requests as _r
            _r.get = requests_get_orig
            _r.put = requests_put_orig
        sys.exit(1)

    print("Initializing lights...")
    client.initialize()
    print("Found lights:", client.lights)

    try:
        if not args.no_flash:
            print("Flashing all green 3 times over 5 seconds...")
            client.flash_all_green(flashes=3)
            time.sleep(1)

        if not args.no_rainbow:
            print("Running rainbow fade for 10 seconds...")
            client.rainbow_fade()

        print("Final restore to initial states...")
        client.restore_all_to_prism()
        print("Done.")

    except KeyboardInterrupt:
        print("Interrupted — restoring lights and exiting.")
        client.restore_all_to_prism()

    finally:
        if args.simulate and requests_get_orig is not None:
            import requests as _r

            _r.get = requests_get_orig
            _r.put = requests_put_orig


if __name__ == "__main__":
    main()
