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

# --- 2. PREMIUM CUSTOM CSS ---
st.markdown("""
    <style>
    /* Gradient Background Blue-Red Mix */
    .stApp {
        background: linear-gradient(135deg, #0d47a1 10%, #d32f2f 100%);
        background-attachment: fixed;
    }
    
    /* Login Box (Rounded Rectangle) */
    .login-container {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 40px;
        border-radius: 25px;
        box-shadow: 0px 15px 35px rgba(0,0,0,0.4);
        text-align: center;
        width: 100%;
        max-width: 450px;
        margin: auto;
    }

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 32px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        text-align: center;
        margin-bottom: 20px;
    }

    .ats-title {
        color: #0d47a1;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 25px;
        text-transform: uppercase;
        border-bottom: 2px solid #0d47a1;
        display: inline-block;
        padding-bottom: 5px;
    }

    /* Input Box Styles - Font Colour Blue while typing */
    .stTextInput input {
        border-radius: 10px !important;
        background-color: white !important;
        border: 1px solid #ccc !important;
        color: #0d47a1 !important; /* Blue font colour while typing */
        font-weight: 500 !important;
    }

    /* Label Styling with Icons */
    label {
        color: #333 !important;
        font-weight: bold !important;
    }

    /* Login Button */
    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
        font-size: 18px;
        width: 100%;
        border: none;
        margin-top: 20px;
    }
    
    .stButton>button:hover {
        background: #b71c1c;
        color: white;
    }

    /* Hide Streamlit Header/Footer */
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
    st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
    
    # Login Box
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # ATS LOGIN Title inside the box
        st.markdown('<p class="ats-title">ATS LOGIN</p>', unsafe_allow_html=True)
        
        # Email ID field
        u_mail = st.text_input("👤 EMAIL ID", placeholder="Enter Email ID")
        
        # Password field with toggle
        u_pass = st.text_input("🔒 PASSWORD", placeholder="Enter Password", type="password")
        
        # Remember Me & Forget Password
        col_1, col_2 = st.columns(2)
        with col_1:
            remember = st.toggle("Remember Me")
        with col_2:
            st.markdown("<p style='font-size:12px; color:grey; text-align:right;'>Forgot Password?<br><b style='color:#0d47a1;'>Contact Admin</b></p>", unsafe_allow_html=True)
        
        if st.button("LOGIN SUCCESSFUL"):
            try:
                client = get_gsheet_client()
                sh = client.open("ATS_Cloud_Database") 
                user_sheet = sh.worksheet("User_Master")
                users_df = pd.DataFrame(user_sheet.get_all_records())
                
                # Validation Logic
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.success("Login Successful!")
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            except Exception as e:
                st.error("Database Connection Error. Contact Admin.")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 5. DASHBOARD AREA (Stays Persistent) ---
    st.sidebar.markdown(f"### 👤 Recruiter: {st.session_state.user_full_name}")
    
    menu = st.sidebar.radio("Navigation", ["Tracking Dashboard", "New Candidate Entry", "Logout"])
    
    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    # Dashboard Content
    if menu == "Tracking Dashboard":
        st.header("📊 Candidate Tracking Dashboard")
        st.write(f"Welcome back, {st.session_state.user_full_name}! Inga unga tracking table load aagum.")
        # Unga pazhaya Dashboard logic code-ah inga add pannikonga.
