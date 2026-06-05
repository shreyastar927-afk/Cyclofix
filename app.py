from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, CycleLog
from datetime import datetime, date

app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyclofix-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyclofix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@login_required
def home():
    return render_template('base.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        last_period = request.form.get('last_period_start')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please log in.')
            return redirect(url_for('login'))

        new_user = User(
            email=email,
            name=name,
            password=generate_password_hash(password),
            last_period_start=datetime.strptime(last_period, '%Y-%m-%d').date()
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/log', methods=['GET', 'POST'])
@login_required
def log_pain():
    if request.method == 'POST':
        pain_intensity = int(request.form.get('pain_intensity'))
        pain_type = request.form.get('pain_type')

        # Auto-calculate cycle day
        today = date.today()
        if current_user.last_period_start:
            cycle_day = (today - current_user.last_period_start).days + 1
        else:
            cycle_day = None

        new_log = CycleLog(
            user_id=current_user.id,
            date=today,
            cycle_day=cycle_day,
            pain_intensity=pain_intensity,
            pain_type=pain_type
        )
        db.session.add(new_log)
        db.session.commit()
        return redirect(url_for('suggestions'))

    return render_template('log.html')
@app.route('/suggestions')
@login_required
def suggestions():
    return render_template('base.html', user=current_user)
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)