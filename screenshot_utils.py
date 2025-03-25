import logging
import os
import threading
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

# Global variables for thread management
screenshot_thread = None
stop_screenshots = False
stop_screenshots_lock = threading.Lock()


def get_screenshots(screenshots_dir):
    """Get all screenshots organized by domain and device type."""
    screenshots = {}
    for dirpath, dirnames, filenames in os.walk(screenshots_dir):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            screenshots[dirname] = [f for f in os.listdir(dir_full_path) if
                                    os.path.isfile(os.path.join(dir_full_path, f))]
    return screenshots


def is_valid_url(url):
    """
    Checks the validity of the URL and adds 'http://' if the scheme is missing.
    Performs enhanced validation to ensure URL is safe and well-formed.
    """
    if not url:
        raise ValueError("URL cannot be empty.")
        
    if not isinstance(url, str):
        raise ValueError(f"URL must be a string, received {type(url).__name__}")
    
    # Obsługa URL bez schematu
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url
        parsed_url = urlparse(url)
    
    # Sprawdzenie, czy URL jest poprawnie sformułowany
    if not parsed_url.scheme or not parsed_url.netloc:
        raise ValueError(f"Invalid URL: {url}. Ensure it's properly formatted with http:// or https://.")
    
    # Sprawdź, czy schemat jest dozwolony
    if parsed_url.scheme not in ['http', 'https']:
        raise ValueError(f"Invalid URL scheme: {parsed_url.scheme}. Only http and https are supported.")
    
    # Sprawdź, czy adres nie zawiera niebezpiecznych znaków
    unsafe_chars = ['<', '>', '"', "'", '%', '{', '}', '|', '\\', '^', '~', '[', ']', '`']
    for char in unsafe_chars:
        if char in url:
            raise ValueError(f"URL contains unsafe character: {char}")
    
    # Sprawdź, czy domena nie jest pusta
    if not parsed_url.netloc:
        raise ValueError(f"URL domain cannot be empty: {url}")
    
    return url


def create_directory_for_domain(domain_name):
    """Creates device-specific folders for the given domain."""
    domain_folder = os.path.join(BASE_SCREENSHOT_FOLDER, domain_name)
    mobile_folder = os.path.join(domain_folder, 'mobile')
    desktop_folder = os.path.join(domain_folder, 'desktop')
    os.makedirs(mobile_folder, exist_ok=True)
    os.makedirs(desktop_folder, exist_ok=True)
    return mobile_folder, desktop_folder


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
    if stop_screenshots:
        return


def get_all_links(driver, base_url=None):
    """Retrieves all links from the given page, excluding mailto, image files, and specific keywords."""
    links = []
    attempts = 3
    for _ in range(attempts):
        try:
            elements = driver.find_elements(By.TAG_NAME, 'a')
            for element in elements:
                href = element.get_attribute('href')
                if href:
                    # Skip mailto links
                    if href.startswith('mailto:'):
                        logging.info(f"Skipping mailto link: {href}")
                        continue
                    # Skip links containing 'poczta'
                    if 'poczta' in href.lower():
                        logging.info(f"Skipping link (contains 'poczta'): {href}")
                        continue
                    # Skip image files
                    if href.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        logging.info(f"Skipping link (image file): {href}")
                        continue
                    # Skip javascript links
                    if href.startswith('javascript:'):
                        logging.info(f"Skipping javascript link: {href}")
                        continue
                    
                    # If base_url is provided, filter for links from the same domain
                    if base_url:
                        parsed_href = urlparse(href)
                        if parsed_href.netloc == '' or parsed_href.netloc == urlparse(base_url).netloc:
                            links.append(href)
                        else:
                            logging.info(f"Skipping link (external domain): {href}")
                    else:
                        links.append(href)
            break
        except Exception as e:
            logging.error(f"Error retrieving links: {e}")
            time.sleep(1)
    return list(set(links))  # Remove duplicates


def kill_screenshot_process():
    """Kill Chrome processes used for screenshots."""
    for proc in psutil.process_iter(['pid', 'name']):
        if 'chrome' in proc.info['name'].lower():
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                pass


def visit_links_and_take_screenshots(url, device_type, max_links=40):
    """Takes screenshots of a website and its links in specified device type view."""
    url = is_valid_url(url)
    domain_name = urlparse(url).netloc.replace('www.', '').replace(':', '_')
    mobile_folder, desktop_folder = create_directory_for_domain(domain_name)

    setup_logging(domain_name, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))

    options = chrome_options_desktop if device_type == 'desktop' else chrome_options_mobile
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(5)  # Wait for page to fully render

        if device_type == 'desktop':
            driver.set_window_size(1920, 1080)
        
        # Take screenshot of the main page
        main_screenshot_path = os.path.join(
            desktop_folder if device_type == 'desktop' else mobile_folder,
            f"main_page_{device_type}.png"
        )
        take_full_page_screenshot(driver, main_screenshot_path, is_mobile=(device_type == 'mobile'))

        # Get all links from the page
        links = get_all_links(driver, url)
        logging.info(f"Found {len(links)} links on page {url}")

        processed_links = set()
        link_count = 0
        
        # Process each link
        for i, link in enumerate(links):
            if link_count >= max_links:
                break
                
            if link in processed_links:
                continue
                
            processed_links.add(link)
            
            try:
                driver.get(link)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                time.sleep(5)

                if device_type == 'desktop':
                    driver.set_window_size(1920, 1080)
                    
                screenshot_path = os.path.join(
                    desktop_folder if device_type == 'desktop' else mobile_folder,
                    f"screen_{i + 1}_{device_type}.png"
                )
                
                take_full_page_screenshot(driver, screenshot_path, is_mobile=(device_type == 'mobile'))
                link_count += 1
                
            except Exception as e:
                logging.error(f"Error capturing screenshot for {link}: {str(e)}")

    except Exception as e:
        logging.error(f"Error processing {url}: {str(e)}")
        
    finally:
        driver.quit()
