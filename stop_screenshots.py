import os
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

stop_screenshots = False


def take_screenshots(url):
    global stop_screenshots
    stop_screenshots = False  # Reset the flag at the start

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(10)

        screenshot_dir = os.path.join('static', 'screenshots', urlparse(url).netloc)
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, 'screenshot.png')
        driver.save_screenshot(screenshot_path)

        # Check the stop_screenshots flag
        if stop_screenshots:
            return

        # Additional screenshot logic here...

    except Exception as e:
        print(f"Error taking screenshot: {e}")
    finally:
        driver.quit()
