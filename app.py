import sqlite3
import re
import os
import shutil
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY_CHANGE_THIS"

DATABASE = "ats.db"
SESSION_TIMEOUT = 1800  # 30 minutes


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# INIT DATABASE
# -----------------------------
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id TEXT,
        name TEXT,
        phone TEXT UNIQUE,
        email TEXT,
        status TEXT,
        created_at TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        timestamp TEXT
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# SESSION TIMEOUT CHECK
# -----------------------------
@app.before_request
def session_management():
    if "user" in session:
        last_activity = session.get("last_activity")
        if last_activity:
            if datetime.now() > datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S") + timedelta(seconds=SESSION_TIMEOUT):
                session.clear()
                flash("Session expired. Please login again.")
                return redirect(url_for("login"))
        session["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session.clear()  # Clear old session
            session["user"] = username
            session["role"] = user["role"]
            session["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            flash("Login successful")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials")

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for("login"))


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    candidates = conn.execute("SELECT * FROM candidates WHERE active=1").fetchall()
    conn.close()

    return render_template("dashboard.html", candidates=candidates)


# -----------------------------
# PHONE VALIDATION
# -----------------------------
def valid_phone(phone):
    pattern = r"^[1-9][0-9]{9}$"
    return re.match(pattern, phone)


# -----------------------------
# ADD CANDIDATE
# -----------------------------
@app.route("/add_candidate", methods=["POST"])
def add_candidate():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form["name"]
    phone = request.form["phone"]
    email = request.form["email"]

    if not valid_phone(phone):
        flash("Invalid mobile number. Enter valid 10 digit number.")
        return redirect(url_for("dashboard"))

    conn = get_db()

    # Duplicate check
    existing = conn.execute("SELECT * FROM candidates WHERE phone=?", (phone,)).fetchone()
    if existing:
        flash("Candidate already exists.")
        return redirect(url_for("dashboard"))

    candidate_id = "CAND-" + datetime.now().strftime("%Y%m%d%H%M%S")

    conn.execute("""
        INSERT INTO candidates (candidate_id, name, phone, email, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (candidate_id, name, phone, email, "New", datetime.now()))

    conn.execute("""
        INSERT INTO activity_logs (user, action, timestamp)
        VALUES (?, ?, ?)
    """, (session["user"], f"Added candidate {name}", datetime.now()))

    conn.commit()
    conn.close()

    flash("Candidate added successfully")
    return redirect(url_for("dashboard"))


# -----------------------------
# SOFT DELETE
# -----------------------------
@app.route("/delete_candidate/<int:id>")
def delete_candidate(id):
    if "role" not in session or session["role"] != "admin":
        flash("Access denied")
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("UPDATE candidates SET active=0 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    flash("Candidate archived")
    return redirect(url_for("dashboard"))


# -----------------------------
# DAILY BACKUP
# -----------------------------
def backup_database():
    if not os.path.exists("backups"):
        os.makedirs("backups")

    backup_file = f"backups/ats_backup_{datetime.now().strftime('%Y%m%d')}.db"
    shutil.copyfile(DATABASE, backup_file)


# -----------------------------
# RATE LIMIT CHECK (WhatsApp Example)
# -----------------------------
def check_whatsapp_limit(user):
    conn = get_db()
    one_hour_ago = datetime.now() - timedelta(hours=1)

    count = conn.execute("""
        SELECT COUNT(*) as total FROM activity_logs
        WHERE user=? AND action LIKE '%WhatsApp%'
        AND timestamp > ?
    """, (user, one_hour_ago)).fetchone()["total"]

    conn.close()

    return count < 20


# -----------------------------
# CREATE DEFAULT ADMIN
# -----------------------------
def create_admin():
    conn = get_db()
    cursor = conn.cursor()

    admin = cursor.execute("SELECT * FROM users WHERE username='admin'").fetchone()

    if not admin:
        cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, ("admin", generate_password_hash("Admin@123"), "admin"))
        conn.commit()

    conn.close()


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    init_db()
    create_admin()
    app.run(debug=True)
