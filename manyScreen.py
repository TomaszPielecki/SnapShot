import os
from urllib.parse import urlparse, urljoin

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def is_valid_url(url):
    """
    Validates the URL to ensure it includes the protocol and is properly formatted.
    Adds 'http://' if the protocol is missing.
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme in ['http', 'https']:
        return url
    elif not parsed_url.scheme:
        url = 'http://' + url
        parsed_url = urlparse(url)
        if all([parsed_url.scheme, parsed_url.netloc]):
            return url
    raise ValueError(f"Invalid URL: {url}")


def take_screenshots(url, save_dir='static/screenshots'):
    """
    Takes screenshots of the given URL and its internal links, saving them to the specified directory.
    """
    url = is_valid_url(url)
    domain = urlparse(url).netloc.replace('www.', '')
    domain_dir = os.path.join(save_dir, domain)

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    screenshots_dict = {}  # Initialize a dictionary to hold directories and their screenshots

    try:
        driver.get(url)

        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Create domain directory if it doesn't exist
        if not os.path.exists(domain_dir):
            os.makedirs(domain_dir)

        # Take screenshot of the main page
        main_screenshot_path = os.path.join(domain_dir, f"{domain}.png")
        driver.save_screenshot(main_screenshot_path)

        # Add the main page screenshot to the dictionary
        screenshots_dict[os.path.basename(main_screenshot_path)] = [os.path.basename(main_screenshot_path)]

        # Find all internal links (anchors) on the page
        links = driver.find_elements(By.TAG_NAME, "a")
        subpages = set()  # To avoid duplicate URLs

        for link in links:
            href = link.get_attribute("href")
            if href:
                full_url = urljoin(url, href)
                if is_valid_url(full_url) and urlparse(full_url).netloc == urlparse(url).netloc:
                    subpages.add(full_url)

        # Take screenshots of subpages and update the dictionary
        for subpage_url in subpages:
            try:
                driver.get(subpage_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

                subpage_screenshot_name = f"{subpage_url.replace('http://', '').replace('https://', '').replace('/', '_')}.png"
                subpage_screenshot_path = os.path.join(domain_dir, subpage_screenshot_name)
                driver.save_screenshot(subpage_screenshot_path)

                # Add subpage screenshot to the dictionary
                if subpage_screenshot_name not in screenshots_dict:
                    screenshots_dict[subpage_screenshot_name] = []
                screenshots_dict[subpage_screenshot_name].append(subpage_screenshot_name)

            except Exception as e:
                print(f"An error occurred while taking a screenshot of {subpage_url}: {e}")

    except Exception as e:
        print(f"An error occurred while taking a screenshot of {url}: {e}")
    finally:
        driver.quit()

    return screenshots_dict  # Return the dictionary of screenshots