import os
import pytest

from SnapShot.app import BASE_SCREENSHOT_FOLDER, DOMAINS_FILE, LOG_FILE


# Fixture client for Flask app testing
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Test: Delete screenshot functionality
def test_delete_screenshot(client):
    folder = 'katarzynakobiela.pl'
    screenshot = 'main_page_desktop.png'
    screenshot_path = os.path.join(BASE_SCREENSHOT_FOLDER, folder, screenshot)

    # Setup: Create the test file
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
    with open(screenshot_path, 'w') as f:
        f.write("test content")

    # Ensure the file was created
    assert os.path.exists(screenshot_path) is True

    # Simulate deleting the file via the Flask endpoint
    response = client.post(f'/delete_screenshot/{folder}/{screenshot}')
    assert response.status_code == 302  # Check for redirect

    # Ensure the file was deleted
    assert os.path.exists(screenshot_path) is False


# Fixture for setup and teardown of test files and directories
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Setup: Create necessary directories and files
    os.makedirs(BASE_SCREENSHOT_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(DOMAINS_FILE, 'w') as f:
        f.write('{"domains": []}')
    yield
    # Teardown: Clean up created files and directories after test
    if os.path.exists(BASE_SCREENSHOT_FOLDER):
        for root, dirs, files in os.walk(BASE_SCREENSHOT_FOLDER, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    if os.path.exists(DOMAINS_FILE):
        os.remove(DOMAINS_FILE)
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
