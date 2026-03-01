import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials

# --- 1. THEME SETUP (Points 1, 2, 70) ---
st.set_page_config(page_title="Takecare ATS", layout="wide")

st.markdown("""
    <style>
    /* Full Page Red-Blue Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* White Box & Dark Blue Font for Inputs (Point 6, 7, 70) */
    div[data-baseweb="input"], input, select {
        background-color: white !important; 
        color: #0d47a1 !important; 
        font-weight: bold !important;
    }
    
    /* Center Company Name (Point 4, 5) */
    .center-text {
        text-align: center;
        color: white;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_db():
    # Use your streamlit secrets here
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

# --- 3. LOGIN PAGE LOGIC (Points 3-12) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='center-text'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center-text'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                rem = st.checkbox("Remember me") # Point 8
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                # Simple Validation check
                try:
                    gc = get_db()
                    u_sheet = gc.open("ATS_Cloud_Database").worksheet("User_Master")
                    users = pd.DataFrame(u_sheet.get_all_records())
                    
                    match = users[(users['Mail_ID'] == mail) & (users['Password'].astype(str) == pwd)]
                    
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.user = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Incorrect username or password") # Point 11
                except Exception as e:
                    st.error("Database Connection Error. Check Secrets.")
            
            st.info("Forgot password? Contact Admin") # Point 10

else:
    st.success(f"Welcome {st.session_state.user['Username']}! UI Step 1 Success.")
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()
