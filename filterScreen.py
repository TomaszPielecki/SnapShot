from datetime import datetime
from pathlib import Path
from typing import List


def find_screenshots_by_date(screenshots_dir: str, start_date: datetime, end_date: datetime, domain: str = None,
                             device_type: str = None) -> List[str]:
    """
    Finds screenshots in the given directory and its subdirectories whose modification date
    falls within the given date range, and optionally filters by domain and device type.

    :param screenshots_dir: Path to the directory containing screenshots.
    :param start_date: Start date of the range for which to find screenshots.
    :param end_date: End date of the range for which to find screenshots.
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
                if start_date.date() <= file_date <= end_date.date():
                    if domain and domain not in str(file_path):
                        continue
                    if device_type and device_type not in str(file_path):
                        continue
                    screenshots.append(str(file_path.relative_to(screenshots_dir)))
            except OSError as e:
                print(f"Cannot read file '{file_path}'. Error: {e}")
    return screenshots
