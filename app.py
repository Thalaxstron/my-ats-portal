import streamlit as st
import sqlite3
import re
from datetime import datetime, timedelta

# -------------------- SESSION TIMEOUT --------------------
SESSION_TIMEOUT = 30  # minutes

# -------------------- DATABASE --------------------
conn = sqlite3.connect("ats.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT,
    experience TEXT,
    status TEXT
)
""")

conn.commit()

# Default user create (first time only)
try:
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("admin", "admin123"))
    conn.commit()
except:
    pass


# -------------------- CSS FIX (No layout change) --------------------
st.markdown("""
<style>

div[data-baseweb="input"] > div {
    background-color: white !important;
}

input {
    background-color: white !important;
    color: black !important;
    font-weight: 500 !important;
}

/* Red Login Button */
.stButton > button {
    background-color: #d32f2f !important;
    color: white !important;
    border-radius: 8px !important;
    font-weight: bold !important;
    border: none !important;
}

.stButton > button:hover {
    background-color: #b71c1c !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)


# -------------------- SESSION EXPIRY CHECK --------------------
if "login_time" in st.session_state:
    if datetime.now() - st.session_state.login_time > timedelta(minutes=SESSION_TIMEOUT):
        st.session_state.clear()
        st.warning("Session expired. Please login again.")
        st.stop()


# -------------------- LOGIN PAGE --------------------
if "logged_in" not in st.session_state:

    st.title("HR Consultancy ATS Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        if user:
            st.session_state.logged_in = True
            st.session_state.login_time = datetime.now()
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Username or Password")

    st.stop()


# -------------------- MAIN DASHBOARD --------------------
st.title("HR Consultancy ATS Portal")

menu = st.sidebar.selectbox("Menu", ["Add Candidate", "View Candidates"])

# -------------------- LOGOUT --------------------
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.success("Logged out successfully")
    st.rerun()


# -------------------- ADD CANDIDATE --------------------
if menu == "Add Candidate":

    st.subheader("Add Candidate Details")

    name = st.text_input("Candidate Name")
    phone = st.text_input("Phone Number")
    email = st.text_input("Email")
    experience = st.selectbox("Experience", ["Fresher", "1-3 Years", "3-5 Years", "5+ Years"])
    status = st.selectbox("Status", ["Active", "Inactive"])

    if st.button("Save"):

        # Phone Validation
        if not re.fullmatch(r"\d{10}", phone):
            st.error("Phone number must be exactly 10 digits.")
            st.stop()

        c.execute("INSERT INTO candidates (name, phone, email, experience, status) VALUES (?, ?, ?, ?, ?)",
                  (name, phone, email, experience, status))
        conn.commit()

        st.success("Candidate Added Successfully")


# -------------------- VIEW CANDIDATES --------------------
if menu == "View Candidates":

    st.subheader("Candidate List")

    c.execute("SELECT * FROM candidates")
    data = c.fetchall()

    if data:
        for row in data:
            st.write(f"Name: {row[1]}")
            st.write(f"Phone: {row[2]}")
            st.write(f"Email: {row[3]}")
            st.write(f"Experience: {row[4]}")
            st.write(f"Status: {row[5]}")
            st.write("---")
    else:
        st.info("No Candidates Found")
