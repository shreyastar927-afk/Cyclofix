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
    from collections import Counter

    # Get the most recent log
    latest_log = CycleLog.query.filter_by(
        user_id=current_user.id
    ).order_by(CycleLog.created_at.desc()).first()

    # All possible suggestions
    all_suggestions = {
        'cramp': ['heat', 'breathing', 'rest', 'movement'],
        'ache': ['rest', 'heat', 'movement', 'breathing'],
        'sharp': ['rest', 'breathing', 'heat', 'movement'],
        'back': ['heat', 'movement', 'rest', 'breathing']
    }

    # Get suggestions for this pain type
    pain_type = latest_log.pain_type if latest_log else 'cramp'
    suggestions_list = all_suggestions.get(pain_type, all_suggestions['cramp'])

    # Check feedback history
    past_feedback = CycleLog.query.filter_by(
        user_id=current_user.id,
        pain_type=pain_type
    ).filter(CycleLog.relief_helped == 'yes').all()

    # Count how many times each suggestion helped
    all_helpful = [log.relief_suggestion for log in past_feedback]
    help_counts = Counter(all_helpful)

    # Only count as helpful if it helped at least 2 times
    helpful = [s for s, count in help_counts.items() if count >= 2]

    # Sort — put previously helpful suggestions first
    suggestions_list = sorted(
        suggestions_list,
        key=lambda x: help_counts.get(x, 0),
        reverse=True
    )

    suggestion_details = {
        'heat': {
            'emoji': '🔥',
            'title': 'Apply Heat',
            'desc': 'Use a hot water bottle or heating pad on your lower abdomen for 15-20 minutes.'
        },
        'breathing': {
            'emoji': '🌬️',
            'title': 'Deep Breathing',
            'desc': 'Inhale for 4 counts, hold for 4, exhale for 6. Repeat 5 times to reduce tension.'
        },
        'rest': {
            'emoji': '🛏️',
            'title': 'Rest',
            'desc': 'Lie down in a comfortable position. Try lying on your side with knees pulled up.'
        },
        'movement': {
            'emoji': '🚶',
            'title': 'Gentle Movement',
            'desc': 'A short slow walk or gentle stretching can help reduce cramping.'
        }
    }

    return render_template('suggestions.html',
        user=current_user,
        suggestions=suggestions_list,
        details=suggestion_details,
        log=latest_log,
        helpful=helpful
    )
@app.route('/feedback', methods=['POST'])
@login_required
def feedback():
    suggestion = request.form.get('suggestion')
    response = request.form.get('response')

    # Get the most recent log for reference
    latest_log = CycleLog.query.filter_by(
        user_id=current_user.id
    ).order_by(CycleLog.created_at.desc()).first()

    if latest_log:
        # Create a new log entry for each feedback
        feedback_log = CycleLog(
            user_id=current_user.id,
            date=latest_log.date,
            cycle_day=latest_log.cycle_day,
            pain_intensity=latest_log.pain_intensity,
            pain_type=latest_log.pain_type,
            relief_suggestion=suggestion,
            relief_helped=response
        )
        db.session.add(feedback_log)
        db.session.commit()

    return '', 200
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)