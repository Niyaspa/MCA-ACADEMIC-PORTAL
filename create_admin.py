from werkzeug.security import generate_password_hash
from app import app
from models import db, User

with app.app_context():
    db.create_all()
    email = "admin@example.com"
    if not User.query.filter_by(email=email).first():
        admin = User(
            name="Administrator",
            email=email,
            password_hash=generate_password_hash("admin123"),
            role="admin",
            semester=None
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin@example.com / admin123")
    else:
        print("Admin user already exists.")
