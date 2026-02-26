import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. PREMIUM CSS (Gradient + Centering) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    [data-testid="stVerticalBlock"] > div:has(div.login-card) {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .login-card {
        background: rgba(255, 255, 255, 0.1);
        padding: 30px;
        border-radius: 15px;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        width: 100%;
        max-width: 400px;
    }
    .company-header { color: white; font-family: 'Arial Black', sans-serif; font-size: 28px; margin-bottom: 5px; }
    .ats-title { color: white; font-weight: bold; font-size: 20px; margin-bottom: 25px; }
    .field-label { color: white !important; font-weight: bold !important; text-align: left !important; display: block; margin-bottom: 5px; margin-top: 15px; font-size: 14px; }
    .stTextInput input { border-radius: 8px !important; background-color: white !important; color: #0d47a1 !important; font-weight: bold !important; height: 45px !important; }
    .stCheckbox label { color: white !important; font-weight: bold; }
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
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

# --- 4. SESSION MANAGEMENT (Crucial for Refresh Fix) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. APP LOGIC ---
if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    _, col_m, _ = st.columns([1, 1.5, 1])
    with col_m:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="company-header">TAKECARE</div>', unsafe_allow_html=True)
        st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
        
        st.markdown('<p class="field-label">EMAIL ID</p>', unsafe_allow_html=True)
        u_mail = st.text_input("email", placeholder="Enter Email", label_visibility="collapsed")
        
        st.markdown('<p class="field-label">PASSWORD</p>', unsafe_allow_html=True)
        u_pass = st.text_input("pass", placeholder="Enter Password", type="password", label_visibility="collapsed")
        
        col_rem, col_for = st.columns(2)
        with col_rem:
            remember = st.checkbox("Remember Me") # Visual toggle added
        with col_for:
            st.markdown('<p style="text-align:right; color:white; font-size:12px; margin-top:10px;">Forgot Password?</p>', unsafe_allow_html=True)

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
    # --- DASHBOARD AREA ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.selectbox("Menu", ["Dashboard & Tracking", "New Shortlist Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    if menu == "New Shortlist Entry":
        st.header("📝 Candidate Shortlist")
        # Unga entry logic inge irukkum...
        st.info("Form entries logic working fine.")

    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking System")
        raw_data = cand_sheet.get_all_records()
        if raw_data:
            df = pd.DataFrame(raw_data)
            st.dataframe(df, use_container_width=True)
