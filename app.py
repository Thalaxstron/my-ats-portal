import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="centered")

# Session Stability
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. ADVANCED CSS (Blue-Red Gradient & Responsive Design) ---
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #0d47a1 0%, #b71c1c 100%);
        background-attachment: fixed;
    }
    
    /* Login Box Container */
    .login-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
        text-align: center;
        width: 100%;
        max-width: 400px;
        margin: auto;
    }

    .company-name {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        text-align: center;
        margin-bottom: 10px;
    }

    .ats-title {
        color: #333;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 20px;
        letter-spacing: 1px;
    }

    /* Input Box Styles */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        border: 1px solid #ccc !important;
        padding-left: 35px !important;
    }

    /* Button Styling */
    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 8px;
        height: 45px;
        font-weight: bold;
        width: 100%;
        border: none;
    }
    
    .stButton>button:hover {
        background: #b71c1c;
        color: white;
    }

    /* Remove Streamlit branding */
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

# --- 4. LOGIN LOGIC ---
if not st.session_state.logged_in:
    # Company Name at Top Center
    st.markdown('<div class="company-name">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
    
    # Login Box
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<p class="ats-title">ATS LOGIN</p>', unsafe_allow_html=True)
        
        # Email ID with Icon Label
        u_mail = st.text_input("👤 EMAIL ID", placeholder="EMAIL ID", label_visibility="visible")
        
        # Password with Icon and Toggle
        u_pass = st.text_input("🔒 PASSWORD", placeholder="PASSWORD", type="password", label_visibility="visible")
        
        # Remember Me and Forget Password
        col_a, col_b = st.columns(2)
        with col_a:
            remember = st.toggle("Remember Me")
        with col_b:
            st.markdown("<p style='font-size:12px; color:grey; margin-top:5px;'>Forgot Password?<br><b>Contact Admin</b></p>", unsafe_allow_html=True)
        
        if st.button("LOGIN SUCCESSFUL"):
            try:
                client = get_gsheet_client()
                sh = client.open("ATS_Cloud_Database") 
                users_df = pd.DataFrame(sh.worksheet("User_Master").get_all_records())
                
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.success("Login Successful!")
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_match.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            except:
                st.error("Database connection failed.")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD LOGIC (STAYS PERSISTENT) ---
    st.sidebar.write(f"Logged in as: **{st.session_state.user_full_name}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.header("🏆 Candidate Tracking Dashboard")
    st.write("Welcome to the internal system.")
