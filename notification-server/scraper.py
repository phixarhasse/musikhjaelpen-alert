from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import json
import time
import os
import asyncio
import itertools
import websockets
import websockets.connection
from websockets.exceptions import ConnectionClosed


async def keepalive(websocket, ping_interval=30):
    for ping in itertools.count():
        await asyncio.sleep(ping_interval)
        try:
            await websocket.send(json.dumps({"ping": ping}))
        except ConnectionClosed:
            break


async def main():
    print("Starting donation monitor...")
    load_dotenv()
    previous_value = int(os.environ.get("START_VALUE") or "0")
    url = os.environ.get("MH_URL")  # URL to scrape
    # Path to ChromeDriver executable
    chrome_driver_path = os.environ.get("CHROME_DRIVER_PATH")

    ws_connection = await websockets.connect(uri="ws://localhost:8765", ping_timeout=None)
    print("Connected to WS server")
    # await ws_connection.send("Hello, world!")
    # greeting = await ws_connection.recv()
    # print(f"websocket says < {greeting}")

    # Set up Chrome options
    chrome_options = Options()
    # Run Chrome in headless mode (without opening a browser window)
    chrome_options.add_argument("--headless")

    # Initialize the Chrome browser
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Open the webpage using Selenium
    driver.get(url)
    time.sleep(5)  # Give page time to load
    print("Page loaded, scraper started.")

    try:
        while True:
            try:
                driver.refresh()
                # Wait for the spinner element to disappear, i.e. the raised amount has been loaded
                WebDriverWait(driver, 30).until_not(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "entry-amount-module--spinnerWrapper--70e75"))
                )

                charity_total_element = driver.find_element(
                    By.CLASS_NAME, "entry-amount-module--amount--5ecff")

                if charity_total_element.text:
                    print(
                        f"Current charity total: {charity_total_element.text}")
                    total_text = charity_total_element.text[:-2].replace(
                        ' ', '')
                    current_value = int(total_text)
                    if current_value > previous_value:
                        donation = current_value - previous_value
                        print(
                            f"-----> SOMEONE DONATED {donation} kr!")
                        previous_value = current_value
                        with open("current_value.txt", "w", encoding="utf-8") as f:
                            f.write(f"{current_value} kr")
                            f.close()

                        if (current_value - previous_value >= 200):
                            payload = {
                                "message": f"🎉 TUBRO DONATION! {donation} kr 🎉"}
                            print(payload)
                            await ws_connection.send(str(payload))
                            reply = await ws_connection.recv()
                            print(f"Received: {reply}")
                        else:
                            payload = {
                                "message": f"En hjälte skänte {donation} kr"}
                            await ws_connection.send(str(payload))
                            reply = await ws_connection.recv()
                            print(f"Received: {reply}")
                else:
                    print("Charity total not found")

            except Exception as e:
                print("Error:", e)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nClearing up resources and exiting gracefully...")
        driver.quit()
        service.stop()
        await ws_connection.close()
        exit(0)


if __name__ == "__main__":
    asyncio.run(main())
