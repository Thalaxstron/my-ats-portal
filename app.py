import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import base64

# --- 1. PAGE SETUP & SESSION ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 2. PREMIUM CSS (Winner Background & Glass Box) ---
st.markdown("""
    <style>
    /* Background Image - Successful Winner */
    .stApp {
        background: url("https://images.unsplash.com/photo-1531545514256-b1400bc00f31?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
        background-position: center;
    }
    
    /* Glass-morphism Login Box */
    .login-box {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.2);
        text-align: center;
        max-width: 450px;
        margin: auto;
    }

    .ats-title {
        color: #0d47a1;
        font-family: 'Arial Black', sans-serif;
        font-size: 28px;
        margin-top: 15px;
        margin-bottom: 25px;
    }

    /* Input Field Styling */
    .stTextInput input {
        border-radius: 10px !important;
        height: 48px !important;
        border: 1px solid #ccc !important;
        background-color: white !important;
        color: #333 !important;
    }
    
    /* Login Button Styling */
    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        width: 100%;
        margin-top: 20px;
        border: none;
    }

    /* Hide Streamlit elements for cleaner look */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

# --- 4. APP FLOW ---

if not st.session_state.logged_in:
    # --- MODERN LOGIN PAGE ---
    st.write("#")
    st.write("#")
    
    col1, col2, col3 = st.columns([1, 1.4, 1])
    
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        
        # Logo - Center Top inside the box
        # Using the Takecare logo neenga anupuna maari
        st.image("https://i.ibb.co/6R2M3rD/logo-original.png", use_container_width=True)
        
        st.markdown('<p class="ats-title">ATS LOGIN</p>', unsafe_allow_html=True)
        
        # Input Fields with placeholder and icons logic
        u_mail = st.text_input("👤 EMAIL ID", placeholder="Email ID", label_visibility="visible")
        u_pass = st.text_input("🔒 PASSWORD", placeholder="Password", type="password", label_visibility="visible")
        
        # Row for Remember Me & Forgot Password
        c1, c2 = st.columns(2)
        with c1:
            remember = st.checkbox("Remember Me")
        with c2:
            st.markdown("<p style='font-size:12px; color:#555; text-align:right; margin-top:10px;'>Forgot Password?<br><b style='color:#0d47a1;'>Contact Admin</b></p>", unsafe_allow_html=True)
        
        if st.button("LOGIN"):
            try:
                client = get_gsheet_client()
                sh = client.open("ATS_Cloud_Database") 
                user_sheet = sh.worksheet("User_Master")
                users_df = pd.DataFrame(user_sheet.get_all_records())
                
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.toast("Login Successful!", icon="🏆")
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            except Exception as e:
                st.error("Connection Error. Please check your internet.")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD LOGIC (STAYS PERSISTENT) ---
    st.sidebar.markdown(f"### 🎯 Recruiter: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Navigation", ["Dashboard & Tracking", "New Entry", "Logout"])
    
    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()
    
    # --- DASHBOARD CONTENT ---
    st.header("🔄 Candidate Tracking Dashboard")
    # Namma pazhaya solid tracking table logic inga varum
    st.write(f"Hello {st.session_state.user_full_name}, Dashboard is ready!")
