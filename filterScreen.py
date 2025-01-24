import os
from datetime import datetime


def find_screenshots_by_date(screenshots_dir, date):
    screenshots = []
    for root, dirs, files in os.walk(screenshots_dir):
        for file in files:
            # Sprawdzamy datę modyfikacji pliku
            file_path = os.path.join(root, file)
            file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()
            if file_date == date.date():
                screenshots.append(file_path.replace(screenshots_dir + '/', ''))  # Zwracamy ścieżkę względną
    return screenshots


def get_screenshots(screenshot_dir):
    screenshots = {}
    for dirpath, dirnames, filenames in os.walk(screenshot_dir):
        for dirname in dirnames:
            dir_full_path = os.path.join(dirpath, dirname)
            screenshots[dirname] = [f for f in os.listdir(dir_full_path) if
                                    os.path.isfile(os.path.join(dir_full_path, f))]
    return screenshots
