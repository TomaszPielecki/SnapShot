import json
import logging
import os

from flask import Flask, render_template, redirect, url_for, flash, request
from flask import send_file

from forms import AddDomainForm
from manyScreen import take_screenshots as take_many_screenshots
from screenshots import get_screenshots, take_screenshots

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Paths to files
LOG_FILE = 'logs/app.log'
DOMAINS_FILE = 'data.json'
GALLERY_DIR = 'static/gallery'
SCREENSHOT_DIR = 'static/screenshots'

# Configure logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
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


def take_screenshot(url, SCREENSHOT_DIR):
    pass


@app.route('/screenshots', methods=['GET', 'POST'])
def screenshots():
    domains = load_domains()
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            take_screenshots(url, SCREENSHOT_DIR)
            flash('Screenshot taken successfully!', 'success')
        else:
            flash('Please provide a valid URL.', 'danger')
        return redirect(url_for('screenshots'))

    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    images = [f for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f))]
    return render_template('screenshots.html', screenshots=images, domains=domains)


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


@app.route('/logs')
def view_logs():
    if not os.path.exists(LOG_FILE):
        flash('Log file does not exist.', 'danger')
        return redirect(url_for('dashboard'))
    return send_file(LOG_FILE, as_attachment=True)


@app.route('/logs/delete', methods=['POST'])
def delete_logs():
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        flash('Log file deleted successfully!', 'success')
    else:
        flash('Log file does not exist.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/take_screenshots', methods=['POST'])
def trigger_screenshots():
    url = request.form.get('url')
    if url:
        save_dir = take_screenshots(url)
        flash(f'Screenshots saved in {save_dir}', 'success')
    else:
        flash('Please provide a valid URL.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/take_many_screenshots', methods=['POST'])  # Zmieniony routing
def trigger_many_screenshots():
    domains = load_domains()
    if domains:
        save_dir = take_many_screenshots(domains)  # Wywołanie funkcji `take_many_screenshots`
        flash(f'Many screenshots saved in {save_dir}', 'success')
    else:
        flash('No domains available to take screenshots.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/manyScreen')
@app.route('/manyScreen/<folder>')
def many_screen(folder=None):
    if folder:
        folder_path = os.path.join(SCREENSHOT_DIR, folder)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            screenshots = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        else:
            screenshots = []
        return render_template('manyScreen.html', folder=folder, screenshots=screenshots)
    else:
        screenshot_dirs = [d for d in os.listdir(SCREENSHOT_DIR) if os.path.isdir(os.path.join(SCREENSHOT_DIR, d))]
        domains = load_domains()
        screenshots = get_screenshots(SCREENSHOT_DIR)
        return render_template('manyScreen.html', screenshot_dirs=screenshot_dirs, domains=domains,
                               screenshots=screenshots)


if __name__ == '__main__':
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(GALLERY_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if not os.path.exists(DOMAINS_FILE):
        with open(DOMAINS_FILE, 'w') as f:
            json.dump({'domains': []}, f)

    app.run(debug=True)
