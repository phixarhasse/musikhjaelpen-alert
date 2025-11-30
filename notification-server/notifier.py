from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from playsound import playsound
from dotenv import load_dotenv
from hue_client import HueClient
import websockets
import logging
import asyncio
import time
import os


# TODO: Rename program
# TODO: Startup script

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} - {levelname} - {message}",
        style="{", datefmt="%Y-%m-%d %H:%M")


    logging.info("Starting donation monitor...")

    # Load environment variables
    load_dotenv()
    START_VALUE = int(os.environ.get("START_VALUE") or "0")
    MH_URL = os.environ.get("MH_URL") or ""
    WS_URL = os.environ.get("WEBSOCKET_SERVER_URL") or "ws://localhost:8765"
    REFRESH_RATE = int(os.environ.get("REFRESH_RATE") or "5")  # seconds
    DONATION_SOUND_PATH = "./soundfiles/snyggtbyggt.mp3"
    SPRINT_DONATION_SOUND_PATH = "./soundfiles/sandstorm.mp3"

    try:
        ws_connection = await websockets.connect(uri=WS_URL, ping_timeout=None)
        logging.info("Connected to WS server")
    except Exception as e:
        logging.error(f"Error connecting to WS server: {e}")
        exit(1)

    # Setup Hue
    hue = HueClient()
    hue.initialize()

    # Setup Selenium Scraper
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(MH_URL)
    time.sleep(2)  # Give page time to load
    # Try to accept cookie consent overlays that can block the amount element
    try:
        _try_accept_cookie(driver)
    except Exception:
        logging.debug("Cookie accept attempt failed during initial load", exc_info=True)
    logging.info("Page loaded, scraper started.")

    previous_value: int = START_VALUE
    try:
        while True:
            try:
                # FOR TESTING
                # previous_value = 0

                driver.refresh()
                # Try to accept cookie consent overlays after refresh
                try:
                    _try_accept_cookie(driver)
                except Exception:
                    logging.debug("Cookie accept attempt failed after refresh", exc_info=True)
                # Wait for the spinner element to disappear, i.e. the raised amount has been loaded
                WebDriverWait(driver, timeout=30).until_not(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "entry-amount-module--spinnerWrapper--70e75")))

                # Wait for the charity total element text to be non-empty
                charity_total_element = WebDriverWait(driver, timeout=30).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "entry-amount-module--amount--5ecff")))
                WebDriverWait(driver, timeout=30).until(
                    lambda d: d.find_element(By.CLASS_NAME, "entry-amount-module--amount--5ecff").text != "")

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
                            hue.rainbow_blink()

                        else:
                            # Regular donation event
                            payload = {"event": "donation",
                                       "message": f"En hjälte skänkte {donation} kr"}
                            await ws_connection.send(str(payload))
                            _ = await ws_connection.recv()  # Hold for response
                            playsound(DONATION_SOUND_PATH, block=False)
                            logging.info("Donation event sent")
                            hue.flash_all_green()

                        previous_value = current_value
                        with open("current_value.txt", "w", encoding="utf-8") as f:
                            f.write(f"{current_value} kr")
                            f.close()
                else:
                    logging.error("Charity total not found")

            except Exception as e:
                # Handle Selenium timeouts separately so we can continue polling
                if isinstance(e, TimeoutException):
                    logging.warning("Timed out waiting for elements on the page; will retry")
                    driver.save_screenshot(f"timeout_{int(time.time())}.png")
                else:
                    # Log full traceback for unexpected errors
                    logging.exception("Unexpected exception while scraping")

            time.sleep(REFRESH_RATE)

    except KeyboardInterrupt:
        logging.info("Clearing up resources and exiting...")
        await ws_connection.close()
        driver.quit()
        exit(0)

def _try_accept_cookie(driver, timeout_seconds: float = 2.0) -> bool:
    """Best-effort: click the cookie consent accept button if present.

    Prioritize the specific class you found (`primary-button-module--primaryButtonStyle--cab94`).
    Returns True if a click was performed, False otherwise.
    """
    # Target the exact class first (common on this site), then fall back to
    # a few generic patterns if needed.
    xpaths = [
        "//button[contains(@class, 'primary-button-module--primaryButtonStyle--cab94')]",
        "//button[contains(@class, 'cookie') or contains(@class, 'consent') or contains(@id, 'cookie')]",
        "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept')]",
    ]

    end = time.time() + timeout_seconds
    for xp in xpaths:
        try:
            elems = driver.find_elements(By.XPATH, xp)
        except Exception:
            elems = []

        for el in elems:
            try:
                if not el.is_displayed():
                    continue
                el.click()
                time.sleep(0.25)
                return True
            except Exception:
                continue

        if time.time() > end:
            break

    logging.debug("No cookie accept button found for tried xpaths")
    return False


if __name__ == "__main__":
    asyncio.run(main())
