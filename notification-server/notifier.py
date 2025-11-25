from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from playsound import playsound
from dotenv import load_dotenv
from hue import Hue
import websockets
import logging
import asyncio
import time
import os


# TODO: Rename program
# TODO: Startup script

def flashLightsRed(hue: Hue, times: int):
    for _ in range(times):
        hue.turnOffAllLights()
        time.sleep(0.5)
        hue.setAllLights(65000)
        time.sleep(0.5)
    hue.restoreAllLightState()


def shortFlashLightsGreen(hue: Hue):
    hue.turnOffAllLights()
    time.sleep(0.5)
    hue.setAllLights(29000)
    time.sleep(4)
    hue.restoreAllLightState()


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} - {levelname} - {message}",
        style="{", datefmt="%Y-%m-%d %H:%M")

    logging.info("Starting donation monitor...")

    # Load environment variables
    load_dotenv()
    START_VALUE = int(os.environ.get("START_VALUE") or "0")
    MH_URL = os.environ.get("MH_URL")
    CHROMEDRIVER_PATH = os.environ.get("CHROME_DRIVER_PATH")
    WS_URL = os.environ.get("WEBSOCKET_SERVER_URL")
    REFRESH_RATE = int(os.environ.get("REFRESH_RATE") or "5")  # seconds
    HUE_BRIDGE_IP = os.environ.get("HUE_BRIDGE_IP" or "")
    DONATION_SOUND_PATH = "./soundfiles/snyggtbyggt.mp3"
    SPRINT_DONATION_SOUND_PATH = "./soundfiles/sandstorm.mp3"

    try:
        ws_connection = await websockets.connect(uri=WS_URL, ping_timeout=None)
        logging.info("Connected to WS server")
    except Exception as e:
        logging.error(f"Error connecting to WS server: {e}")
        exit(1)

    # Setup Hue
    hue = Hue(bridgeIp=HUE_BRIDGE_IP)
    hue.getLights()
    hue.saveAllLightState()

    # Setup Selenium Scraper
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(MH_URL)
    time.sleep(5)  # Give page time to load
    logging.info("Page loaded, scraper started.")

    previous_value: int = START_VALUE
    try:
        while True:
            try:
                # FOR TESTING
                # previous_value = 0

                driver.refresh()
                # Wait for the spinner element to disappear, i.e. the raised amount has been loaded
                WebDriverWait(driver, 30).until_not(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "entry-amount-module--spinnerWrapper--70e75")))

                # Find charity total element
                charity_total_element = driver.find_element(
                    By.CLASS_NAME, "entry-amount-module--amount--5ecff")

                if charity_total_element.text:
                    logging.info(
                        f"Current charity total: {charity_total_element.text}")

                    # Formatting
                    total_text = charity_total_element.text[:-2].replace(
                        ' ', '')
                    current_value = int(total_text)

                    if current_value > previous_value:
                        donation = current_value - previous_value
                        logging.info(f"Donation detected: {donation} kr")

                        if (current_value - previous_value) >= 200:
                            # Sprint donation event
                            payload = {"event": "sprint_donation",
                                       "message": f"🎉 SPRINT DONATION! {donation} kr 🎉"}
                            await ws_connection.send(str(payload))
                            _ = await ws_connection.recv()  # Hold for response
                            playsound(SPRINT_DONATION_SOUND_PATH, block=False)
                            logging.info("Sprint donation event sent")
                            flashLightsRed(hue, 5)

                        else:
                            # Regular donation event
                            payload = {"event": "donation",
                                       "message": f"En hjälte skänkte {donation} kr"}
                            await ws_connection.send(str(payload))
                            _ = await ws_connection.recv()  # Hold for response
                            playsound(DONATION_SOUND_PATH, block=False)
                            logging.info("Donation event sent")
                            shortFlashLightsGreen(hue)

                        previous_value = current_value
                        with open("current_value.txt", "w", encoding="utf-8") as f:
                            f.write(f"{current_value} kr")
                            f.close()
                else:
                    logging.error("Charity total not found")

            except Exception as e:
                logging.error("Unexpected exception while scraping:", e)

            time.sleep(REFRESH_RATE)

    except KeyboardInterrupt:
        logging.info("Clearing up resources and exiting...")
        await ws_connection.close()
        driver.quit()
        service.stop()
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())
