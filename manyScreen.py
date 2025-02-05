import logging
import os
import time
from datetime import datetime
from urllib.parse import urlparse

import psutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Base folder for storing screenshots
BASE_SCREENSHOT_FOLDER = os.path.join('static', 'screenshots')
os.makedirs(BASE_SCREENSHOT_FOLDER, exist_ok=True)

# Browser settings for desktop
chrome_options_desktop = Options()
chrome_options_desktop.add_argument("--headless")
chrome_options_desktop.add_argument("--hide-scrollbars")
chrome_options_desktop.add_argument('--no-sandbox')
chrome_options_desktop.add_argument('--disable-dev-shm-usage')
chrome_options_desktop.add_argument("--ignore-certificate-errors")

# Browser settings for mobile
chrome_options_mobile = Options()
chrome_options_mobile.add_argument("--headless")
chrome_options_mobile.add_argument("--window-size=375,812")  # iPhone X resolution
chrome_options_mobile.add_argument("--hide-scrollbars")
chrome_options_mobile.add_argument('--no-sandbox')
chrome_options_mobile.add_argument('--disable-dev-shm-usage')
chrome_options_mobile.add_argument("--ignore-certificate-errors")


def is_valid_url(url):
    """Checks the validity of the URL and adds 'http://' if the scheme is missing."""
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url
        parsed_url = urlparse(url)
    if all([parsed_url.scheme, parsed_url.netloc]):
        return url
    else:
        raise ValueError(f"Invalid URL: {url}. Ensure it's properly formatted with http:// or https://.")


def create_directory_for_domain(domain_name, date_str):
    """Creates a folder for screenshots for the given domain and date."""
    folder_path = os.path.join(BASE_SCREENSHOT_FOLDER, domain_name, date_str)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def create_device_specific_folders(domain_folder):
    """Creates device-specific folders for mobile and desktop screenshots."""
    mobile_folder = os.path.join(domain_folder, 'mobile')
    desktop_folder = os.path.join(domain_folder, 'desktop')
    os.makedirs(mobile_folder, exist_ok=True)
    os.makedirs(desktop_folder, exist_ok=True)
    return mobile_folder, desktop_folder


def get_all_links(driver):
    """Retrieves all links from the given page."""
    links = []
    attempts = 3
    for _ in range(attempts):
        try:
            elements = driver.find_elements(By.TAG_NAME, 'a')
            links = [element.get_attribute('href') for element in elements if element.get_attribute('href')]
            break
        except Exception as e:
            print(f"Error retrieving links: {e}")
            time.sleep(1)
    return links


def setup_logging(domain, date_str):
    """Sets up logging for the given domain and date."""
    log_folder = os.path.join(BASE_SCREENSHOT_FOLDER, domain, date_str)
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, 'log.txt')
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging


def take_full_page_screenshot(driver, filename, is_mobile=False):
    """Takes a full-page screenshot."""
    original_size = driver.get_window_size()
    total_width = driver.execute_script("return document.documentElement.scrollWidth")
    total_height = driver.execute_script("return document.documentElement.scrollHeight")

    driver.set_window_size(375 if is_mobile else total_width, total_height)
    time.sleep(5)
    driver.save_screenshot(filename)
    driver.set_window_size(original_size['width'], original_size['height'])


def kill_screenshot_process():
    current_process = psutil.Process()
    for child in current_process.children(recursive=True):
        if 'chrome' in child.name().lower():
            child.kill()


def visit_links_and_take_screenshots(url, device_type):
    global stop_screenshots
    stop_screenshots = False  # Reset the flag at the start

    url = is_valid_url(url)
    domain_name = urlparse(url).netloc.replace('www.', '').replace(':', '_')
    date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    domain_folder = create_directory_for_domain(domain_name, date_str)
    mobile_folder, desktop_folder = create_device_specific_folders(domain_folder)

    setup_logging(domain_name, date_str)

    options = chrome_options_desktop if device_type == 'desktop' else chrome_options_mobile
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(10)

        if device_type == 'desktop':
            driver.set_window_size(1920, 1080)
        main_screenshot_path = os.path.join(
            desktop_folder if device_type == 'desktop' else mobile_folder,
            f"main_page_{device_type}.png"
        )
        take_full_page_screenshot(driver, main_screenshot_path, is_mobile=(device_type == 'mobile'))

        links = list(set(get_all_links(driver)))
        processed_links = set()
        for i, link in enumerate(links):
            if stop_screenshots:
                break
            if link in processed_links:
                continue
            processed_links.add(link)
            try:
                driver.get(link)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                time.sleep(10)

                if device_type == 'desktop':
                    driver.set_window_size(1920, 1080)
                screenshot_path = os.path.join(
                    desktop_folder if device_type == 'desktop' else mobile_folder,
                    f"screen_{i + 1}_{device_type}.png"
                )
                take_full_page_screenshot(driver, screenshot_path, is_mobile=(device_type == 'mobile'))
            except Exception as e:
                print(f"Error capturing screenshot for {link}: {str(e)}")
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
    finally:
        driver.quit()
