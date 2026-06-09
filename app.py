from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, CycleLog
from datetime import datetime, date, timedelta
from datetime import timedelta
def generate_weekly_insight(user_id):
    from collections import Counter
    from datetime import timedelta
    
    # Get logs from the last 4 weeks
    four_weeks_ago = date.today() - timedelta(weeks=4)
    recent_logs = CycleLog.query.filter_by(
        user_id=user_id
    ).filter(
        CycleLog.date >= four_weeks_ago,
        CycleLog.pain_intensity != None
    ).all()
    
    if not recent_logs:
        return {
            'text': "Log your pain this cycle to get your first weekly insight 🌸",
            'emoji': '📊'
        }
    
    # What helped most
    helpful_logs = [l for l in recent_logs if l.relief_helped == 'yes' and l.relief_suggestion]
    help_counts = Counter([l.relief_suggestion for l in helpful_logs])
    
    # Average pain this cycle
    avg_pain = round(sum([l.pain_intensity for l in recent_logs]) / len(recent_logs), 1)
    
    # Worst day
    worst_log = max(recent_logs, key=lambda l: l.pain_intensity)
    
    # Most common pain type
    pain_types = Counter([l.pain_type for l in recent_logs if l.pain_type])
    most_common = pain_types.most_common(1)[0][0] if pain_types else None
    
    # Generate insight based on available data
    insights = []
    
    if help_counts:
        top = help_counts.most_common(1)[0]
        insights.append({
            'text': f"{top[0].capitalize()} has helped you {top[1]} time{'s' if top[1] > 1 else ''} recently — it's your most effective relief method.",
            'emoji': '💡'
        })
    
    if worst_log:
        insights.append({
            'text': f"Your most intense pain this cycle was a {worst_log.pain_intensity}/10 on Day {worst_log.cycle_day}. Knowing your pattern helps you prepare.",
            'emoji': '📈'
        })
    
    if avg_pain:
        if avg_pain <= 4:
            insights.append({
                'text': f"Your average pain this cycle was {avg_pain}/10 — that's on the milder side. Keep logging to track changes over time.",
                'emoji': '🌸'
            })
        elif avg_pain <= 7:
            insights.append({
                'text': f"Your average pain this cycle was {avg_pain}/10 — moderate. Your relief suggestions are being personalised based on this.",
                'emoji': '📊'
            })
        else:
            insights.append({
                'text': f"Your average pain this cycle was {avg_pain}/10 — that's significant. Consider speaking to a doctor if this is consistent.",
                'emoji': '⚠️'
            })
    
    if most_common:
        insights.append({
            'text': f"{most_common.capitalize()} pain is your most common type. Your suggestions are being tailored around this.",
            'emoji': '🔍'
        })
    
    # Return a random insight from available ones
    import random
    return random.choice(insights) if insights else {
        'text': "Keep logging your pain to unlock personalised weekly insights 🌸",
        'emoji': '📊'
    }
def get_cycle_phase(cycle_day, cycle_length=28):
    if cycle_day <= 5:
        return {
            'phase': 'Menstrual',
            'emoji': '🔴',
            'description': 'Your body is shedding. Rest is productive, not lazy.',
            'color': '#e91e8c'
        }
    elif cycle_day <= 13:
        return {
            'phase': 'Follicular',
            'emoji': '🌱',
            'description': 'Energy is rising. Good time to take on new things.',
            'color': '#4CAF50'
        }
    elif cycle_day == 14:
        return {
            'phase': 'Ovulation',
            'emoji': '⭐',
            'description': 'Peak energy day. You might feel unusually social and sharp.',
            'color': '#FF9800'
        }
    else:
        return {
            'phase': 'Luteal',
            'emoji': '🌙',
            'description': 'Energy slowing down. Your body is preparing. Be gentle with yourself.',
            'color': '#9C27B0'
        }
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cyclofix-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cyclofix.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

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
    today = date.today()
    if current_user.last_period_start:
        current_day = (today - current_user.last_period_start).days + 1
    else:
        current_day = 1
    insight = generate_weekly_insight(current_user.id)
    phase = get_cycle_phase(current_day, current_user.cycle_length)
    return render_template('base.html', user=current_user, current_day=current_day, insight=insight, phase=phase)

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

        remember = request.form.get('remember') == 'true'
        login_user(user, remember=remember, duration = timedelta(days=365))
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

    from datetime import date as date_type
    return render_template('log.html', today=date_type.today())
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
@app.route('/patterns')
@login_required
def patterns():
    from collections import Counter

    # Get all logs for this user
    all_logs = CycleLog.query.filter_by(
        user_id=current_user.id
    ).order_by(CycleLog.date.asc()).all()

    # Build pain timeline data
    timeline = []
    for log in all_logs:
        if log.pain_intensity and log.cycle_day:
            timeline.append({
                'day': log.cycle_day,
                'intensity': log.pain_intensity,
                'type': log.pain_type
            })

    # What helped most
    helpful_logs = [l for l in all_logs if l.relief_helped == 'yes' and l.relief_suggestion]
    help_counts = Counter([l.relief_suggestion for l in helpful_logs])
    top_helpers = help_counts.most_common(3)

    # Pain type breakdown
    pain_types = Counter([l.pain_type for l in all_logs if l.pain_type])
    most_common_pain = pain_types.most_common(1)[0] if pain_types else None

    # Average pain per cycle day
    day_pain = {}
    for log in all_logs:
        if log.cycle_day and log.pain_intensity:
            if log.cycle_day not in day_pain:
                day_pain[log.cycle_day] = []
            day_pain[log.cycle_day].append(log.pain_intensity)
    avg_pain = {day: round(sum(vals)/len(vals), 1) for day, vals in day_pain.items()}
    worst_day = max(avg_pain, key=avg_pain.get) if avg_pain else None

    return render_template('patterns.html',
        user=current_user,
        timeline=timeline,
        top_helpers=top_helpers,
        most_common_pain=most_common_pain,
        avg_pain=avg_pain,
        worst_day=worst_day
    )
@app.route('/period_started', methods=['POST'])
@login_required
def period_started():
    today = date.today()
    current_user.last_period_start = today
    
    # Calculate cycle length from previous cycle if we have data
    if current_user.last_period_start:
        days_since = (today - current_user.last_period_start).days
        if 20 <= days_since <= 45:  # reasonable cycle length range
            current_user.cycle_length = days_since
    
    db.session.commit()
    return redirect(url_for('home'))
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)