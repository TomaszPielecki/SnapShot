import os
from urllib.parse import urlparse

from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def is_valid_url(url):
    """
    Validates the URL to ensure it includes the protocol and is properly formatted.
    Adds 'http://' if the protocol is missing.

    :param url: URL to validate
    :return: Validated URL with protocol
    """
    parsed_url = urlparse(url)
    if not parsed_url.scheme:
        url = 'http://' + url
        parsed_url = urlparse(url)
    if all([parsed_url.scheme, parsed_url.netloc]):
        return url
    else:
        raise ValueError(f"Invalid URL: {url}")

def take_screenshot(url, save_dir):
    """
    Takes a screenshot of the given URL and saves it to the specified directory.

    :param url: URL of the website to take a screenshot of
    :param save_dir: Directory to save the screenshot
    """
    url = is_valid_url(url)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        screenshot_path = os.path.join(save_dir,
                                       f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}.png")
        driver.save_screenshot(screenshot_path)
    except Exception as e:
        print(f"An error occurred while taking a screenshot of {url}: {e}")
    finally:
        driver.quit()

def get_screenshots(directory='static/screenshots'):
    """
    Pobiera zrzuty ekranu dla każdej domeny.

    :param directory: Ścieżka do katalogu zrzutów
    :return: Słownik {domena: [ścieżki_do_plików]}
    """
    screenshots = {}
    if not os.path.exists(directory):
        return screenshots

    for domain_folder in os.listdir(directory):
        domain_path = os.path.join(directory, domain_folder)
        if os.path.isdir(domain_path):
            screenshots[domain_folder] = []
            for file in os.listdir(domain_path):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    screenshots[domain_folder].append(os.path.join(domain_path, file))
    return screenshots
