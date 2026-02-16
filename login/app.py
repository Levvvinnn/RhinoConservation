import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

DB_PATH = Path("users.db")

def init_db():
    if not DB_PATH.exists():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

def get_db_conn():
    return sqlite3.connect(DB_PATH)

app = Flask(__name__)
app.secret_key = os.urandom(24)

init_db()

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
                cur.execute("INSERT INTO users (email, password_hash) VALUES (?, ?)", (email, pw_hash))
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
                session["user_email"] = email
                flash("Logged in successfully.")
                return redirect(url_for("index"))
            else:
                error = "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user_email", None)
    flash("Logged out.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
