import sqlite3

conn = sqlite3.connect('loghub.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    level TEXT,
    message TEXT
)
''')

conn.commit()
conn.close()
print("Database created successfully!")
