from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import requests
import time
import os


def main():
    print("Starting scraper...")
    load_dotenv()
    previous_value = int(os.environ.get("START_VALUE") or "0")
    url = os.environ.get("MH_URL")  # URL to scrape
    # Path to ChromeDriver executable
    chrome_driver_path = os.environ.get("CHROME_DRIVER_PATH")

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
                        print(
                            f"-----> SOMEONE DONATED {current_value-previous_value} kr!")
                        previous_value = current_value
                        with open("current_value.txt", "w", encoding="utf-8") as f:
                            f.write(f"{current_value} kr")
                            f.close()
                        _ = requests.post("http://localhost:5000/donation")
                else:
                    print("Charity total not found")

            except Exception as e:
                print("Error:", e)

            time.sleep(5)

    except KeyboardInterrupt:
        print("\nClearing up resources and exiting gracefully...")
        driver.quit()
        service.stop()
        exit(0)


main()
