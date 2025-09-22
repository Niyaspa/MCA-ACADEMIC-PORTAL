import smtplib
from email.message import EmailMessage
from flask import current_app

def allowed_file(filename):
    allowed = {"pdf","doc","docx","ppt","pptx","txt","zip","png","jpg","jpeg"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed

def send_email(to_email, subject, body):
    cfg = current_app.config
    server = cfg.get("MAIL_SERVER")
    if not server or not to_email:
        return False
    msg = EmailMessage()
    msg["From"] = cfg.get("FROM_EMAIL")
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    try:
        if cfg.get("MAIL_USE_TLS", True):
            s = smtplib.SMTP(server, cfg.get("MAIL_PORT", 587))
            s.starttls()
        else:
            s = smtplib.SMTP(server, cfg.get("MAIL_PORT", 25))
        if cfg.get("MAIL_USERNAME"):
            s.login(cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD"))
        s.send_message(msg)
        s.quit()
        return True
    except Exception as e:
        print("Email send failed:", e)
        return False
    