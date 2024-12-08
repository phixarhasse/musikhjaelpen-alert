import logging
import requests


class Hue:
    def __init__(self, bridgeIp: str = ""):
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                            level=logging.DEBUG, datefmt="%Y-%m-%d %H:%M:%S")
        if (bridgeIp == ""):
            logging.error("Hue bridge IP not provided.")
            quit(1)

        self.bridgeIp = bridgeIp
        self.url = f"http://{self.bridgeIp}/api"
        self.lights = []
        self.lightsStartingState = []
        self.username = ""
        self.loadUsername()
        if (self.username == ""):
            logging.info("Waiting for Hue authorization...")
            self.authorize()
            logging.info("---> Hue Authorization complete!")

    def saveUsername(self, username):
        try:
            f = open("hue_username", "x")
            f.write(username)
            f.close()
        except Exception as e:
            logging.error(e)

    def loadUsername(self):
        try:
            f = open("hue_username", "r")
            self.username = f.readline()
            f.close()
        except Exception as e:
            logging.error(e)
            self.username = ""
            return

    def authorize(self):
        self.username = ""
        try:
            hueResponse = requests.post(
                self.url, json={"devicetype": "mh_donation_notification"})
            # Need to generate username
            if (hueResponse.json()[0]["error"]["type"] == 101):
                logging.info(
                    "\tPlease press the link button on the HUE Bridge.")
                user_input = input("Have you pressed it? [y/n] ")
                if (not user_input == 'y'):
                    logging.info("\tHue authentication cancelled. Exiting.")
                    quit(0)
                else:
                    hueResponse = requests.post(
                        self.url, json={"devicetype": "mh_donation_notification"})
                    username = hueResponse.json()[0]["success"]["username"]
                    self.username = username
                    self.saveUsername(username)
            elif (hueResponse.ok):
                username = hueResponse.json()[0]["success"]["username"]
                self.username = username
                self.saveUsername(username)
            logging.info(f"Hue username stored")
        except Exception as e:
            logging.error("Error during Hue authentication.")
            logging.error("Exception: ", e)
            quit(1)

    def getLights(self):
        self.lights = []
        if (self.username == ""):
            return
        try:
            hueResponse = requests.get(f"{self.url}/{self.username}/lights/")
            if (not hueResponse.ok):
                logging.warning("Unable to get Hue lights.")
                return
        except Exception as e:
            logging.error(e)
            return
        for light in hueResponse.json():
            self.lights.append(light)
        return

    def saveAllLightState(self):
        if (self.username == ""):
            return
        if (len(self.lights) == 0):
            self.getLights()
        try:
            for light in self.lights:
                hueResponse = requests.get(
                    f"{self.url}/{self.username}/lights/{light}")
                self.lightsStartingState.append(
                    {"light": light, "state": hueResponse.json()["state"]})
            logging.info("Hue lights states stored.")
            return
        except Exception as e:
            logging.error("Unable to store Hue light states", e)
            return

    def restoreAllLightState(self):
        if (self.username == ""):
            return
        if (len(self.lightsStartingState) == 0):
            logging.error("No light states to restore.")
            return
        try:
            for light in self.lightsStartingState:
                hueResponse = requests.put(
                    f"{self.url}/{self.username}/lights/{light['light']}/state",
                    json=light["state"])
                logging.debug(
                    f"Hue light {light['light']}: {hueResponse.status_code}")
            logging.info("Hue lights states restored.")
            return
        except Exception as e:
            logging.error("Unable to restore Hue light states", e)

    def setAllLights(self, color: int):
        try:
            for light in self.lights:
                hueResponse = requests.put(
                    f"{self.url}/{self.username}/lights/{light}/state",
                    json={"on": True, "sat": 254, "bri": 200, "hue": color})
                logging.debug(f"Hue light {light}: {hueResponse.status_code}")
        except Exception as e:
            logging.error(e)
            return

    def turnOffAllLights(self):
        try:
            for light in self.lights:
                hueResponse = requests.put(
                    f"{self.url}/{self.username}/lights/{light}/state",
                    json={"on": False})
                logging.debug(f"Hue light {light}: {hueResponse.status_code}")
        except Exception as e:
            logging.error(e)
            return
