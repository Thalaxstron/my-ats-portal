import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials

# --- 1. PAGE CONFIG & MASTER CSS (Points 1, 2, 70, 81) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Full Page Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* White Box & Dark Blue Font for Inputs */
    div[data-baseweb="input"], input, select {
        background-color: white !important; 
        color: #0d47a1 !important; 
        font-weight: bold !important;
    }

    /* Fixed Header Styling (Point 24, 81) */
    .header-container {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
        display: flex; justify-content: space-between; align-items: flex-start;
    }
    
    /* Fixed Column Headers (Point 27) */
    .table-header-freeze {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; display: flex;
        border-bottom: 1px solid #ccc;
    }
    
    .h-cell {
        color: white; font-weight: bold; text-align: center; font-size: 13px;
        border-right: 1px solid white; display: flex; align-items: center; justify-content: center;
    }

    .center-text { text-align: center; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_db():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

# --- 3. DASHBOARD RENDERER (Step 3 Logic) ---
def render_dashboard(username):
    # HTML for Header
    st.markdown(f"""
        <div class="header-container">
            <div style="color: white; flex: 2;">
                <h2 style="margin:0;">Takecare Manpower Services Pvt Ltd</h2>
                <p style="margin:0; font-size:16px;">Successful HR Firm</p>
                <p style="margin:12px 0 0 0; font-size:18px;">Welcome back, {username}!</p>
                <div style="background:white; color:#0d47a1; padding:6px 12px; border-radius:4px; font-weight:bold; margin-top:8px; display:inline-block;">
                    📞 Target for Today: 80+ Calls / 3-5 Interview / 1+ Joining
                </div>
            </div>
            <div style="width: 250px;"></div> 
        </div>
    """, unsafe_allow_html=True)

    # Right Side Buttons (Streamlit Interactive)
    _, right_col = st.columns([3, 1])
    with right_col:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True, key="logout_btn"):
            st.session_state.auth = False
            st.rerun()
        st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed", key="search_bar")
        
        btn_row = st.columns(2)
        btn_row[0].button("Filter ⚙️", use_container_width=True, key="filter_btn")
        btn_row[1].button("+ New", type="primary", use_container_width=True, key="add_btn")

    # Fixed Table Headers
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboarded", "SR Date", "HR Name", "Action", "WA Invite"]
    widths = [8, 12, 10, 15, 12, 10, 10, 8, 10, 5, 5]
    
    h_html = "".join([f'<div style="width:{w}%;" class="h-cell">{l}</div>' for l, w in zip(labels, widths)])
    st.markdown(f'<div class="table-header-freeze">{h_html}</div>', unsafe_allow_html=True)

    # Content Area
    st.markdown('<div style="margin-top:270px; background:white; min-height:100vh; padding: 20px;">', unsafe_allow_html=True)
    st.write("### Data Table loading...")
    # Ingathaan namma adutha step-la actual data rows-ai poduvom
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. MAIN FLOW CONTROL ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    # LOGIN PAGE
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 class='center-text'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center-text'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1, 1])
    with col:
        with st.container(border=True):
            mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                try:
                    gc = get_db()
                    u_sh = gc.open("ATS_Cloud_Database").worksheet("User_Master")
                    users = pd.DataFrame(u_sh.get_all_records())
                    match = users[(users['Mail_ID'] == mail) & (users['Password'].astype(str) == pwd)]
                    
                    if not match.empty:
                        st.session_state.auth = True
                        st.session_state.user = match.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Incorrect username or password")
                except Exception as e:
                    st.error(f"Error: {e}")
            st.info("Forgot password? Contact Admin")
else:
    # DASHBOARD PAGE
    render_dashboard(st.session_state.user['Username'])
