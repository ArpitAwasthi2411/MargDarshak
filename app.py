from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///margdarshak.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder for profile photos
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Allowed file extensions
db = SQLAlchemy(app)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'entrepreneur' or 'mentor'
    vision_statement = db.Column(db.String(500))  # Renamed from SOPI for entrepreneurs
    bio = db.Column(db.String(500))  # Bio for entrepreneurs
    research_projects = db.Column(db.Text)  # Research or projects for entrepreneurs
    experience = db.Column(db.Text)  # For mentors
    work = db.Column(db.Text)  # For mentors
    projects = db.Column(db.Text)  # For mentors
    students_mented = db.Column(db.Integer, default=0)  # For mentors
    profile_photo = db.Column(db.String(200))  # Path to profile photo
    goals = db.relationship('Goal', backref='user', lazy=True)  # Entrepreneurs' goals
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    messages_received = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    mentorship_requests_sent = db.relationship('MentorshipRequest', foreign_keys='MentorshipRequest.entrepreneur_id', backref='entrepreneur', lazy=True)
    mentorship_requests_received = db.relationship('MentorshipRequest', foreign_keys='MentorshipRequest.mentor_id', backref='mentor', lazy=True)
    login_history = db.relationship('LoginHistory', backref='user', lazy=True)

# Define Goal model
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500))
    deadline = db.Column(db.String(50))
    status = db.Column(db.String(50), default='In Progress')  # e.g., "In Progress", "Completed"

# Define Message model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())

# Define SuccessStory model
class SuccessStory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    entrepreneur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image = db.Column(db.String(200))  # URL or path to image
    entrepreneur = db.relationship('User', foreign_keys=[entrepreneur_id], backref='success_stories_as_entrepreneur')
    mentor = db.relationship('User', foreign_keys=[mentor_id], backref='success_stories_as_mentor')

# Define MentorshipRequest model
class MentorshipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entrepreneur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'declined'
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())

# Define LoginHistory model
class LoginHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False, default=db.func.now())

# Create the database
with app.app_context():
    db.create_all()

# Simple keyword-based matching function
def match_users(user_text, target_users, target_field='experience'):
    if not user_text or not target_users:
        return []

    # Convert user_text to lowercase and split into keywords
    user_keywords = set(user_text.lower().split())

    # Calculate a match score for each target user based on keyword overlap
    matched_users = []
    for user in target_users:
        target_text = getattr(user, target_field) or ''
        target_keywords = set(target_text.lower().split())
        common_keywords = user_keywords.intersection(target_keywords)
        # Score is the number of common keywords divided by the total number of user keywords
        score = len(common_keywords) / len(user_keywords) if user_keywords else 0
        matched_users.append((user, score))

    # Sort by score in descending order
    matched_users.sort(key=lambda x: x[1], reverse=True)
    return matched_users

# Home route
@app.route('/')
def home():
    success_stories = SuccessStory.query.all()
    return render_template('home.html', success_stories=success_stories)

# Sign-up route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('signup'))

        user = User(name=name, username=username, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        return redirect(url_for('onboarding'))
    return render_template('signup.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            # Log the login time
            login_entry = LoginHistory(user_id=user.id)
            db.session.add(login_entry)
            db.session.commit()
            if user.vision_statement or user.experience:  # Check if onboarding is done
                return redirect(url_for('dashboard'))
            return redirect(url_for('onboarding'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

# Onboarding route
@app.route('/onboarding', methods=['GET', 'POST'])
def onboarding():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if user.role == 'entrepreneur':
            user.vision_statement = request.form.get('vision_statement')
            user.bio = request.form.get('bio')
            user.research_projects = request.form.get('research_projects')
        else:  # mentor
            user.experience = request.form.get('experience')
            user.work = request.form.get('work')
            user.projects = request.form.get('projects')
            user.students_mented = int(request.form.get('students_mented', 0))

        # Handle profile photo upload
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                user.profile_photo = f'uploads/{filename}'

        db.session.commit()
        flash('Profile setup completed! Welcome to MargDarshak.', 'success')
        return redirect(url_for('dashboard'))
    return render_template('onboarding.html', user=user)

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    goals = Goal.query.filter_by(user_id=user.id).all() if user.role == 'entrepreneur' else []
    login_history = LoginHistory.query.filter_by(user_id=user.id).order_by(LoginHistory.login_time.desc()).limit(5).all()
    messages = Message.query.filter_by(receiver_id=user.id).order_by(Message.timestamp.desc()).limit(5).all()
    mentorship_requests = MentorshipRequest.query.filter_by(mentor_id=user.id, status='pending').all() if user.role == 'mentor' else []
    return render_template('dashboard.html', user=user, goals=goals, login_history=login_history, messages=messages, mentorship_requests=mentorship_requests)

# Goal management route
@app.route('/add-goal', methods=['POST'])
def add_goal():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'entrepreneur':
        flash('Only entrepreneurs can add goals.', 'danger')
        return redirect(url_for('dashboard'))

    title = request.form.get('title')
    description = request.form.get('description')
    deadline = request.form.get('deadline')
    goal = Goal(user_id=user.id, title=title, description=description, deadline=deadline)
    db.session.add(goal)
    db.session.commit()
    flash('Goal added successfully!', 'success')
    return redirect(url_for('dashboard'))

# Messaging route
@app.route('/messages/<int:other_user_id>', methods=['GET', 'POST'])
def messages(other_user_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    other_user = User.query.get(other_user_id)

    if request.method == 'POST':
        content = request.form.get('content')
        message = Message(sender_id=user.id, receiver_id=other_user.id, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Message sent!', 'success')

    messages = Message.query.filter(
        ((Message.sender_id == user.id) & (Message.receiver_id == other_user.id)) |
        ((Message.sender_id == other_user.id) & (Message.receiver_id == user.id))
    ).order_by(Message.timestamp.asc()).all()
    return render_template('messages.html', user=user, other_user=other_user, messages=messages)

# Chatbot route
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'entrepreneur':
        flash('Only entrepreneurs can access the chatbot.', 'danger')
        return redirect(url_for('dashboard'))

    messages = session.get('chatbot_messages', [])
    if not messages:
        messages = [{'sender': 'bot', 'text': 'What courses would you like to explore to grow in your field?'}]
        session['chatbot_messages'] = messages

    if request.method == 'POST':
        user_input = request.form.get('input')
        messages.append({'sender': 'user', 'text': user_input})

        # Simple course suggestion logic based on vision statement
        vision_keywords = user.vision_statement.lower().split() if user.vision_statement else []
        course_suggestions = []
        if 'fintech' in vision_keywords:
            course_suggestions.append('Introduction to Fintech on Coursera')
        if 'ai' in vision_keywords or 'machine learning' in vision_keywords:
            course_suggestions.append('Machine Learning by Andrew Ng on Coursera')
        if 'marketing' in vision_keywords:
            course_suggestions.append('Digital Marketing Specialization on Coursera')
        if not course_suggestions:
            course_suggestions.append('General Entrepreneurship Course on Udemy')

        response = f"Based on your vision statement, I recommend the following courses: {', '.join(course_suggestions)}."
        messages.append({'sender': 'bot', 'text': response})
        session['chatbot_messages'] = messages
        return redirect(url_for('chatbot'))

    return render_template('chatbot.html', messages=messages)

# Match mentors route with mentorship requests
# Match mentors route with mentorship requests
@app.route('/match-mentors', methods=['GET', 'POST'])
def match_mentors():
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])

    if user.role == 'entrepreneur':
        if not user.vision_statement:
            flash('Please set your Vision Statement first.', 'danger')
            return redirect(url_for('onboarding'))

        mentors = User.query.filter_by(role='mentor').all()
        search_query = request.form.get('search', '').lower() if request.method == 'POST' else ''

        # Filter mentors based on search query
        if search_query:
            mentors = [mentor for mentor in mentors if search_query in (mentor.experience or '').lower()]

        # Simple keyword-based matching based on vision statement
        matched_mentors = match_users(user.vision_statement, mentors, target_field='experience')
        matched_mentors = [(mentor, score) for mentor, score in matched_mentors if mentor in mentors]

        # Check existing mentorship requests
        existing_requests = {req.mentor_id: req.status for req in MentorshipRequest.query.filter_by(entrepreneur_id=user.id).all()}

        return render_template('match_mentors.html', user=user, mentors=matched_mentors, entrepreneur_id=user.id, existing_requests=existing_requests)

    else:  # user.role == 'mentor'
        entrepreneurs = User.query.filter_by(role='entrepreneur').all()
        search_query = request.form.get('search', '').lower() if request.method == 'POST' else ''

        # Filter entrepreneurs based on search query
        if search_query:
            entrepreneurs = [entrepreneur for entrepreneur in entrepreneurs if search_query in (entrepreneur.vision_statement or '').lower()]

        matched_entrepreneurs = match_users(user.experience, entrepreneurs, target_field='vision_statement')
        return render_template('match_mentors.html', user=user, entrepreneurs=matched_entrepreneurs, mentor_id=user.id)
   
# Mentorship request route
@app.route('/request-mentorship/<int:mentor_id>', methods=['POST'])
def request_mentorship(mentor_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'entrepreneur':
        flash('Only entrepreneurs can request mentorship.', 'danger')
        return redirect(url_for('dashboard'))

    existing_request = MentorshipRequest.query.filter_by(entrepreneur_id=user.id, mentor_id=mentor_id).first()
    if existing_request:
        flash('You have already sent a mentorship request to this mentor.', 'info')
    else:
        mentorship_request = MentorshipRequest(entrepreneur_id=user.id, mentor_id=mentor_id)
        db.session.add(mentorship_request)
        db.session.commit()
        flash('Mentorship request sent!', 'success')
    return redirect(url_for('match_mentors'))

# Handle mentorship requests
@app.route('/handle-mentorship-request/<int:request_id>/<action>', methods=['POST'])
def handle_mentorship_request(request_id, action):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if user.role != 'mentor':
        flash('Only mentors can handle mentorship requests.', 'danger')
        return redirect(url_for('dashboard'))

    mentorship_request = MentorshipRequest.query.get(request_id)
    if mentorship_request.mentor_id != user.id:
        flash('You can only handle your own mentorship requests.', 'danger')
        return redirect(url_for('dashboard'))

    if action == 'accept':
        mentorship_request.status = 'accepted'
        user.students_mented += 1
    elif action == 'decline':
        mentorship_request.status = 'declined'
    db.session.commit()
    flash(f'Mentorship request {action}ed!', 'success')
    return redirect(url_for('dashboard'))

# Event page route
@app.route('/event/<int:mentor_id>/<int:entrepreneur_id>')
def event_page(mentor_id, entrepreneur_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'danger')
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    mentor = User.query.get(mentor_id)
    if user.role != 'entrepreneur' or user.id != entrepreneur_id:
        flash('Only the assigned entrepreneur can view this event.', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('event.html', mentor=mentor)

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)