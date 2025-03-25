import json
import logging
import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask import send_file
from flask import send_from_directory
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from filterScreen import find_screenshots_by_date
from forms import AddDomainForm, LoginForm, RegisterForm
from screenshot_utils import is_valid_url, visit_links_and_take_screenshots, create_directory_for_domain, get_screenshots

# Załadowanie zmiennych środowiskowych
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_only_for_development')
socketio = SocketIO(app)

# Paths to files
LOG_FILE = 'logs/logfile.log'
MAX_LOG_LINES = 1000
DOMAINS_FILE = 'data.json'
USERS_FILE = 'users.json'
SCREENSHOT_DIR = 'static/screenshots'
BASE_SCREENSHOT_FOLDER = 'static/screenshots'

# Configure logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Funkcje pomocnicze
def get_logs():
    ensure_log_directory()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            logs = file.readlines()
        logs.reverse()
    else:
        logs = []
    return logs


def load_domains():
    if not os.path.exists(DOMAINS_FILE):
        return []
    with open(DOMAINS_FILE, 'r') as f:
        data = json.load(f)
        return data.get('domains', [])


def save_domains(domains):
    unique_domains = list(set(domains))
    with open(DOMAINS_FILE, 'w') as f:
        json.dump({'domains': unique_domains}, f, indent=4)


# Funkcje związane z użytkownikami i autoryzacją
def load_users():
    if not os.path.exists(USERS_FILE):
        # Utwórz domyślnego admina podczas pierwszego uruchomienia
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'SnapShot2024!')
        save_users({admin_username: {'password': generate_password_hash(admin_password), 'role': 'admin'}})
    
    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Zaloguj się, aby uzyskać dostęp do tej strony.', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Zaloguj się, aby uzyskać dostęp do tej strony.', 'danger')
            return redirect(url_for('login', next=request.url))
        
        users = load_users()
        if session['user'] not in users or users[session['user']].get('role') != 'admin':
            flash('Nie masz uprawnień do tej strony.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


# Trasy związane z autoryzacją
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        users = load_users()
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['user'] = username
            session['role'] = users[username].get('role', 'user')
            flash(f'Witaj, {username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
@admin_required
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data
        
        users = load_users()
        
        if username in users:
            flash(f'Użytkownik {username} już istnieje.', 'danger')
        else:
            users[username] = {
                'password': generate_password_hash(password),
                'role': role
            }
            save_users(users)
            flash(f'Użytkownik {username} został zarejestrowany.', 'success')
            return redirect(url_for('dashboard'))
    
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    if 'user' in session:
        flash(f'Wylogowano użytkownika {session["user"]}.', 'success')
        session.pop('user', None)
        session.pop('role', None)
    return redirect(url_for('login'))


# Zabezpieczone trasy aplikacji
@app.route('/')
@login_required
def dashboard():
    write_log("Accessed dashboard")
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
        screenshots=screenshots,
        user=session.get('user'),
        role=session.get('role')
    )


@app.route('/manage_pages', methods=['GET', 'POST'])
@login_required
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
@admin_required
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


@app.route('/copy_domain/<domain>', methods=['POST'])
def copy_domain(domain):
    try:
        domains = load_domains()
        if domain not in domains:
            flash("Domain not found!", 'danger')
            return redirect(url_for('manage_domains'))

        new_domain = f"{domain}_copy"
        if new_domain in domains:
            flash(f"Domain '{new_domain}' already exists!", 'danger')
            return redirect(url_for('manage_domains'))

        domains.append(new_domain)
        save_domains(domains)
        flash(f"Domain '{domain}' copied as '{new_domain}'.", 'success')
    except Exception as e:
        flash(f"Error copying domain: {str(e)}", 'danger')

    return redirect(url_for('manage_domains'))


@app.route('/filtrScreen')
def gallery():
    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    images = [f for f in os.listdir(screenshots_dir) if os.path.isfile(os.path.join(screenshots_dir, f))]
    return render_template('FiltrScreen.html', images=images)


@app.route('/screenshots/delete/<folder>/<screenshot>', methods=['POST'])
def delete_screenshot_from_folder(folder, screenshot):
    screenshot_path = os.path.join(SCREENSHOT_DIR, folder, screenshot)
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        flash('Screenshot deleted successfully!', 'success')
    else:
        flash('Screenshot does not exist.', 'danger')
    return redirect(url_for('many_screen', folder=folder))


@app.route('/logs/delete', methods=['POST'])
def delete_logs_route():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            lines = file.readlines()
        if len(lines) >= 500:
            lines = lines[500:]
            with open(LOG_FILE, 'w') as file:
                file.writelines(lines)
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Log count is less than 500."}), 400
    else:
        return jsonify({"success": False, "error": "Log file does not exist."}), 404


def setup_logging():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def write_log(message, level=logging.INFO):
    ensure_log_directory()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r') as file:
            lines = file.readlines()
        lines.reverse()
        if len(lines) >= MAX_LOG_LINES:
            lines = lines[:MAX_LOG_LINES - 1]
    else:
        lines = []

    lines.insert(0, f"{logging.getLevelName(level)} - {message}\n")

    with open(LOG_FILE, 'w') as file:
        file.writelines(lines)


def ensure_log_directory():
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


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


@app.route('/screenshots/delete/<screenshot>', methods=['POST'])
def delete_screenshots(screenshot):
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot)
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        flash('Screenshot deleted successfully!', 'success')
    else:
        flash('Screenshot does not exist.', 'danger')
    return redirect(url_for('screenshots_route'))


@app.route('/create_domain_folder', methods=['POST'])
def create_domain_folder():
    url = request.form.get('url')
    if url:
        domain_name = urlparse(url).netloc.replace('www.', '').replace(':', '_')
        create_directory_for_domain(domain_name)
        flash('Folder created successfully!', 'success')
    else:
        flash('Please provide a valid URL.', 'danger')
    return redirect(url_for('dashboard'))


@app.route('/search_screenshots', methods=['GET', 'POST'])
def search_screenshots():
    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        domain = request.form.get('domain')
        device_type = request.form.get('device_type')

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('search_screenshots'))

        screenshots_dir = os.path.join(app.static_folder, 'screenshots')
        filtered_screenshots = []

        for folder in os.listdir(screenshots_dir):
            folder_path = os.path.join(screenshots_dir, folder)
            if os.path.isdir(folder_path):
                subfolders = ['desktop', 'mobile'] if not device_type else [device_type]
                for subfolder in subfolders:
                    subfolder_path = os.path.join(folder_path, subfolder)
                    if os.path.exists(subfolder_path) and os.path.isdir(subfolder_path):
                        screenshots = find_screenshots_by_date(subfolder_path, start_date, end_date, domain,
                                                               device_type)
                        filtered_screenshots.extend(screenshots)

        return render_template('filtrScreen.html', screenshots=filtered_screenshots,
                               start_date=start_date_str, end_date=end_date_str, domain=domain, device_type=device_type)

    domains = load_domains()
    return render_template('filtrScreen.html', domains=domains)


@app.route('/get_screenshots', methods=['GET'])
def get_screenshots_route():
    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    screenshots = get_screenshots(screenshots_dir)
    return jsonify(screenshots)


@app.route('/download/<path:filename>')
def download_file(filename):
    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    return send_from_directory(screenshots_dir, filename, as_attachment=True)


@app.route('/api/search_screenshots', methods=['POST'])
def api_search_screenshots():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    domain = request.form.get('domain')
    device_type = request.form.get('device_type')

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid date format. Please use YYYY-MM-DD."}), 400

    screenshots_dir = os.path.join(app.static_folder, 'screenshots')
    filtered_screenshots = []

    for folder in os.listdir(screenshots_dir):
        folder_path = os.path.join(screenshots_dir, folder)
        if os.path.isdir(folder_path):
            subfolders = ['desktop', 'mobile'] if not device_type else [device_type.lower()]
            for subfolder in subfolders:
                subfolder_path = os.path.join(folder_path, subfolder)
                if os.path.exists(subfolder_path) and os.path.isdir(subfolder_path):
                    screenshots = [f for f in os.listdir(subfolder_path) if
                                   os.path.isfile(os.path.join(subfolder_path, f))]
                    for screenshot in screenshots:
                        file_path = os.path.join(subfolder_path, screenshot)
                        file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).date()

                        if (start_date.date() <= file_date <= end_date.date()) and (
                                not domain or domain.lower() in folder.lower()):
                            filtered_screenshots.append(os.path.join(folder, subfolder, screenshot))

    return jsonify({"screenshots": filtered_screenshots})


@app.route('/screenshots/delete', methods=['POST'])
def delete_screenshot():
    screenshot = request.args.get('screenshot')
    screenshot_path = os.path.join(SCREENSHOT_DIR, screenshot)
    if os.path.exists(screenshot_path):
        os.remove(screenshot_path)
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Screenshot does not exist."}), 404


@app.route('/download_logs')
def download_logs():
    ensure_log_directory()
    if os.path.exists(LOG_FILE):
        return send_file(LOG_FILE, as_attachment=True)
    else:
        flash('Log file does not exist.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/logs', methods=['GET'])
@app.route('/logs/<domain>/<date_str>', methods=['GET'])
def fetch_logs(domain=None, date_str=None):
    if domain and date_str:
        log_folder = os.path.join(BASE_SCREENSHOT_FOLDER, domain, date_str)
        log_file = os.path.join(log_folder, 'log.txt')
        if os.path.exists(log_file):
            with open(log_file, 'r') as file:
                logs = file.readlines()
            return jsonify({"logs": logs})
        else:
            return jsonify({"error": "Log file does not exist."}), 404
    else:
        logs = get_logs()
        return jsonify({"logs": logs[-20:]})


@app.route('/zrobscreen', methods=['POST'])
@login_required
def zrobscreen():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    # Bardziej rygorystyczna walidacja
    if 'domain' not in data:
        return jsonify({"error": "Missing 'domain' field"}), 400
    if 'deviceType' not in data:
        return jsonify({"error": "Missing 'deviceType' field"}), 400
    if data['deviceType'] not in ['mobile', 'desktop']:
        return jsonify({"error": "Invalid device type. Must be 'mobile' or 'desktop'"}), 400

    domain = data['domain']
    device_type = data['deviceType']
    
    try:
        visit_links_and_take_screenshots(domain, device_type, max_links=50)
        write_log(f"User {session.get('user')} took screenshots for {domain} on {device_type}")
        return jsonify({"success": True}), 200
    except Exception as e:
        write_log(f"Error taking screenshots: {str(e)}", level=logging.ERROR)
        return jsonify({"error": str(e)}), 500


@app.route('/screenshot', methods=['POST'])
@login_required
def screenshot():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400
        
    # Bardziej rygorystyczna walidacja
    if 'urls' not in data:
        return jsonify({"error": "Missing 'urls' field"}), 400
    if not isinstance(data['urls'], list):
        return jsonify({"error": "'urls' must be an array"}), 400
    if not data['urls']:
        return jsonify({"error": "'urls' cannot be empty"}), 400
    if 'deviceType' not in data:
        return jsonify({"error": "Missing 'deviceType' field"}), 400
    if data['deviceType'] not in ['mobile', 'desktop']:
        return jsonify({"error": "Invalid device type. Must be 'mobile' or 'desktop'"}), 400

    urls = data['urls']
    device_type = data['deviceType']
    screenshots = []

    for url in urls:
        try:
            # Walidacja URL
            if not isinstance(url, str):
                continue
                
            url = is_valid_url(url)
            visit_links_and_take_screenshots(url, device_type)
            domain_name = url.split('/')[2].replace('www.', '').replace(':', '_')
            domain_folder = os.path.join('static', 'screenshots', domain_name, device_type)
            if os.path.exists(domain_folder):
                screenshots.extend([os.path.join(domain_folder, f) for f in os.listdir(domain_folder) if
                                   os.path.isfile(os.path.join(domain_folder, f))])
        except Exception as e:
            write_log(f"Error processing {url}: {e}", level=logging.ERROR)
            return jsonify({"error": f"Error processing {url}: {str(e)}"}), 500

    return jsonify({"screenshots": screenshots}), 200


if __name__ == '__main__':
    setup_logging()
    write_log("Application started")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    if not os.path.exists(DOMAINS_FILE):
        with open(DOMAINS_FILE, 'w') as f:
            json.dump({'domains': []}, f)
    
    # Upewnij się, że plik użytkowników istnieje
    if not os.path.exists(USERS_FILE):
        load_users()  # Ta funkcja utworzy plik z domyślnym adminem

    socketio.run(app, debug=True)
