import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

# Session Persistence Logic
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. CSS FOR PROFESSIONAL LOGIN (LIGHT BLUE THEME) ---
st.markdown("""
    <style>
    /* Responsive Background */
    .stApp {
        background-color: #e3f2fd; /* Light Blue Background */
    }
    
    /* Login Box Container (Rounded Rectangle) */
    .login-container {
        background-color: white;
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.1);
        text-align: center;
        max-width: 450px;
        margin: auto;
    }

    .ats-title {
        color: #0d47a1;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 20px;
        font-family: 'Segoe UI', sans-serif;
    }

    /* Customizing Input Fields */
    div[data-baseweb="input"] {
        border-radius: 10px !important;
        background-color: white !important;
    }
    
    /* Hide Streamlit Header/Footer for cleaner look */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Mobile Responsive Adjustments */
    @media (max-width: 640px) {
        .login-container {
            width: 90%;
            padding: 20px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

# --- 4. APP LOGIC ---

if not st.session_state.logged_in:
    # --- CLEAN LOGIN PAGE ---
    
    # Logo at Top Center
    st.image("https://i.ibb.co/6R2M3rD/logo-original.png", width=300) # Inga unga logo direct link use pannalam
    
    col1, col2, col3 = st.columns([1, 2, 1]) # Centering the box
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<p class="ats-title">ATS LOGIN</p>', unsafe_allow_html=True)
        
        # Email Input with Icon
        u_mail = st.text_input("👤 Email ID", placeholder="EMAIL ID", label_visibility="collapsed")
        
        # Password Input with Toggle
        u_pass = st.text_input("🔒 Password", placeholder="PASSWORD", type="password", label_visibility="collapsed")
        
        # Remember Me Toggle & Forget Password
        c1, c2 = st.columns(2)
        with c1:
            remember = st.toggle("Remember Me")
        with c2:
            st.markdown("<p style='color:grey; font-size:12px; margin-top:5px;'>Forgot Password? <br><b>Contact Admin</b></p>", unsafe_allow_html=True)
        
        if st.button("LOGIN SUCCESSFUL"):
            try:
                client = get_gsheet_client()
                sh = client.open("ATS_Cloud_Database") 
                user_sheet = sh.worksheet("User_Master")
                users_df = pd.DataFrame(user_sheet.get_all_records())
                
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.success("Login Successful!")
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            except Exception as e:
                st.error("Database Connection Error")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD LOGIC (As requested, keeping it same) ---
    st.sidebar.title(f"Welcome {st.session_state.user_full_name}")
    # ... Neenga nethu panna New Entry and Tracking logic inga continue aagum ...
    
    menu = st.sidebar.radio("Menu", ["Dashboard & Tracking", "New Entry", "Logout"])
    
    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()
        
    # [Unga Tracking and New Entry Logic Blocks inga irukkum]
    st.header("🔄 Candidate Tracking Dashboard")
    st.info("Unga Dashboard data inga load aagum Boss!")
