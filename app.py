from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///margdarshak.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'mentee' or 'mentor'
    sopi = db.Column(db.String(500))  # Statement of Purpose or Interest
    expertise = db.Column(db.String(500))  # For mentors

# Define MicroProject model
class MicroProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

# Home route
@app.route('/')
def home():
    return render_template('home.html')

# Sign-up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        sopi = request.form.get('sopi', '')
        expertise = request.form.get('expertise', '')

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('signup'))

        user = User(email=email, password=password, role=role, sopi=sopi, expertise=expertise)
        db.session.add(user)
        db.session.commit()
        flash('Sign-up successful! Please proceed.', 'success')
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    return render_template('signup.html')

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please sign up first.', 'danger')
        return redirect(url_for('signup'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

# Chatbot route for SOPI
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user_id' not in session:
        flash('Please sign up first.', 'danger')
        return redirect(url_for('signup'))
    user = User.query.get(session['user_id'])
    if user.role != 'mentee':
        flash('Only mentees can access the chatbot.', 'danger')
        return redirect(url_for('dashboard'))
    if user.sopi:
        return redirect(url_for('dashboard'))

    messages = session.get('chatbot_messages', [])
    if not messages:
        messages = [{'sender': 'bot', 'text': 'What are your entrepreneurial goals? (e.g., Start a fintech company)'}]
        session['chatbot_messages'] = messages

    if request.method == 'POST':
        user_input = request.form.get('input')
        messages.append({'sender': 'user', 'text': user_input})
        messages.append({'sender': 'bot', 'text': 'Got it! Your SOPI is saved. Proceed to find a mentor.'})
        session['chatbot_messages'] = messages
        user.sopi = user_input
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('chatbot.html', messages=messages)
# Match mentors route
@app.route('/match-mentors')
def match_mentors():
    if 'user_id' not in session:
        flash('Please sign up first.', 'danger')
        return redirect(url_for('signup'))
    user = User.query.get(session['user_id'])
    if user.role != 'mentee':
        flash('Only mentees can find mentors.', 'danger')
        return redirect(url_for('dashboard'))
    if not user.sopi:
        flash('Please set your SOPI first.', 'danger')
        return redirect(url_for('chatbot'))

    # Simulated AI: Keyword-based matching
    keywords = user.sopi.lower().split()
    mentors = User.query.filter_by(role='mentor').all()
    matched_mentors = [
        mentor for mentor in mentors
        if mentor.expertise and any(keyword in mentor.expertise.lower().split() for keyword in keywords)
    ]

    return render_template('match_mentors.html', mentors=matched_mentors, mentee_id=user.id)
# Event page route
@app.route('/event/<int:mentor_id>/<int:mentee_id>')
def event_page(mentor_id, mentee_id):
    if 'user_id' not in session:
        flash('Please sign up first.', 'danger')
        return redirect(url_for('signup'))
    user = User.query.get(session['user_id'])
    mentor = User.query.get(mentor_id)
    if user.role != 'mentee' or user.id != mentee_id:
        flash('Only the assigned mentee can view this event.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('event.html', mentor=mentor)
# Micro-projects route
@app.route('/micro-projects/<int:mentor_id>/<int:mentee_id>', methods=['GET', 'POST'])
def micro_projects(mentor_id, mentee_id):
    if 'user_id' not in session:
        flash('Please sign up first.', 'danger')
        return redirect(url_for('signup'))
    user = User.query.get(session['user_id'])
    mentor = User.query.get(mentor_id)
    mentee = User.query.get(mentee_id)

    if user.role == 'mentor' and user.id != mentor_id:
        flash('You can only assign projects as the selected mentor.', 'danger')
        return redirect(url_for('dashboard'))
    if user.role == 'mentee' and user.id != mentee_id:
        flash('You can only view your own projects.', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        micro_project = MicroProject(mentor_id=mentor_id, mentee_id=mentee_id, title=title, description=description)
        db.session.add(micro_project)
        db.session.commit()
        flash('Micro-project assigned successfully!', 'success')
        return redirect(url_for('micro_projects', mentor_id=mentor_id, mentee_id=mentee_id))

    projects = MicroProject.query.filter_by(mentee_id=mentee_id).all()
    return render_template('micro_projects.html', user=user, mentor=mentor, mentee=mentee, projects=projects)
# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)