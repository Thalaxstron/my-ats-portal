import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & RAINBOW UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# Custom CSS for Rainbow Background & Styling (Point 69 & 7-10)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(124deg, #ff2400, #e81d1d, #e8b71d, #e3e81d, #1de840, #1ddde8, #2b1de8, #dd00f3);
        background-size: 800% 800%;
        animation: rainbow 18s ease infinite;
    }
    @keyframes rainbow { 
        0%{background-position:0% 82%} 50%{background-position:100% 19%} 100%{background-position:0% 82%} 
    }
    /* White box, Dark Blue Text for Inputs (Point 7 & 8) */
    input, select, textarea { 
        background-color: white !important; 
        color: #00008b !important; 
        font-weight: bold !important; 
    }
    /* Login Button RED (Point 10) */
    div.stButton > button:first-child { 
        background-color: #FF0000 !important; 
        color: white !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (Point 13 - Neenga kudutha logic) ---
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        # Make sure "gcp_service_account" is set in your Streamlit Secrets
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

client = get_gsheet_client()
if client:
    try:
        sh = client.open("ATS_Cloud_Database") 
        user_sheet = sh.worksheet("User_Master")
        client_sheet = sh.worksheet("Client_Master")
        cand_sheet = sh.worksheet("ATS_Data") 
    except Exception as e:
        st.error(f"Sheet Access Error: {e}")
        st.stop()

# --- 3. HELPER FUNCTIONS (Point 30) ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:04d}" if valid_ids else "E0001"

# --- 4. SESSION MANAGEMENT (Point 62) ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. LOGIN PAGE (Points 2 to 13) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID (Mail ID based LOGIN)")
            u_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember me", value=False)
            
            if st.button("LOGIN", use_container_width=True):
                # Google Sheet-la irunthu User check panra logic
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                
                # Point 13: ID & Password check
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    # Point 12: Invalid Message
                    st.error("Incorrect username or password")
            
            st.markdown("<p style='color: white;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)

# --- 6. DASHBOARD (Point 14 to 68) ---
else:
    u_data = st.session_state.user_data
    
    # Point 15, 16, 20, 21: Header Section
    h_col1, h_col2 = st.columns([3, 1])
    with h_col1:
        st.markdown(f"<h1 style='font-size: 25px;'>Takecare Manpower Service Pvt Ltd</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 20px;'>Successful HR Firm</p>", unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"<p style='font-size: 18px;'>Welcome back, {u_data['Username']}!</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 18px;'>Target for Today: 80+ Calls / 3-5 Interview / 1+ Joining</p>", unsafe_allow_html=True)
        if st.button("Logout", key="logout_btn"): # Point 22
            st.session_state.logged_in = False
            st.rerun()

    # Point 17, 18, 19: Action Buttons
    col_btn, col_search = st.columns([4, 1])
    with col_btn:
        if st.button("+ New Shortlist", type="primary"):
            # Point 24: Pop up logic (Streamlit Dialog function use pannalam)
            pass 

    with col_search:
        search_query = st.text_input("🔍 Search", placeholder="Search rows...")

    # --- Frozen Header Mockup (Point 23 & 24) ---
    st.markdown("---")
    t_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 1, 0.5, 0.5])
    headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboard", "SR Date", "Edit", "WA"]
    for col, h in zip(t_cols, headers):
        col.markdown(f"**{h}**")
    
    # Scrollable area starts here (Neenga data loop panni output kudukkanum)
    st.info("Data rows will be displayed here based on ATS_Data sheet.")
