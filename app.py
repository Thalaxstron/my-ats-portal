import streamlit as st
import sqlite3
import pandas as pd
import re
import uuid
import time
import hashlib
from datetime import datetime

# ---------------------------
# DATABASE
# ---------------------------
conn = sqlite3.connect("ats_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT,
    position TEXT,
    added_on TEXT
)
""")

conn.commit()

# ---------------------------
# HASH FUNCTION (No bcrypt)
# ---------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------
# DEFAULT ADMIN
# ---------------------------
def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            ("admin", hash_password("admin123"))
        )
        conn.commit()

create_default_admin()

# ---------------------------
# SESSION SETTINGS
# ---------------------------
SESSION_TIMEOUT = 1800  # 30 minutes

def regenerate_session():
    st.session_state.session_id = str(uuid.uuid4())

def logout():
    st.session_state.clear()
    st.rerun()

def check_timeout():
    if "last_activity" in st.session_state:
        if time.time() - st.session_state.last_activity > SESSION_TIMEOUT:
            st.warning("Session expired due to inactivity")
            logout()

# ---------------------------
# PHONE VALIDATION (82)
# ---------------------------
def valid_phone(phone):
    pattern = r"^[1-9][0-9]{9}$"
    return re.fullmatch(pattern, phone)

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9@.\s]", "", text)

# ---------------------------
# LOGIN PAGE
# ---------------------------
def login_page():
    st.title("🔐 ATS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and hash_password(password) == user[0]:
            regenerate_session()
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.last_activity = time.time()
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Username or Password")

# ---------------------------
# DASHBOARD
# ---------------------------
def dashboard():
    check_timeout()
    st.session_state.last_activity = time.time()

    st.title("🏢 Takecare Manpower Services Pvt Ltd")
    st.subheader("ATS Recruitment Dashboard")

    st.write(f"Welcome, **{st.session_state.username}**")

    if st.button("Logout"):
        logout()

    st.divider()

    # Add Candidate
    st.subheader("➕ Add Candidate")

    name = clean_text(st.text_input("Candidate Name"))
    phone = st.text_input("Contact Number (10 digits)")
    email = clean_text(st.text_input("Email"))
    position = clean_text(st.text_input("Position"))

    if st.button("Save Candidate"):
        if not valid_phone(phone):
            st.error("Invalid Phone Number (10 digits, no special characters, cannot start with 0)")
        else:
            cursor.execute("""
                INSERT INTO candidates (name,phone,email,position,added_on)
                VALUES (?,?,?,?,?)
            """, (
                name,
                phone,
                email,
                position,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            st.success("Candidate Saved Successfully")

    st.divider()

    # Candidate List
    st.subheader("📋 Candidate List")
    df = pd.read_sql_query("SELECT * FROM candidates ORDER BY id DESC", conn)
    st.dataframe(df, use_container_width=True)

    # WhatsApp Safe Link
    st.subheader("📲 WhatsApp Invite")
    selected_phone = st.text_input("Enter Phone Number")

    if selected_phone:
        if valid_phone(selected_phone):
            st.markdown(f"[Open WhatsApp Chat](https://wa.me/91{selected_phone})")
        else:
            st.error("Invalid Phone Number")

    # Delete
    st.subheader("🗑 Delete Candidate")
    delete_id = st.number_input("Enter Candidate ID", min_value=1, step=1)

    if st.button("Delete"):
        cursor.execute("DELETE FROM candidates WHERE id=?", (delete_id,))
        conn.commit()
        st.success("Deleted Successfully")

    # Backup
    st.subheader("💾 Backup")
    if st.button("Download CSV Backup"):
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Backup File",
            csv,
            file_name=f"ATS_Backup_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ---------------------------
# APP CONTROL
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    dashboard()
else:
    login_page()
