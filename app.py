import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# Session Stability (Refresh pannaalum login pogaadhu)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. THEME UI (Winner Background & Glass-morphism) ---
st.markdown("""
    <style>
    .stApp {
        background: url("https://images.unsplash.com/photo-1551836022-d5d88e9218df?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    .login-box {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(12px);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0px 20px 40px rgba(0,0,0,0.3);
        text-align: center;
        max-width: 450px;
        margin: auto;
    }

    .ats-title {
        color: #0d47a1;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        margin-top: 15px;
    }

    /* Input Styling */
    .stTextInput input {
        border-radius: 12px !important;
        height: 50px !important;
        border: 1px solid #0d47a1 !important;
    }

    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 10px;
        height: 55px;
        font-weight: bold;
        font-size: 20px;
        width: 100%;
        border: none;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background: #1565c0;
        transform: scale(1.02);
    }

    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DB CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

# --- 4. APP FLOW ---
if not st.session_state.logged_in:
    st.write("#")
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        # Using placeholder for logo - replace with your actual URL
        st.image("https://i.ibb.co/6R2M3rD/logo-original.png", width=350)
        st.markdown('<p class="ats-title">ATS LOGIN</p>', unsafe_allow_html=True)
        
        u_mail = st.text_input("👤 EMAIL ID", placeholder="example@takecare.com")
        u_pass = st.text_input("🔒 PASSWORD", placeholder="••••••••", type="password")
        
        c1, c2 = st.columns(2)
        with c1: st.checkbox("Remember Me")
        with c2: st.markdown("<p style='font-size:12px; text-align:right;'>Forgot Password?<br><b style='color:#0d47a1;'>Contact Admin</b></p>", unsafe_allow_html=True)
        
        if st.button("LOGIN"):
            try:
                client = get_gsheet_client()
                sh = client.open("ATS_Cloud_Database") 
                users_df = pd.DataFrame(sh.worksheet("User_Master").get_all_records())
                
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.toast("Welcome Winner!", icon="🏆")
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_match.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            except:
                st.error("Database Connection Failed.")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD (Persistence Guaranteed) ---
    st.sidebar.markdown(f"### 🏆 Winner: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Navigate", ["Tracking Dashboard", "New Shortlist", "Logout"])
    
    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()
    
    if menu == "Tracking Dashboard":
        st.header("🔄 Real-time Tracking Dashboard")
        # Dashboard logic goes here...
