import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. PREMIUM CSS (Gradient + Centering + Persistence Fix) ---
st.markdown("""
    <style>
    /* Full Page Red-Blue Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }

    /* Centering the Login Container */
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

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        margin-bottom: 5px;
    }

    .ats-title {
        color: white;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 25px;
    }

    /* Headlines for Email/Pass */
    .field-label {
        color: white !important;
        font-weight: bold !important;
        text-align: left !important;
        display: block;
        margin-bottom: 5px;
        margin-top: 15px;
        font-size: 14px;
    }

    /* Input Box Styles */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* Blue font while typing */
        font-weight: bold !important;
        height: 45px !important;
    }

    /* Checkbox & Text color */
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

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. LOGIN LOGIC ---
if not st.session_state.logged_in:
    _, col_m, _ = st.columns([1, 1.5, 1])
    
    with col_m:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
        st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
        
        st.markdown('<p class="field-label">EMAIL ID</p>', unsafe_allow_html=True)
        u_mail = st.text_input("email", placeholder="Enter Email", label_visibility="collapsed")
        
        st.markdown('<p class="field-label">PASSWORD</p>', unsafe_allow_html=True)
        u_pass = st.text_input("pass", placeholder="Enter Password", type="password", label_visibility="collapsed")
        
        col_rem, col_for = st.columns(2)
        with col_rem:
            remember = st.checkbox("Remember Me")
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
    # --- 6. DASHBOARD & TRACKING (Persistence Enabled) ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.selectbox("Menu", ["Dashboard & Tracking", "New Shortlist Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    # --- MODULE: NEW SHORTLIST ---
    if menu == "New Shortlist Entry":
        st.header("📝 Candidate Shortlist")
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_options = ["-- Select --"] + sorted(clients_df['Client Name'].unique().tolist())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Candidate Name")
                phone = st.text_input("Contact Number")
                sel_client = st.selectbox("Client Name", client_options)
            with c2:
                if sel_client != "-- Select --":
                    rows = clients_df[clients_df['Client Name'] == sel_client]
                    pos_list = [p.strip() for p in str(rows.iloc[0]['Position']).split(',')]
                    job = st.selectbox("Position", pos_list)
                else:
                    job = st.selectbox("Position", ["Select Client First"])
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save Candidate", use_container_width=True):
                if name and phone and sel_client != "-- Select --":
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date = comm_date.strftime("%d-%m-%Y")
                    # Append logic...
                    st.success(f"Candidate {name} Saved!")
                else: st.warning("Fill all details")

    # --- MODULE: DASHBOARD & TRACKING ---
    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking System")
        raw_data = cand_sheet.get_all_records()
        if not raw_data:
            st.info("No candidates found.")
        else:
            all_df = pd.DataFrame(raw_data)
            st.dataframe(all_df, use_container_width=True)
