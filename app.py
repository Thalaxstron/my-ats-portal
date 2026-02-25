import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & DYNAMIC CSS ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# Adding the Red-Blue Gradient and Login Styling
st.markdown("""
    <style>
    /* Overall Background Linear Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Login Centering Logic */
    .main-login-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }

    /* Headings for Email & Password */
    .field-label {
        color: white !important;
        font-weight: bold !important;
        margin-bottom: 5px;
        margin-top: 15px;
        font-size: 14px;
        text-align: left;
    }

    /* Input Box - Blue Font */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* Blue Typing Font */
        font-weight: bold !important;
        height: 45px !important;
    }

    /* Professional White Text for Labels */
    .stCheckbox label { color: white !important; font-weight: bold; }
    .company-header { color: white; font-family: 'Arial Black'; font-size: 32px; text-align: center; }
    .ats-title { color: white; font-size: 22px; margin-bottom: 20px; text-align: center; }

    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database") 
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data") 
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 3. LOGIN PAGE ---
if not st.session_state.logged_in:
    _, col_m, _ = st.columns([1, 1.3, 1])
    
    with col_m:
        st.markdown('<div class="main-login-box">', unsafe_allow_html=True)
        st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
        st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
        
        # Headlines with Input Fields
        st.markdown('<p class="field-label">EMAIL ID</p>', unsafe_allow_html=True)
        u_mail = st.text_input("email", placeholder="Enter Business Email", label_visibility="collapsed")
        
        st.markdown('<p class="field-label">PASSWORD</p>', unsafe_allow_html=True)
        u_pass = st.text_input("pass", placeholder="Enter Password", type="password", label_visibility="collapsed")
        
        # Remember Me & Forget Password Row
        c_rem, c_for = st.columns(2)
        with c_rem:
            remember = st.checkbox("Remember Me")
        with c_for:
            st.markdown('<p style="text-align:right; color:white; font-size:12px; margin-top:5px;">Forgot Password?<br><b>Contact Admin</b></p>', unsafe_allow_html=True)

        if st.button("ACCESS DASHBOARD", use_container_width=True):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_row.iloc[0]['Username']
                st.rerun()
            else:
                st.error("Invalid Credentials")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 4. MODULE: DASHBOARD & NAVIGATION ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.selectbox("Menu", ["Dashboard & Tracking", "New Shortlist Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking System")
        raw_data = cand_sheet.get_all_records()
        if not raw_data:
            st.info("No candidates found.")
        else:
            all_df = pd.DataFrame(raw_data)
            
            # Filters
            f1, f2, f3 = st.columns(3)
            with f1: search_q = st.text_input("🔍 Search Name/Mobile")
            with f2: client_filter = st.selectbox("Filter by Client", ["All"] + sorted(all_df['Client Name'].unique().tolist()))
            with f3: hr_filter = st.selectbox("Filter by Recruiter", ["All"] + sorted(all_df['HR Name'].unique().tolist()))

            # Table View and Edit logic follows... (same as your stable yesterday code)
            # [Continuing with your existing tracking table logic here]
            st.dataframe(all_df) # Placeholder for your custom column logic

    elif menu == "New Shortlist Entry":
        # [Existing New Entry logic here]
        st.header("📝 Candidate Shortlist")
        # ... (rest of your entry code)
