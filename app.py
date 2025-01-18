import json
import logging
import os

from flask import Flask, render_template, redirect, url_for, flash, request

from forms import AddDomainForm
from screenshots import get_screenshots, take_screenshot

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Paths to files
LOG_FILE = 'logs/app.log'
DOMAINS_FILE = 'data.json'
GALLERY_DIR = 'static/gallery'
SCREENSHOT_DIR = 'static/screenshots'

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Example log message
logging.info('Application started')


def get_logs():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        return f.readlines()


def load_domains():
    if not os.path.exists(DOMAINS_FILE):
        return []
    with open(DOMAINS_FILE, 'r') as f:
        data = json.load(f)
        return data.get('domains', [])


def save_domains(domains):
    # Remove duplicates by converting the list to a set and back to a list
    unique_domains = list(set(domains))
    with open(DOMAINS_FILE, 'w') as f:
        json.dump({'domains': unique_domains}, f, indent=4)


@app.route('/')
def dashboard():
    logs = get_logs()
    domains = load_domains()
    screenshots = get_screenshots(SCREENSHOT_DIR)
    screenshot_files = [f for f in os.listdir(SCREENSHOT_DIR) if os.path.isfile(os.path.join(SCREENSHOT_DIR, f))]
    screenshot_count = len(screenshot_files)
    log_count = len(logs)
    domain_count = len(domains)

    return render_template(
        'dashboard.html',
        log_count=log_count,
        domain_count=domain_count,
        screenshot_count=screenshot_count,
        logs=logs,
        screenshots=screenshots
    )


@app.route('/manage_pages', methods=['GET', 'POST'])
def manage_domains():
    form = AddDomainForm()
    domains = load_domains()

    if form.validate_on_submit():
        domain = form.new_domain.data
        if domain:
            domains.append(domain)
            save_domains(domains)
            flash('Domain added successfully!', 'success')
        else:
            flash('Please provide all required information.', 'danger')

    return render_template('manage_pages.html', domains=domains, add_domain_form=form)


@app.route('/domains/delete/<domain>', methods=['POST'])
def delete_domain(domain):
    domains = load_domains()
    if domain in domains:
        domains.remove(domain)
        save_domains(domains)
        flash('Domain deleted successfully!', 'success')
    else:
        flash('Domain does not exist.', 'danger')

    return redirect(url_for('manage_domains'))


@app.route('/domains/edit/<old_domain>', methods=['GET', 'POST'])
def edit_domain(old_domain):
    form = AddDomainForm()
    domains = load_domains()

    if request.method == 'POST' and form.validate_on_submit():
        new_domain = form.new_domain.data
        if old_domain in domains:
            domains[domains.index(old_domain)] = new_domain
            save_domains(domains)
            flash('Domain updated successfully!', 'success')
        else:
            flash('Domain does not exist.', 'danger')
        return redirect(url_for('manage_domains'))

    form.new_domain.data = old_domain
    return render_template('edit_domain.html', form=form, old_domain=old_domain)


@app.route('/gallery')
def gallery():
    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    images = [f for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f))]
    return render_template('gallery.html', images=images)


@app.route('/screenshots', methods=['GET', 'POST'])
def screenshots():
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            take_screenshot(url, SCREENSHOT_DIR)
            flash('Screenshot taken successfully!', 'success')
        else:
            flash('Please provide a valid URL.', 'danger')
        return redirect(url_for('screenshots'))

    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    images = [f for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f))]
    return render_template('screenshots.html', screenshots=images)


@app.route('/screenshots/delete/<int:screenshot_id>', methods=['POST'])
def delete_screenshot(screenshot_id):
    screenshot_files = [f for f in os.listdir(SCREENSHOT_DIR) if os.path.isfile(os.path.join(SCREENSHOT_DIR, f))]
    if 0 <= screenshot_id < len(screenshot_files):
        screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot_files[screenshot_id])
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            flash('Screenshot deleted successfully!', 'success')
        else:
            flash('Screenshot does not exist.', 'danger')
    else:
        flash('Invalid screenshot ID.', 'danger')
    return redirect(url_for('screenshots'))


if __name__ == '__main__':
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(GALLERY_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if not os.path.exists(DOMAINS_FILE):
        with open(DOMAINS_FILE, 'w') as f:
            json.dump({'domains': []}, f)

    app.run(debug=True)
