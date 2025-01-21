# screenshots.py
import os


def get_screenshots(screenshot_dir):
    screenshots = {}
    for dirpath, dirnames, filenames in os.walk(screenshot_dir):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            screenshots[dirname] = [f for f in os.listdir(dir_full_path) if
                                    os.path.isfile(os.path.join(dir_full_path, f))]
    return screenshots


def take_screenshots(url, save_dir='static/screenshots'):
    from urllib.parse import urlparse, urljoin
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from seleniumwire import webdriver
    from webdriver_manager.chrome import ChromeDriverManager

    def is_valid_url(url):
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = 'http://' + url
            parsed_url = urlparse(url)
        if all([parsed_url.scheme, parsed_url.netloc]):
            return url
        else:
            raise ValueError(f"Invalid URL: {url}")

    url = is_valid_url(url)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        main_screenshot_path = os.path.join(save_dir,
                                            f"{url.replace('http://', '').replace('https://', '').replace('/', '_')}.png")
        driver.save_screenshot(main_screenshot_path)

        links = driver.find_elements(By.TAG_NAME, "a")
        subpages = set()

        for link in links:
            href = link.get_attribute("href")
            if href:
                full_url = urljoin(url, href)
                if is_valid_url(full_url) and urlparse(full_url).netloc == urlparse(url).netloc:
                    subpages.add(full_url)

        for subpage_url in subpages:
            try:
                driver.get(subpage_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                subpage_screenshot_path = os.path.join(save_dir,
                                                       f"{subpage_url.replace('http://', '').replace('https://', '').replace('/', '_')}.png")
                driver.save_screenshot(subpage_screenshot_path)
            except Exception as e:
                print(f"An error occurred while taking a screenshot of {subpage_url}: {e}")

    except Exception as e:
        print(f"An error occurred while taking a screenshot of {url}: {e}")
    finally:
        driver.quit()
