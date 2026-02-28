import streamlit as st
import sqlite3
import pandas as pd
import re
import bcrypt
import uuid
import time
from datetime import datetime

# ---------------------------
# DATABASE CONNECTION
# ---------------------------
conn = sqlite3.connect("ats_database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password BLOB
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
# SECURITY SETTINGS
# ---------------------------
SESSION_TIMEOUT = 1800  # 30 minutes

# ---------------------------
# SESSION MANAGEMENT
# ---------------------------
def regenerate_session():
    st.session_state.session_id = str(uuid.uuid4())

def logout():
    st.session_state.clear()
    st.rerun()

def check_timeout():
    if "last_activity" in st.session_state:
        elapsed = time.time() - st.session_state.last_activity
        if elapsed > SESSION_TIMEOUT:
            st.warning("⏳ Session expired due to inactivity.")
            logout()

# ---------------------------
# PHONE VALIDATION (POINT 82)
# ---------------------------
def valid_phone(phone):
    """
    Rules:
    ✔ Only digits
    ✔ Exactly 10 digits
    ✔ No spaces
    ✔ No special characters
    ✔ Cannot start with 0
    ✔ Duplicate allowed
    """
    pattern = r"^[1-9][0-9]{9}$"
    return re.fullmatch(pattern, phone)

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9@.\s]", "", text)

# ---------------------------
# DEFAULT ADMIN USER
# ---------------------------
def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute(
            "INSERT INTO users (username,password) VALUES (?,?)",
            ("admin", hashed)
        )
        conn.commit()

create_default_admin()

# ---------------------------
# LOGIN PAGE
# ---------------------------
def login_page():
    st.title("🔐 Takecare Manpower ATS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode(), user[0]):
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
    st.subheader("📊 ATS Tracking Dashboard")

    st.write(f"Welcome back, **{st.session_state.username}**")

    col1, col2 = st.columns([1,1])
    with col1:
        st.info("🎯 Target: 80+ Telescreening / 3-5 Interview / 1+ Joining")
    with col2:
        if st.button("🚪 Logout"):
            logout()

    st.divider()

    # ---------------------------
    # ADD CANDIDATE
    # ---------------------------
    st.subheader("➕ New Shortlist")

    name = clean_text(st.text_input("Candidate Name"))
    phone = st.text_input("Contact Number (10 digits only)")
    email = clean_text(st.text_input("Email"))
    position = clean_text(st.text_input("Position / Job Title"))

    if st.button("Save Candidate"):

        if not valid_phone(phone):
            st.error("""
            ❌ Invalid Phone Number:
            - Must be 10 digits
            - Only numbers allowed
            - No special characters
            - Cannot start with 0
            """)
        else:
            cursor.execute("""
                INSERT INTO candidates (name, phone, email, position, added_on)
                VALUES (?, ?, ?, ?, ?)
            """, (
                name,
                phone,
                email,
                position,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            conn.commit()
            st.success("✅ Candidate Saved Successfully")

    st.divider()

    # ---------------------------
    # VIEW CANDIDATES
    # ---------------------------
    st.subheader("📋 ATS Tracking Table")

    df = pd.read_sql_query("SELECT * FROM candidates ORDER BY id DESC", conn)
    st.dataframe(df, use_container_width=True)

    # ---------------------------
    # WHATSAPP SAFE LINK
    # ---------------------------
    st.subheader("📲 WhatsApp Invite")

    selected_phone = st.text_input("Enter Contact Number")

    if selected_phone:
        if valid_phone(selected_phone):
            wa_link = f"https://wa.me/91{selected_phone}"
            st.markdown(f"[👉 Open WhatsApp Chat]({wa_link})")
        else:
            st.error("Invalid Phone Number")

    # ---------------------------
    # DELETE OPTION
    # ---------------------------
    st.subheader("🗑 Delete Candidate")

    delete_id = st.number_input("Enter Candidate ID", min_value=1, step=1)

    if st.button("Delete"):
        cursor.execute("DELETE FROM candidates WHERE id=?", (delete_id,))
        conn.commit()
        st.success("Candidate Deleted Successfully")

    st.divider()

    # ---------------------------
    # BACKUP SYSTEM
    # ---------------------------
    st.subheader("💾 Backup Database")

    if st.button("Download CSV Backup"):
        backup_df = pd.read_sql_query("SELECT * FROM candidates", conn)
        csv = backup_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CSV File",
            data=csv,
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
