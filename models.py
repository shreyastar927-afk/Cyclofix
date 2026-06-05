from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    last_period_start = db.Column(db.Date, nullable=True)
    cycle_length = db.Column(db.Integer, default=28)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    logs = db.relationship('CycleLog', backref='user', lazy=True)

class CycleLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    cycle_day = db.Column(db.Integer, nullable=True)
    pain_intensity = db.Column(db.Integer, nullable=True)
    pain_type = db.Column(db.String(50), nullable=True)
    relief_suggestion = db.Column(db.String(100), nullable=True)
    relief_helped = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)