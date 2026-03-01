import streamlit as st
import pandas as pd
import sqlite3
import re
from datetime import datetime, timedelta

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Takecare Manpower ATS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# CUSTOM CSS (LOGIN FIX)
# --------------------------------------------------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
}

/* Remove header */
[data-testid="stHeader"] {background: transparent;}

/* Input box white */
div[data-baseweb="input"] > div {
    background-color: white !important;
}

input {
    background-color: white !important;
    color: #0d47a1 !important;
    font-weight: 600 !important;
}

/* Checkbox */
div[data-baseweb="checkbox"] {
    background-color: white !important;
    padding: 4px;
    border-radius: 6px;
}

/* Login Button */
.stButton > button {
    background-color: #d32f2f !important;
    color: white !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    border: none !important;
}

.stButton > button:hover {
    background-color: #b71c1c !important;
    color: white !important;
}

/* Titles */
.main-title {
    color: white;
    text-align: center;
    font-size: 40px;
    font-weight: bold;
}

.sub-title {
    color: white;
    text-align: center;
    font-size: 22px;
    margin-bottom: 30px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------
conn = sqlite3.connect("ats.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    email TEXT,
    experience TEXT,
    date_added TEXT
)
""")
conn.commit()

# --------------------------------------------------
# SESSION TIMEOUT (30 mins)
# --------------------------------------------------
TIMEOUT = 30  # minutes

def check_session_timeout():
    if "login_time" in st.session_state:
        if datetime.now() - st.session_state.login_time > timedelta(minutes=TIMEOUT):
            st.session_state.logged_in = False
            st.session_state.clear()
            st.warning("Session expired. Please login again.")
            st.stop()

# --------------------------------------------------
# LOGIN SYSTEM
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown('<div class="main-title">TAKECARE MANPOWER</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">HR Consultancy ATS Portal</div>', unsafe_allow_html=True)

    email = st.text_input("Email ID")
    password = st.text_input("Password", type="password")
    remember = st.checkbox("Remember Me")

    if st.button("Login"):

        # Simple login (change credentials here)
        if email == "admin@takecare.com" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.login_time = datetime.now()
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid Credentials")

else:
    check_session_timeout()

    # --------------------------------------------------
    # DASHBOARD
    # --------------------------------------------------
    st.title("ATS Dashboard")

    if st.button("Logout"):
        st.session_state.clear()
        st.success("Logged out successfully")
        st.rerun()

    st.divider()

    # --------------------------------------------------
    # ADD CANDIDATE
    # --------------------------------------------------
    st.subheader("Add Candidate")

    name = st.text_input("Candidate Name")
    phone = st.text_input("Phone Number (10 digits)")
    email = st.text_input("Email ID")
    experience = st.selectbox("Experience", ["Fresher", "1 Year", "2 Years", "3+ Years"])

    if st.button("Save Candidate"):

        # Phone validation (10 digits only)
        if not re.fullmatch(r"\d{10}", phone):
            st.error("Phone number must be exactly 10 digits.")
        else:
            c.execute("""
                INSERT INTO candidates (name, phone, email, experience, date_added)
                VALUES (?, ?, ?, ?, ?)
            """, (name, phone, email, experience, datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            st.success("Candidate Saved Successfully")

    st.divider()

    # --------------------------------------------------
    # VIEW CANDIDATES
    # --------------------------------------------------
    st.subheader("Candidate List")

    df = pd.read_sql_query("SELECT * FROM candidates", conn)
    st.dataframe(df, use_container_width=True)

    st.download_button(
        "Download CSV Backup",
        df.to_csv(index=False),
        "backup.csv",
        "text/csv"
    )
