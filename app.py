from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DATABASE = 'loghub.db'
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# -------------------- Database Connection --------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# -------------------- Home Route --------------------

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('upload'))
    return redirect(url_for('login'))

# -------------------- Signup --------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing:
            return 'Username already exists'
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        db.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

# -------------------- Login --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('upload'))
        return 'Invalid credentials'
    return render_template('login.html')

# -------------------- Logout --------------------

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# -------------------- Upload Logs --------------------

def parse_log(file_path):
    log_entries = []
    pattern = r'^(.*?) - (\w+) - (.*)$'

    with open(file_path, 'r') as f:
        for line in f:
            match = re.match(pattern, line.strip())
            if match:
                timestamp_str, level, message = match.groups()
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    continue
                log_entries.append((timestamp, level, message))
    return log_entries

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['logfile']
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            logs = parse_log(file_path)
            db = get_db()
            for log in logs:
                db.execute(
                    'INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)',
                    (log[0], log[1], log[2])
                )
            db.commit()
            return redirect(url_for('dashboard'))

    return render_template('upload.html')

# -------------------- Dashboard --------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()

    # Get filters from request
    keyword = request.args.get('keyword', '')
    level = request.args.get('level', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    # Base query
    query = 'SELECT timestamp, level, message FROM logs WHERE 1=1'
    params = []

    if keyword:
        query += ' AND message LIKE ?'
        params.append(f'%{keyword}%')

    if level:
        query += ' AND level = ?'
        params.append(level)

    if start_date:
        query += ' AND DATE(timestamp) >= ?'
        params.append(start_date)

    if end_date:
        query += ' AND DATE(timestamp) <= ?'
        params.append(end_date)

    query += ' ORDER BY timestamp DESC'
    cursor = db.execute(query, params)
    logs = cursor.fetchall()

    # Count log levels
    level_counts = {'INFO': 0, 'WARNING': 0, 'ERROR': 0}
    for log in logs:
        if log['level'] in level_counts:
            level_counts[log['level']] += 1

    return render_template('dashboard.html', logs=logs, level_counts=level_counts)

# -------------------- Main --------------------

if __name__ == '__main__':
    app.run(debug=True)
	