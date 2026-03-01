import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# Custom CSS (FIXED INPUT COLORS + RED LOGIN BUTTON)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }

    [data-testid="stHeader"] { background: transparent; }

    .main-title { color: white; text-align: center; font-size: 40px; font-weight: bold; margin-bottom: 0px; }
    .sub-title { color: white; text-align: center; font-size: 25px; margin-bottom: 20px; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }

    /* ---------- FIX INPUT BOX WHITE ---------- */
    div[data-baseweb="input"] > div {
        background-color: white !important;
    }

    input {
        background-color: white !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
    }

    textarea {
        background-color: white !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
    }

    /* ---------- FIX CHECKBOX WHITE ---------- */
    div[data-baseweb="checkbox"] {
        background-color: white !important;
        padding: 5px;
        border-radius: 6px;
    }

    /* ---------- RED LOGIN BUTTON (NO SIZE CHANGE) ---------- */
    .stButton > button {
        background-color: #d32f2f !important;
        color: white !important;
        border-radius: 8px;
        font-weight: bold;
        border: none;
    }

    .stButton > button:hover {
        background-color: #b71c1c !important;
        color: white !important;
    }

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
    st.error(f"Database Error: {e}"); st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# --- 5. LOGIN LOGIC ---
if not st.session_state.logged_in:

    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember Me")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")

            st.caption("Forgot password? Contact Admin")

else:
    # --- DASHBOARD (UNCHANGED LOGIC) ---
    u_data = st.session_state.user_data
    
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 2, 1.5, 0.5])
    with h_col1: st.subheader("TAKECARE")
    with h_col2: st.markdown(f"### Welcome back, {u_data['Username']}!")
    with h_col4: 
        if st.button("Log out"): 
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)
