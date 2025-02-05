from datetime import datetime
from pathlib import Path
from typing import List, Dict


def find_screenshots_by_date(screenshots_dir: str, date: datetime, domain: str = None, device_type: str = None) -> List[
    str]:
    """
    Finds screenshots in the given directory and its subdirectories whose modification date
    matches the given date, and optionally filters by domain and device type.

    :param screenshots_dir: Path to the directory containing screenshots.
    :param date: Date for which to find screenshots.
    :param domain: Optional domain to filter screenshots.
    :param device_type: Optional device type to filter screenshots (e.g., 'desktop' or 'mobile').
    :return: List of relative paths to the found screenshots.
    """
    screenshots = []
    screenshots_dir = Path(screenshots_dir)

    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        raise FileNotFoundError(f"Directory '{screenshots_dir}' does not exist or is not a directory.")

    for file_path in screenshots_dir.rglob('*'):  # Recursively search the directory
        if file_path.is_file():
            try:
                file_date = datetime.fromtimestamp(file_path.stat().st_mtime).date()
                if file_date == date.date():
                    if domain and domain not in str(file_path):
                        continue
                    if device_type and device_type not in str(file_path):
                        continue
                    screenshots.append(str(file_path.relative_to(screenshots_dir)))
            except OSError as e:
                print(f"Cannot read file '{file_path}'. Error: {e}")
    return screenshots


def get_screenshots(screenshot_dir: str) -> Dict[str, List[str]]:
    """
    Pobiera strukturę katalogów i plików z katalogu z zrzutami ekranu.

    :param screenshot_dir: Ścieżka do katalogu głównego z zrzutami ekranu.
    :return: Słownik, gdzie kluczami są nazwy podkatalogów, a wartościami listy plików.
    """
    screenshots = {}
    screenshot_dir = Path(screenshot_dir)

    if not screenshot_dir.exists() or not screenshot_dir.is_dir():
        raise FileNotFoundError(f"Katalog '{screenshot_dir}' nie istnieje lub nie jest katalogiem.")

    for subdir in screenshot_dir.iterdir():
        if subdir.is_dir():
            try:
                screenshots[subdir.name] = [
                    file.name for file in subdir.iterdir() if file.is_file()
                ]
            except OSError as e:
                print(f"Nie można odczytać katalogu '{subdir}'. Błąd: {e}")
    return screenshots
