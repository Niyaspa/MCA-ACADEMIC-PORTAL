from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pathlib import Path
import random

from models import db, User, Syllabus, Note, QuestionPaper, Quiz, QuizQuestion, QuizAttempt, Notification
from utils import allowed_file, send_email
from config import Config

def get_available_subjects(model_class):
    """Get distinct subjects from the specified model class"""
    return [s[0] for s in db.session.query(model_class.subject).distinct().order_by(model_class.subject).all()]

def build_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    upload_root = Path(app.config["UPLOAD_FOLDER"])

    # ---------------- Home ----------------
    @app.route("/")
    def index():
        return render_template("index.html")

    # ---------------- Auth ----------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name","").strip()
            email = request.form.get("email","").strip().lower()
            password = request.form.get("password","")
            semester = request.form.get("semester","").strip()
            if not name or not email or not password:
                flash("All fields are required", "error")
                return redirect(url_for("register"))
            if User.query.filter_by(email=email).first():
                flash("Email already registered.", "error")
                return redirect(url_for("register"))
            user = User(name=name, email=email, password_hash=generate_password_hash(password),
                        role="student", semester=semester)
            db.session.add(user)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email","").strip().lower()
            password = request.form.get("password","")
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash("Logged in successfully.", "success")
                return redirect(url_for("admin_dashboard" if user.role=="admin" else "student_dashboard"))
            flash("Invalid credentials.", "error")
        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    # ---------------- Student ----------------
    @app.route("/student/dashboard")
    @login_required
    def student_dashboard():
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        # Filter notifications visible to the student
        notifs = Notification.query.order_by(Notification.created_at.desc()).all()
        visible = []
        for n in notifs:
            if n.audience == "all":
                visible.append(n)
            elif n.audience == "semester" and current_user.semester and n.audience_semester == current_user.semester:
                visible.append(n)
            elif n.audience == "user" and n.audience_user_id == current_user.id:
                visible.append(n)
        attempts = (QuizAttempt.query
                    .filter_by(user_id=current_user.id)
                    .order_by(QuizAttempt.taken_at.desc()).limit(5).all())
        return render_template("student/dashboard.html", notifications=visible[:10], attempts=attempts)

    # ---------------- Resources (student) ----------------
    @app.route("/syllabus")
    @login_required
    def syllabus_list():
        semester = request.args.get("semester", current_user.semester or "")
        subject = request.args.get("subject", "")
        q = Syllabus.query
        if semester:
            q = q.filter_by(semester=semester)
        if subject:
            q = q.filter_by(subject=subject)
        items = q.order_by(Syllabus.semester, Syllabus.subject).all()
        # Get available subjects for dropdown
        available_subjects = get_available_subjects(Syllabus)
        return render_template("resources/list.html", title="Syllabus",
                               resource="syllabus", items=items, semester=semester,
                               subject=subject, available_subjects=available_subjects)

    @app.route("/notes")
    @login_required
    def notes_list():
        semester = request.args.get("semester", current_user.semester or "")
        subject = request.args.get("subject", "")
        q = Note.query
        if semester:
            q = q.filter_by(semester=semester)
        if subject:
            q = q.filter_by(subject=subject)
        items = q.order_by(Note.semester, Note.subject, Note.title).all()
        # Get available subjects for dropdown
        available_subjects = get_available_subjects(Note)
        return render_template("resources/list.html", title="Study Notes",
                               resource="notes", items=items, semester=semester,
                               subject=subject, available_subjects=available_subjects)

    @app.route("/papers")
    @login_required
    def papers_list():
        semester = request.args.get("semester", current_user.semester or "")
        subject = request.args.get("subject", "")
        q = QuestionPaper.query
        if semester:
            q = q.filter_by(semester=semester)
        if subject:
            q = q.filter_by(subject=subject)
        items = q.order_by(QuestionPaper.semester, QuestionPaper.subject,
                           QuestionPaper.year.desc()).all()
        # Get available subjects for dropdown
        available_subjects = get_available_subjects(QuestionPaper)
        return render_template("resources/list.html", title="Question Papers",
                               resource="papers", items=items, semester=semester,
                               subject=subject, available_subjects=available_subjects)

    @app.route("/uploads/<path:sub>/<path:filename>")
    @login_required
    def download_file(sub, filename):
        folder = upload_root / sub
        return send_from_directory(folder, filename, as_attachment=True)

    # ---------------- Quizzes ----------------
    @app.route("/quizzes")
    @login_required
    def quiz_list():
        semester = request.args.get("semester", current_user.semester or "")
        subject = request.args.get("subject", "")
        q = Quiz.query
        if semester:
            q = q.filter_by(semester=semester)
        if subject:
            q = q.filter_by(subject=subject)
        items = q.order_by(Quiz.created_at.desc()).all()
        # Get available subjects for dropdown
        available_subjects = get_available_subjects(Quiz)
        return render_template("quiz/list.html", items=items, semester=semester,
                               subject=subject, available_subjects=available_subjects)

    @app.route("/quiz/<int:quiz_id>", methods=["GET", "POST"])
    @login_required
    def take_quiz(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        
        # Get questions for this quiz attempt
        if quiz.randomize_questions and quiz.questions_per_attempt and len(quiz.questions) > quiz.questions_per_attempt:
            # Random selection enabled and we have more questions than needed
            selected_questions = random.sample(list(quiz.questions), quiz.questions_per_attempt)
        else:
            # Use all questions (either no randomization or not enough questions to select from)
            selected_questions = list(quiz.questions)
        
        if request.method == "POST":
            total = len(selected_questions)
            score = 0
            # We need to get the selected questions from the submitted form
            # The question IDs are embedded in the form field names
            submitted_question_ids = set()
            for field_name in request.form:
                if field_name.startswith('q'):
                    q_id = field_name[1:]  # Remove 'q' prefix
                    if q_id.isdigit():
                        submitted_question_ids.add(int(q_id))
            
            # Score based on submitted questions only
            for q in quiz.questions:
                if q.id in submitted_question_ids:
                    ans = request.form.get(f"q{q.id}")
                    if ans and ans.upper() == q.correct_option.upper():
                        score += 1
            
            attempt = QuizAttempt(user_id=current_user.id, quiz_id=quiz.id,
                                  score=score, total=total)
            db.session.add(attempt)
            db.session.commit()
            flash(f"You scored {score}/{total}", "success")
            return redirect(url_for("quiz_result", attempt_id=attempt.id))
        
        # Create a copy of the quiz object with selected questions for the template
        class QuizWithSelectedQuestions:
            def __init__(self, original_quiz, selected_questions):
                self.id = original_quiz.id
                self.title = original_quiz.title
                self.semester = original_quiz.semester
                self.subject = original_quiz.subject
                self.questions = selected_questions
                self.randomize_questions = original_quiz.randomize_questions
                self.questions_per_attempt = original_quiz.questions_per_attempt
                self.total_questions = len(original_quiz.questions)
        
        quiz_for_template = QuizWithSelectedQuestions(quiz, selected_questions)
        return render_template("quiz/take_quiz.html", quiz=quiz_for_template)

    @app.route("/quiz/result/<int:attempt_id>")
    @login_required
    def quiz_result(attempt_id):
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        quiz = Quiz.query.get_or_404(attempt.quiz_id)
        return render_template("quiz/results.html", attempt=attempt, quiz=quiz)

    # ---------------- Notifications (student) ----------------
    @app.route("/notifications")
    @login_required
    def notifications():
        notifs = Notification.query.order_by(Notification.created_at.desc()).all()
        visible = []
        for n in notifs:
            if n.audience == "all":
                visible.append(n)
            elif n.audience == "semester" and current_user.semester and n.audience_semester == current_user.semester:
                visible.append(n)
            elif n.audience == "user" and n.audience_user_id == current_user.id:
                visible.append(n)
        return render_template("notifications/list.html", notifications=visible)

    # ---------------- Admin ----------------
    def admin_required(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != "admin":
                flash("Admin access required.", "error")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper

    @app.route("/admin/dashboard")
    @login_required
    @admin_required
    def admin_dashboard():
        stats = {
            "students": User.query.filter_by(role="student").count(),
            "syllabus": Syllabus.query.count(),
            "notes": Note.query.count(),
            "papers": QuestionPaper.query.count(),
            "quizzes": Quiz.query.count()
        }
        recent = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
        return render_template("admin/dashboard.html", stats=stats, notifications=recent)

    def handle_upload(subfolder):
        file = request.files.get("file")
        semester = request.form.get("semester","").strip()
        subject = request.form.get("subject","").strip()
        title = request.form.get("title","").strip()
        year = request.form.get("year","").strip()

        if not file or file.filename == "":
            flash("No file selected", "error")
            return None
        if not allowed_file(file.filename):
            flash("Invalid file type", "error")
            return None
        filename = secure_filename(file.filename)
        folder = upload_root / subfolder
        folder.mkdir(parents=True, exist_ok=True)
        file.save(folder / filename)

        if subfolder == "syllabus":
            rec = Syllabus(semester=semester, subject=subject, filename=filename)
        elif subfolder == "notes":
            rec = Note(semester=semester, subject=subject, title=title or filename, filename=filename)
        elif subfolder == "papers":
            rec = QuestionPaper(semester=semester, subject=subject, year=year or "NA", filename=filename)
        else:
            return None
        db.session.add(rec)
        db.session.commit()
        flash("Uploaded successfully.", "success")
        return rec

    @app.route("/admin/upload/<string:rtype>", methods=["GET", "POST"])
    @login_required
    @admin_required
    def admin_upload(rtype):
        if rtype not in {"syllabus","notes","papers"}:
            flash("Invalid resource type", "error")
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            rec = handle_upload(rtype)
            if rec:
                return redirect(url_for("admin_upload", rtype=rtype))
        return render_template("admin/upload.html", rtype=rtype)

    @app.route("/admin/manage/<string:rtype>")
    @login_required
    @admin_required
    def admin_manage(rtype):
        semester = request.args.get("semester", "")
        subject = request.args.get("subject", "")
        
        if rtype == "syllabus":
            q = Syllabus.query
            if semester:
                q = q.filter_by(semester=semester)
            if subject:
                q = q.filter_by(subject=subject)
            items = q.order_by(Syllabus.semester, Syllabus.subject).all()
            available_subjects = get_available_subjects(Syllabus)
        elif rtype == "notes":
            q = Note.query
            if semester:
                q = q.filter_by(semester=semester)
            if subject:
                q = q.filter_by(subject=subject)
            items = q.order_by(Note.semester, Note.subject, Note.title).all()
            available_subjects = get_available_subjects(Note)
        elif rtype == "papers":
            q = QuestionPaper.query
            if semester:
                q = q.filter_by(semester=semester)
            if subject:
                q = q.filter_by(subject=subject)
            items = q.order_by(QuestionPaper.semester, QuestionPaper.subject, QuestionPaper.year.desc()).all()
            available_subjects = get_available_subjects(QuestionPaper)
        else:
            flash("Invalid resource type", "error")
            return redirect(url_for("admin_dashboard"))
        return render_template("admin/manage_resources.html", rtype=rtype, items=items,
                               semester=semester, subject=subject, available_subjects=available_subjects)

    @app.route("/admin/delete/<string:rtype>/<int:item_id>", methods=["POST"])
    @login_required
    @admin_required
    def admin_delete_resource(rtype, item_id):
        model_map = {"syllabus": Syllabus, "notes": Note, "papers": QuestionPaper}
        M = model_map.get(rtype)
        if not M:
            flash("Invalid type", "error")
            return redirect(url_for("admin_dashboard"))
        rec = M.query.get_or_404(item_id)
        # remove file
        sub = "syllabus" if rtype=="syllabus" else ("notes" if rtype=="notes" else "papers")
        fpath = upload_root / sub / rec.filename
        try:
            if fpath.exists():
                fpath.unlink()
        except Exception as e:
            print("Failed to delete file:", e)
        db.session.delete(rec)
        db.session.commit()
        flash("Deleted.", "info")
        return redirect(url_for("admin_manage", rtype=rtype))

    # ---- Quizzes (admin)
    @app.route("/admin/quizzes")
    @login_required
    @admin_required
    def admin_quizzes():
        semester = request.args.get("semester", "")
        subject = request.args.get("subject", "")
        q = Quiz.query
        if semester:
            q = q.filter_by(semester=semester)
        if subject:
            q = q.filter_by(subject=subject)
        items = q.order_by(Quiz.created_at.desc()).all()
        # Get available subjects for dropdown
        available_subjects = get_available_subjects(Quiz)
        return render_template("quiz/admin_list.html", items=items, semester=semester,
                               subject=subject, available_subjects=available_subjects)

    @app.route("/admin/quiz/create", methods=["GET","POST"])
    @login_required
    @admin_required
    def admin_quiz_create():
        if request.method == "POST":
            title = request.form.get("title","").strip()
            semester = request.form.get("semester","").strip()
            subject = request.form.get("subject","").strip()
            if not title or not semester or not subject:
                flash("All fields are required", "error")
                return redirect(url_for("admin_quiz_create"))
            
            # Handle random selection fields
            randomize_questions = bool(request.form.get("randomize_questions"))
            questions_per_attempt = None
            if randomize_questions:
                questions_per_attempt_str = request.form.get("questions_per_attempt", "").strip()
                if questions_per_attempt_str:
                    try:
                        questions_per_attempt = int(questions_per_attempt_str)
                        if questions_per_attempt <= 0:
                            flash("Questions per attempt must be a positive number", "error")
                            return redirect(url_for("admin_quiz_create"))
                    except ValueError:
                        flash("Invalid number for questions per attempt", "error")
                        return redirect(url_for("admin_quiz_create"))
            
            qz = Quiz(
                title=title, 
                semester=semester, 
                subject=subject, 
                created_by=current_user.id,
                randomize_questions=randomize_questions,
                questions_per_attempt=questions_per_attempt
            )
            db.session.add(qz)
            db.session.commit()
            
            if randomize_questions and questions_per_attempt:
                flash(f"Quiz created with random selection ({questions_per_attempt} questions per attempt). Now add questions.", "success")
            elif randomize_questions:
                flash("Quiz created with random selection (all questions). Now add questions.", "success")
            else:
                flash("Quiz created. Now add questions.", "success")
            return redirect(url_for("admin_quiz_add_question", quiz_id=qz.id))
        return render_template("quiz/create_quiz.html")

    @app.route("/admin/quiz/<int:quiz_id>/add", methods=["GET","POST"])
    @login_required
    @admin_required
    def admin_quiz_add_question(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        if request.method == "POST":
            question = request.form.get("question","").strip()
            options = {k: request.form.get(k,"").strip() for k in ["option_a","option_b","option_c","option_d"]}
            correct = request.form.get("correct_option","").strip().upper()
            if not question or not all(options.values()) or correct not in {"A","B","C","D"}:
                flash("Please fill all fields and choose correct option A/B/C/D.", "error")
                return redirect(url_for("admin_quiz_add_question", quiz_id=quiz.id))
            qq = QuizQuestion(quiz_id=quiz.id, question=question, correct_option=correct, **options)
            db.session.add(qq)
            db.session.commit()
            flash("Question added.", "success")
            return redirect(url_for("admin_quiz_add_question", quiz_id=quiz.id))
        return render_template("quiz/add_question.html", quiz=quiz)

    @app.route("/admin/quiz/<int:quiz_id>/delete", methods=["POST"])
    @login_required
    @admin_required
    def admin_quiz_delete(quiz_id):
        quiz = Quiz.query.get_or_404(quiz_id)
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted.", "info")
        return redirect(url_for("admin_quizzes"))

    # ---- Notifications (admin)
    @app.route("/admin/notify", methods=["GET","POST"])
    @login_required
    @admin_required
    def admin_notify():
        if request.method == "POST":
            title = request.form.get("title","").strip()
            body = request.form.get("body","").strip()
            link = request.form.get("link","").strip() or None
            audience = request.form.get("audience","all")
            audience_semester = request.form.get("audience_semester","").strip() or None
            audience_user_id = request.form.get("audience_user_id","").strip() or None

            n = Notification(
                title=title, body=body, link=link,
                audience=audience, audience_semester=audience_semester,
                audience_user_id=int(audience_user_id) if audience_user_id else None
            )
            db.session.add(n)
            db.session.commit()

            # Optional email fan-out
            recipients = []
            if audience == "all":
                recipients = [u.email for u in User.query.filter_by(role="student").all()]
            elif audience == "semester" and audience_semester:
                recipients = [u.email for u in User.query.filter_by(role="student", semester=audience_semester).all()]
            elif audience == "user" and audience_user_id:
                u = User.query.filter_by(id=int(audience_user_id)).first()
                if u: recipients = [u.email]

            sent = 0
            for r in recipients:
                if send_email(r, f"[MCA Portal] {title}", body):
                    sent += 1
            flash(f"Notification created. Emails sent: {sent}", "success")
            return redirect(url_for("admin_notify"))

        users = User.query.order_by(User.name).all()
        return render_template("admin/notify.html", users=users)

    return app

app = build_app()

if __name__ == "__main__":
    app.run(debug=True)
