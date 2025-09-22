import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
    if DATABASE_URL:
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'mca_portal.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = INSTANCE_DIR / "uploads"
    (UPLOAD_FOLDER / "syllabus").mkdir(parents=True, exist_ok=True)
    (UPLOAD_FOLDER / "notes").mkdir(parents=True, exist_ok=True)
    (UPLOAD_FOLDER / "papers").mkdir(parents=True, exist_ok=True)

    # Optional SMTP (used by utils.send_email)
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@mca-portal.local")
