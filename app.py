import streamlit as st
import sqlite3
import pandas as pd
import re
import bcrypt
import uuid
import time
import os
from datetime import datetime, timedelta

# ---------------------------
# DATABASE SETUP
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
            st.warning("Session Expired. Please Login Again.")
            logout()

# ---------------------------
# SECURITY VALIDATIONS
# ---------------------------
def valid_phone(phone):
    return re.fullmatch(r"\d{10}", phone)

def clean_text(text):
    return re.sub(r"[^a-zA-Z0-9@.\s]", "", text)

# ---------------------------
# DEFAULT ADMIN USER
# ---------------------------
def create_default_admin():
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username,password) VALUES (?,?)",
                       ("admin", hashed))
        conn.commit()

create_default_admin()

# ---------------------------
# LOGIN SYSTEM
# ---------------------------
def login_page():
    st.title("🔐 ATS Login")

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
            st.error("Invalid Credentials")

# ---------------------------
# MAIN DASHBOARD
# ---------------------------
def dashboard():
    check_timeout()
    st.session_state.last_activity = time.time()

    st.title("📊 ATS Recruitment Dashboard")

    if st.button("Logout"):
        logout()

    st.subheader("➕ Add Candidate")

    name = clean_text(st.text_input("Candidate Name"))
    phone = st.text_input("Phone (10 digits only)")
    email = clean_text(st.text_input("Email"))
    position = clean_text(st.text_input("Position"))

    if st.button("Save Candidate"):

        if not valid_phone(phone):
            st.error("Invalid Phone Number (Only 10 digits allowed)")
        else:
            cursor.execute("""
                INSERT INTO candidates (name,phone,email,position,added_on)
                VALUES (?,?,?,?,?)
            """, (name, phone, email, position,
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            st.success("Candidate Saved Successfully")

    st.subheader("📋 Candidate List")

    df = pd.read_sql_query("SELECT * FROM candidates", conn)
    st.dataframe(df)

    # WhatsApp Safe Link
    if not df.empty:
        selected_phone = st.text_input("Enter Phone for WhatsApp")

        if valid_phone(selected_phone):
            wa_link = f"https://wa.me/91{selected_phone}"
            st.markdown(f"[Open WhatsApp Chat]({wa_link})")
        elif selected_phone:
            st.error("Invalid Phone Number")

    # Delete Option
    delete_id = st.number_input("Enter Candidate ID to Delete", step=1)
    if st.button("Delete Candidate"):
        cursor.execute("DELETE FROM candidates WHERE id=?", (delete_id,))
        conn.commit()
        st.success("Candidate Deleted")

    # Backup Section
    st.subheader("💾 Backup System")

    if st.button("Download CSV Backup"):
        backup_df = pd.read_sql_query("SELECT * FROM candidates", conn)
        backup_file = f"backup_{datetime.now().strftime('%Y%m%d')}.csv"
        backup_df.to_csv(backup_file, index=False)

        with open(backup_file, "rb") as f:
            st.download_button(
                label="Download File",
                data=f,
                file_name=backup_file,
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
