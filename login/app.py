import os
import secrets
import hmac
import hashlib
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# Import the API blueprint and database initialization
sys.path.insert(0, str(Path(__file__).parent.parent))
import api
import db as rhino_db

DB_PATH = Path("users.db")

def init_db_users():
    """Initialize user authentication database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # users table (add phone column if missing)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    # otps table for one-time codes
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code_hash TEXT NOT NULL,
            sent_via TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            expires_at DATETIME,
            used INTEGER DEFAULT 0,
            attempts INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    conn.commit()
    conn.close()


def get_db_conn():
    return sqlite3.connect(DB_PATH)


app = Flask(__name__)
# Prefer a stable secret from env for OTP HMACs and sessions; fallback to random for dev.
app.secret_key = os.environ.get("FLASK_SECRET") or os.urandom(24)

OTP_SECRET = os.environ.get("OTP_SECRET") or str(app.secret_key)

# Initialize both user and rhino databases
init_db_users()
rhino_db.init_db()

# Register the API blueprint for rhino tracking
app.register_blueprint(api.api)
@app.route("/")
def index():
    if session.get("user_email"):
        return f"Logged in as {session['user_email']} — <a href='/logout'>Logout</a>"
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        if not email or not password:
            error = "Email and password required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            pw_hash = generate_password_hash(password)
            try:
                conn = get_db_conn()
                cur = conn.cursor()
                cur.execute("INSERT INTO users (email, password_hash, phone) VALUES (?, ?, ?)", (email, pw_hash, phone))
                conn.commit()
                conn.close()
                flash("Account created. Please log in.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        conn.close()
        if not row:
            error = "Invalid email or password."
        else:
            pw_hash = row[0]
            if check_password_hash(pw_hash, password):
                # password OK — generate and send OTP, then require verification
                user = _get_user_by_email(email)
                if not user:
                    error = "User not found."
                else:
                    _create_and_send_otp(user['id'], user['email'], user.get('phone'))
                    session['pending_user_email'] = email
                    flash("OTP sent — please check your email (or console).")
                    return redirect(url_for('verify_otp'))
            else:
                error = "Invalid email or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Logged out.")
    return redirect(url_for("login"))


# --- OTP helpers and routes ---
def generate_numeric_otp(length=6):
    max_n = 10 ** length
    code = str(secrets.randbelow(max_n)).zfill(length)
    return code


def _hash_otp(code: str) -> str:
    return hmac.new(OTP_SECRET.encode(), code.encode(), hashlib.sha256).hexdigest()


def _get_user_by_email(email):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, email, phone FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "email": row[1], "phone": row[2]}


def _create_and_send_otp(user_id, email, phone=None, via='email'):
    code = generate_numeric_otp(6)
    code_hash = _hash_otp(code)
    created = datetime.utcnow()
    expires = created + timedelta(minutes=5)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO otps (user_id, code_hash, sent_via, created_at, expires_at, used, attempts) VALUES (?, ?, ?, ?, ?, 0, 0)",
        (user_id, code_hash, via, created.isoformat(), expires.isoformat()),
    )
    conn.commit()
    conn.close()
    # Delivery
    subject = "Your RhinoTracker one-time code"
    body = f"Your one-time login code is: {code}\nIt expires in 5 minutes."
    # Try sending via email if configured, otherwise print to console for dev/testing
    send_email(email, subject, body)


def send_email(to_email: str, subject: str, body: str):
    smtp_host = os.environ.get('SMTP_HOST')
    smtp_port = int(os.environ.get('SMTP_PORT', 0) or 0)
    smtp_user = os.environ.get('SMTP_USER')
    smtp_pass = os.environ.get('SMTP_PASS')
    from_addr = os.environ.get('SMTP_FROM') or 'no-reply@example.com'
    if smtp_host and smtp_port:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = from_addr
            msg['To'] = to_email
            msg.set_content(body)
            if os.environ.get('SMTP_USE_SSL') == '1':
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                if os.environ.get('SMTP_STARTTLS') == '1':
                    server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            print(f"OTP email sent to {to_email}")
            return True
        except Exception as e:
            print("Error sending email:", e)
            print("Falling back to printing OTP to console.")
    # Fallback for local testing: print
    print("--- OTP (dev) ---")
    print(body)
    print("-----------------")
    return False


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    error = None
    pending = session.get('pending_user_email')
    if not pending:
        flash('No pending login. Please login first.')
        return redirect(url_for('login'))
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user = _get_user_by_email(pending)
        if not user:
            error = 'User not found.'
            return render_template('otp_verify.html', error=error)
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, code_hash, expires_at, used, attempts FROM otps WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user['id'],))
        row = cur.fetchone()
        if not row:
            error = 'No OTP found. Request a new code.'
            conn.close()
            return render_template('otp_verify.html', error=error)
        otp_id, code_hash, expires_at, used, attempts = row
        if used:
            error = 'This code has already been used. Request a new code.'
            conn.close()
            return render_template('otp_verify.html', error=error)
        # check expiry
        if expires_at:
            exp = datetime.fromisoformat(expires_at)
            if datetime.utcnow() > exp:
                error = 'Code expired. Request a new one.'
                conn.close()
                return render_template('otp_verify.html', error=error)
        # limit attempts
        if attempts >= 5:
            error = 'Too many attempts. Request a new code.'
            conn.close()
            return render_template('otp_verify.html', error=error)
        # verify
        if hmac.compare_digest(code_hash, _hash_otp(code)):
            # success
            cur.execute("UPDATE otps SET used = 1 WHERE id = ?", (otp_id,))
            conn.commit()
            conn.close()
            session.pop('pending_user_email', None)
            session['user_email'] = pending
            flash('Logged in successfully.')
            return redirect(url_for('index'))
        else:
            # increment attempts
            cur.execute("UPDATE otps SET attempts = attempts + 1 WHERE id = ?", (otp_id,))
            conn.commit()
            conn.close()
            error = 'Invalid code.'
    return render_template('otp_verify.html', error=error)


if __name__ == "__main__":
    app.run(debug=True)
