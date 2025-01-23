import os
import time
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

BASE_SCREENSHOT_FOLDER = os.path.join('static', 'screenshots')
os.makedirs(BASE_SCREENSHOT_FOLDER, exist_ok=True)


def is_valid_url(url):
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url
        parsed_url = urlparse(url)
    if all([parsed_url.scheme, parsed_url.netloc]):
        return url
    else:
        raise ValueError(f"Invalid URL: {url}")


def create_directory_for_domain(domain_name):
    folder_path = os.path.join(BASE_SCREENSHOT_FOLDER, domain_name)
    os.makedirs(folder_path, exist_ok=True)
    return folder_path


def take_screenshot(driver, filename):
    driver.save_screenshot(filename)


def get_all_links(driver):
    links = driver.find_elements(By.TAG_NAME, 'a')
    return [link.get_attribute('href') for link in links if link.get_attribute('href')]


def visit_links_and_take_screenshots(url, device_type):
    url = is_valid_url(url)
    domain_name = urlparse(url).netloc.replace('www.', '').replace(':', '_')
    domain_folder = create_directory_for_domain(domain_name)

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    if device_type == 'desktop':
        driver.set_window_size(1920, 1080)
    elif device_type == 'mobile':
        driver.set_window_size(375, 812)

    driver.get(url)
    time.sleep(3)

    main_screenshot_path = os.path.join(domain_folder, f"main_page_{device_type}.png")
    take_screenshot(driver, main_screenshot_path)

    links = get_all_links(driver)
    for i, link in enumerate(links):
        try:
            driver.get(link)
            time.sleep(3)
            screenshot_path = os.path.join(domain_folder, f"screen_{i + 1}_{device_type}.png")
            take_screenshot(driver, screenshot_path)
        except Exception as e:
            print(f"Error capturing screenshot for {link}: {e}")

    driver.quit()
