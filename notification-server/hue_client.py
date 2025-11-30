import json
import logging
from dotenv import load_dotenv
import os
import time
from typing import List

import urllib3
import requests

# Suppress insecure TLS warnings (requests/urllib3) since verify=False is used locally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class Encoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)

class HueClient:
    """Simple Hue CLIP v2 client.

    Responsibilities:
    - initialize(): fetch and store available light IDs and their initial state
    - flash_all_green(): flash all lights green N times over a duration
    - rainbow_fade(): fade through a set of colors over a duration
    """

    def __init__(self, bridge_ip: str | None = None, appkey: str | None = None, username: str | None = None):
        logging.basicConfig(
            format="%(asctime)s %(levelname)s: %(message)s",
            level=logging.DEBUG,
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        load_dotenv()

        self.bridge_ip = bridge_ip or os.environ.get("HUE_BRIDGE_IP")
        if not self.bridge_ip:
            raise ValueError("Bridge IP must be provided either by argument or HUE_BRIDGE_IP env var")

        self.appkey = appkey or username or os.environ.get("HUE_APPKEY")
        if not self.appkey:
            raise ValueError("Hue appkey not found. Provide as arg or env var HUE_APPKEY")

        self.base_url = f"https://{self.bridge_ip}/clip/v2/resource"
        self.base_url_v1 = f"https://{self.bridge_ip}/api/{self.appkey}"
        self.headers = {
            "hue-application-key": self.appkey,
            "Content-Type": "application/json",
        }

        # Public state
        self.lights: List[str] = []

    def initialize(self) -> None:
        """Fetch all light resources and capture a minimal initial state for each light."""
        try:
            resp = requests.get(f"{self.base_url}/light", headers=self.headers, verify=False)
            if not resp.ok:
                logging.warning(f"initialize: failed to list lights: {resp.status_code} {resp.text}")
                return

            data = resp.json().get("data", [])
            self.lights = []

            for item in data:
                light_id = item.get("id")
                if not light_id:
                    continue

                # GET the full resource for consistent state fields
                resp_light = requests.get(f"{self.base_url}/light/{light_id}", headers=self.headers, verify=False)
                if not resp_light.ok:
                    logging.debug(f"initialize: could not GET light {light_id}: {resp_light.status_code}")
                    continue

                light_data = resp_light.json().get("data", [])
                if not light_data:
                    continue

                # The resource object is usually in the first array element
                self.lights.append(light_id)

            logging.debug(f"initialize: found lights: {self.lights}")
        except Exception as e:
            logging.error("initialize: exception while initializing lights: %s", e)

    def _put_light_state(self, light_id: str, state: dict) -> None:
        try:
            payload = json.dumps(self._normalize_state_for_put(state), cls=Encoder)
            resp = requests.put(f"{self.base_url}/light/{light_id}", headers=self.headers, data=payload, verify=False)
            if not resp.ok:
                logging.debug(f"_put_light_state: light {light_id} -> {resp.status_code} {resp.text}")
        except Exception as e:
            logging.error("_put_light_state: exception for %s: %s", light_id, e)

    def flash_group1(self) -> None:
        try:
            payload = json.dumps({"alert": "lselect"})
            resp = requests.put(f"{self.base_url_v1}/groups/1/action", headers=self.headers, data=payload, verify=False)
            if not resp.ok:
                logging.debug("flash_group1: group 1 -> %s %s", resp.status_code, resp.text)
        except Exception as e:
            logging.error("flash_group1: exception while flashing group 1: %s", e)


    def _normalize_state_for_put(self, state: dict) -> dict:
        """Ensure state is safe for PUT. Specifically, effects_v2 must contain action.effect per API."""
        if not state:
            return state
        s = dict(state)
        ev = s.get("effects_v2")
        if ev is None:
            return s
        # If effects_v2 is present but malformed, normalize
        if isinstance(ev, dict):
            action = ev.get("action") or ev.get("Action") or {}
            if not isinstance(action, dict):
                action = {}
            if "effect" not in action or action.get("effect") is None:
                action["effect"] = "no_effect"
            ev["action"] = action
            s["effects_v2"] = ev
        else:
            # unexpected; replace with no_effect action
            s["effects_v2"] = {"action": {"effect": "no_effect"}}
        return s

    def _set_all(self, state: dict) -> None:
        # Update all lights individually (grouped updates removed for simplicity)
        for lid in list(self.lights):
            self._put_light_state(lid, state)

    def restore_all_to_prism(self) -> None:
        """Restore all lights to the prism effect."""
        # Instead of restoring each light's original state, always set the Prism effect
        prism_state = {"effects_v2": {"action": {"effect": "prism"}}}
        self._set_all(prism_state)

    def flash_all_green(self) -> None:
        """Flash all lights green.
        """
        if not self.lights:
            logging.warning("flash_all_green: no lights initialized. Call initialize() first.")
            return

        green_state = {"dimming": {"brightness": 78.66}, "color": {"xy": {"x": 0.1673, "y": 0.5968}}}

        try:
            self._set_all(green_state)
            time.sleep(0.5)
            self.flash_group1()
            time.sleep(8)
        finally:
            self.restore_all_to_prism()

    def rainbow_blink(self, duration: float = 5.0) -> None:
        if not self.lights:
            logging.warning("rainbow_blink: no lights initialized. Call initialize() first.")
            return

        if duration <= 0:
            return

        try:
            self.restore_all_to_prism()
            time.sleep(0.2)
            self.flash_group1()
            time.sleep(8)
        finally:
            self.restore_all_to_prism()


if __name__ == "__main__":
    # Quick manual test/high-level usage example
    c = HueClient()
    c.initialize()
    print("Lights:", c.lights)
