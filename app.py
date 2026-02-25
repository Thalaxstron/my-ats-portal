import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. ADVANCED CSS (Login UI Polish) ---
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0d47a1 10%, #d32f2f 100%);
        background-attachment: fixed;
    }
    
    /* Centering the Login Content */
    .main-login-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-top: 80px;
    }

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 34px;
        margin-bottom: 5px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    .ats-title {
        color: white;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 30px;
        letter-spacing: 2px;
    }

    /* Input Box Styles */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* Blue font while typing */
        font-weight: bold !important;
        height: 50px !important;
        border: none !important;
        text-align: center; /* Center text inside box */
    }

    /* Button Styling */
    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        width: 100%;
        margin-top: 20px;
        border: 2px solid white;
    }
    
    .stButton>button:hover {
        background: white;
        color: #0d47a1;
    }

    /* Forget Password Text */
    .forget-pw {
        color: white;
        font-size: 13px;
        margin-top: 15px;
    }

    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

def get_next_ref_id(sheet):
    all_ids = sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(str(val)[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. APP INITIALIZATION ---
try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error("⚠️ Check Database Connection or Secrets.")
    st.stop()

# --- 5. APPLICATION FLOW ---

if not st.session_state.logged_in:
    # --- CENTERED LOGIN UI ---
    st.markdown('<div class="main-login-box">', unsafe_allow_html=True)
    st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
    st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
    
    # Using columns to restrict width and keep it centered
    _, col_m, _ = st.columns([1, 1.2, 1])
    
    with col_m:
        # Email ID field - No label, just placeholder
        u_mail = st.text_input("email", placeholder="EMAIL ID", label_visibility="collapsed")
        
        st.write(" ") # Spacer
        
        # Password field - No label, just placeholder
        u_pass = st.text_input("pass", placeholder="PASSWORD", type="password", label_visibility="collapsed")
        
        if st.button("LOGIN SUCCESSFUL"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_match.iloc[0]['Username']
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")
        
        # Forget Password Option
        st.markdown('<p class="forget-pw">Forget password? <br> <b>Contact Admin</b></p>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 6. DASHBOARD & ENTRIES (Yesterday's Stable Logic) ---
    st.sidebar.markdown(f"### 👤 Recruiter: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Main Menu", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    elif menu == "Dashboard & Tracking":
        st.header("📊 Real-time Candidate Tracking")
        data = cand_sheet.get_all_records()
        if data:
            df = pd.DataFrame(data)
            st.markdown("---")
            # Table logic follows... (Already implemented in previous versions)
            st.dataframe(df) # Simple view for quick check

    elif menu == "New Entry":
        st.header("📝 New Shortlist Entry")
        c_df = pd.DataFrame(client_sheet.get_all_records())
        with st.form("entry"):
            name = st.text_input("Candidate Name")
            phone = st.text_input("Mobile Number")
            client_c = st.selectbox("Client", c_df['Client Name'].unique())
            date_c = st.date_input("Interview Date")
            if st.form_submit_button("Save Entry"):
                if name and phone:
                    ref = get_next_ref_id(cand_sheet)
                    cand_sheet.append_row([ref, datetime.now().strftime("%d-%m-%Y"), name, phone, client_c, "", date_c.strftime("%d-%m-%Y"), "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    st.success(f"Saved! ID: {ref}")
