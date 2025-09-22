from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="student")  # 'admin' or 'student'
    semester = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Syllabus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(20), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(20), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuestionPaper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    semester = db.Column(db.String(20), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False, index=True)
    year = db.Column(db.String(10), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    semester = db.Column(db.String(20), nullable=False, index=True)
    subject = db.Column(db.String(120), nullable=False, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Random question selection fields
    questions_per_attempt = db.Column(db.Integer, default=None)  # Number of questions to show per attempt (None = show all)
    randomize_questions = db.Column(db.Boolean, default=False)  # Whether to randomize question selection
    questions = db.relationship("QuizQuestion", backref="quiz", cascade="all, delete-orphan")

class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # 'A'/'B'/'C'/'D'

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey("quiz.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Add this line ↓
    quiz = db.relationship("Quiz", backref="attempts")

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    audience = db.Column(db.String(20), default="all")  # 'all'|'semester'|'user'
    audience_semester = db.Column(db.String(20))
    audience_user_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationRead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    notification_id = db.Column(db.Integer, nullable=False)
    read_at = db.Column(db.DateTime, default=datetime.utcnow)
