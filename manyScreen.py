import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

# Directory to save screenshots
SCREENSHOT_DIR = 'static/screenshots'


def take_screenshots(url):
    # Create a timestamped directory for the screenshots
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_dir = os.path.join(SCREENSHOT_DIR, timestamp)
    os.makedirs(save_dir, exist_ok=True)

    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    # Initialize the WebDriver
    service = Service('path/to/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Open the main URL
        driver.get(url)
        time.sleep(2)  # Wait for the page to load

        # Take a screenshot of the main page
        main_screenshot_path = os.path.join(save_dir, 'main_page.png')
        driver.save_screenshot(main_screenshot_path)

        # Find all links on the main page
        links = driver.find_elements(By.TAG_NAME, 'a')
        visited_links = set()

        for link in links:
            href = link.get_attribute('href')
            if href and href not in visited_links and url in href:
                visited_links.add(href)
                driver.get(href)
                time.sleep(2)  # Wait for the page to load

                # Take a screenshot of the subpage
                subpage_screenshot_path = os.path.join(save_dir, f'{href.split("/")[-1]}.png')
                driver.save_screenshot(subpage_screenshot_path)

                # Go back to the main page
                driver.back()
                time.sleep(2)  # Wait for the page to load

    finally:
        driver.quit()

    return save_dir
