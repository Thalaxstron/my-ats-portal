import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & RAINBOW UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# Custom CSS for Rainbow Background and UI Logic
st.markdown("""
    <style>
    /* Rainbow Background Animation */
    .stApp {
        background: linear-gradient(124deg, #ff2400, #e81d1d, #e8b71d, #e3e81d, #1de840, #1ddde8, #2b1de8, #dd00f3, #dd00f3);
        background-size: 1800% 1800%;
        animation: rainbow 20s ease infinite;
    }
    @keyframes rainbow { 
        0%{background-position:0% 82%}
        50%{background-position:100% 19%}
        100%{background-position:0% 82%}
    }

    /* Input Box Styles */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: white !important;
        color: #000080 !important; /* Dark Blue Text */
        font-weight: bold;
    }

    /* Frozen Header Simulation */
    .frozen-top {
        position: sticky;
        top: 0;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        z-index: 1000;
        padding: 10px;
        border-radius: 10px;
    }

    /* Button Colors */
    div.stButton > button:first-child { background-color: #ff0000; color: white; } /* Login/Submit Red */
    .search-btn { background-color: #00BFFF !important; }
    .shortlist-btn { background-color: #28a745 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
# (Keep your existing gspread connection logic here)
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except:
        st.error("GCP Secrets not found!")
        return None

client = get_gsheet_client()
# Access your sheets: user_sheet, client_sheet, cand_sheet...

# --- 3. LOGIN PAGE (Points 2-12) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1, 1])
    with col_m:
        with st.form("login_form"):
            email = st.text_input("Email ID")
            passw = st.text_input("Password", type="password")
            remember = st.checkbox("Remember Me")
            submit = st.form_submit_button("LOGIN")
            
            if submit:
                # Add your user validation logic here
                if email == "admin@takecare.com" and passw == "admin123":
                    st.session_state.logged_in = True
                    st.session_state.user = {"name": "Admin User", "role": "ADMIN"}
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
        st.info("Forgot password? Contact Admin")

# --- 4. DASHBOARD (Points 14-69) ---
else:
    user = st.session_state.user
    
    # Header (Frozen Area)
    with st.container():
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"<h2 style='margin-bottom:0;'>Takecare Manpower Service Pvt Ltd</h2>", unsafe_allow_html=True)
            st.markdown("<p style='font-size:20px;'>Successful HR Firm</p>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"**Welcome back, {user['name']}!**")
            st.write("Target: 80+ Calls / 3-5 Interview / 1+ Joining")
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.rerun()

    # Action Row
    col_search, col_filter, col_new = st.columns([1, 1, 1])
    with col_search:
        search_query = st.text_input("🔍 Search", placeholder="Type to search...")
    with col_filter:
        if user['role'] in ['ADMIN', 'TL']:
            if st.button("Filter"):
                # Filter Dialog Logic
                pass
    with col_new:
        if st.button("+ New Shortlist", use_container_width=True):
            # Trigger Dialog (Logic point 24)
            st.rerun()

    # --- DATA TABLE ---
    # Fetch Data from Google Sheets here...
    st.markdown("---")
    # Table Header (Point 23)
    cols = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 1.5, 1, 1])
    headers = ["Ref ID", "Candidate Name", "Contact", "Job Title", "Int. Date", "Status", "SR Date", "Action", "WA"]
    for col, h in zip(cols, headers):
        col.write(f"**{h}**")

    # Scrollable Data Area
    # (Loop through your dataframe rows here)
    # logic for point 55-57 (Auto-deletion visual filter)
