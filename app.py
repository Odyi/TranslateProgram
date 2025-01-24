from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz
import os

app = Flask(__name__)
app.secret_key = 'din_hemmelige_nøkkel'

# Sett tidssonen til Europa/Oslo
os.environ['TZ'] = 'Europe/Oslo'

# Initialiser databasen
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('DROP TABLE IF EXISTS users')
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                is_admin BOOLEAN NOT NULL DEFAULT 0
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

# Opprett admin-bruker
def create_admin_user():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''
            INSERT INTO users (full_name, email, password, is_admin)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@odyeradmin.com', generate_password_hash('admin123'), 1))

# Konverter UTC-tid til norsk tid
def convert_utc_to_local(utc_time):
    utc_zone = pytz.utc
    local_zone = pytz.timezone('Europe/Oslo')
    local_time = utc_time.replace(tzinfo=utc_zone).astimezone(local_zone)
    return local_time

# Hjemmeside
@app.route('/')
def index():
    return render_template('index.html')

# Registrering
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        try:
            with sqlite3.connect('database.db') as conn:
                conn.execute('INSERT INTO users (full_name, email, password) VALUES (?, ?, ?)', 
                             (full_name, email, password))
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "E-postadressen er allerede i bruk."

    return render_template('register.html')

# Innlogging
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        with sqlite3.connect('database.db') as conn:
            conn.row_factory = sqlite3.Row
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['is_admin'] = user['is_admin']

            if user['is_admin']:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            return "Feil e-post eller passord."

    return render_template('login.html')

# Dashboard for innloggede brukere
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', full_name=session['full_name'])

# Bestillingsside
@app.route('/order', methods=['POST'])
def order():
    if 'user_id' not in session:
        return jsonify({'message': 'Ikke logget inn'}), 401

    data = request.get_json()
    description = data['description']
    user_id = session['user_id']

    with sqlite3.connect('database.db') as conn:
        conn.execute('INSERT INTO jobs (user_id, description) VALUES (?, ?)', 
                     (user_id, description))

    return jsonify({'message': 'Bestilling mottatt!'})

# Takkeside
@app.route('/thank_you')
def thank_you():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        # Hent kun bestillinger for den innloggede brukeren
        jobs = conn.execute('SELECT * FROM jobs WHERE user_id = ?', (session['user_id'],)).fetchall()

    # Konverter sqlite3.Row-objekter til dictionaries
    jobs = [dict(job) for job in jobs]

    # Konverter tidspunkter til norsk tid
    for job in jobs:
        job['timestamp'] = convert_utc_to_local(datetime.fromisoformat(job['timestamp']))

    return render_template('thank_you.html', jobs=jobs)

# Admin-grensesnitt
@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))

    with sqlite3.connect('database.db') as conn:
        conn.row_factory = sqlite3.Row
        users = conn.execute('SELECT * FROM users').fetchall()
        jobs = conn.execute('SELECT * FROM jobs').fetchall()

    # Konverter sqlite3.Row-objekter til dictionaries
    jobs = [dict(job) for job in jobs]

    # Konverter tidspunkter til norsk tid
    for job in jobs:
        job['timestamp'] = convert_utc_to_local(datetime.fromisoformat(job['timestamp']))

    return render_template('admin.html', users=users, jobs=jobs)

# Logg ut
@app.route('/logout')
def logout():
    session.clear()
    return render_template('logout.html')

if __name__ == '__main__':
    init_db()
    create_admin_user()
    app.run(debug=True)