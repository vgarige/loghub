from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120))
    timestamp = db.Column(db.String(120))
    level = db.Column(db.String(20))
    message = db.Column(db.Text)
