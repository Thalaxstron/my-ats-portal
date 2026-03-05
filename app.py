import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP & ABSOLUTE UI FIX ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 1. Global Reset & Gradient Background */
    header {visibility: hidden;}
    .block-container {padding: 0px !important; max-width: 100% !important;}
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }

    /* 2. LOGIN PAGE ALIGNMENT (Point 3-10) */
    .login-wrapper {
        display: flex; flex-direction: column; align-items: center; justify-content: center; height: 80vh;
    }
    .login-box {
        background: rgba(255, 255, 255, 0.1); padding: 40px; border-radius: 15px;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
        width: 400px; text-align: center; color: white;
    }
    /* White Box Blue Text (Point 7-8) */
    .stTextInput input { background-color: white !important; color: #0d47a1 !important; font-weight: bold !important; border-radius: 8px !important; }
    
    /* 3. DASHBOARD HEADER - THE REAL FIX (Point 15-22) */
    .dashboard-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 210px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; border-bottom: 2px solid white; color: white; padding: 20px 40px;
    }
    .header-left { position: absolute; top: 20px; left: 40px; }
    .header-right { position: absolute; top: 20px; right: 40px; text-align: right; }
    
    .company-name { font-size: 25px; font-weight: bold; margin: 0; }
    .slogan { font-size: 20px; opacity: 0.9; margin: 0; }
    .welcome-text { font-size: 18px; margin-bottom: 5px; }
    .target-badge { 
        background: white; color: #d32f2f; padding: 8px 15px; 
        border-radius: 5px; font-weight: bold; font-size: 16px; display: inline-block;
    }

    /* 4. UTILITY CONTROLS (Search, Filter, New) */
    .utility-bar { position: absolute; top: 85px; left: 40px; display: flex; gap: 10px; align-items: center; }

    /* 5. STICKY TABLE HEADER (Point 23) */
    .sticky-bar {
        position: fixed; top: 210px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center;
    }

    /* 6. DATA AREA SCROLL */
    .scroll-content { margin-top: 255px; padding: 10px 20px; }
    .data-row { border-bottom: 1px solid rgba(255,255,255,0.1); color: white; text-align: center; padding: 10px 0; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE & SESSION (Maintain your existing logic) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN SCREEN (Exact as per Points 3-12) ---
if not st.session_state.logged_in:
    st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="login-box">
        <h2 style="margin-bottom:0;">TAKECARE MANPOWER SERVICES PVT LTD</h2>
        <h4 style="margin-top:5px; opacity:0.8;">ATS LOGIN</h4>
        <br>
    </div>
    """, unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        u_mail = st.text_input("Email ID")
        u_pass = st.text_input("Password", type="password")
        st.checkbox("Remember Me", key="rem")
        if st.button("LOGIN", use_container_width=True, type="primary"):
            # Dummy Logic for Success
            st.session_state.logged_in = True
            st.session_state.user_name = "Admin User"
            st.rerun()
        st.markdown("<p style='text-align:center; color:white; font-size:12px;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 4. SUCCESS LANDING PAGE (DASHBOARD) ---
    # Points 15-22: Professional Header Alignment
    st.markdown(f"""
    <div class="dashboard-header">
        <div class="header-left">
            <p class="company-name">Takecare Manpower Service Pvt Ltd</p>
            <p class="slogan">Successful HR Firm</p>
        </div>
        <div class="header-right">
            <p class="welcome-text">Welcome back, <b>{st.session_state.user_name}!</b></p>
            <div class="target-badge">
                Target: 80+ Calls / 3-5 Interview / 1+ Joining
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Search, Filter, New Buttons - Fixed Position
    with st.container():
        st.markdown('<div class="utility-bar">', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns([2, 1, 1.5, 5])
        with c1: st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
        with c2: st.button("Filter ⚙️")
        with c3: st.button("+ New Shortlist", type="primary")
        with c4: 
            if st.button("Logout 🚪"): 
                st.session_state.logged_in = False
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 5. STICKY TABLE HEADER (Point 23) ---
    # Absolute Alignment for 11 Columns
    cw = [0.7, 1.3, 1.0, 1.4, 1.2, 1.0, 1.0, 1.0, 1.0, 0.4, 0.4]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]

    st.markdown('<div class="sticky-bar">', unsafe_allow_html=True)
    h_cols = st.columns(cw)
    for col, lab in zip(h_cols, labels):
        col.markdown(f"<p style='color:white; font-weight:bold; text-align:center; margin:0; font-size:13px;'>{lab}</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 6. SCROLLABLE DATA ROWS (Frozen Logic) ---
    st.markdown('<div class="scroll-content">', unsafe_allow_html=True)
    
    # Inga dhaan neenga Google Sheet-la irundhu data loop pannanum
    for i in range(15): # Example Loop
        r_cols = st.columns(cw)
        r_cols[0].markdown("<div class='data-row'>E00001</div>", unsafe_allow_html=True)
        r_cols[1].markdown("<div class='data-row'>Candidate Name</div>", unsafe_allow_html=True)
        r_cols[2].markdown("<div class='data-row'>9876543210</div>", unsafe_allow_html=True)
        r_cols[3].markdown("<div class='data-row'>Recruiter Role</div>", unsafe_allow_html=True)
        r_cols[4].markdown("<div class='data-row'>01-03-2026</div>", unsafe_allow_html=True)
        r_cols[5].markdown("<div class='data-row'>Shortlisted</div>", unsafe_allow_html=True)
        r_cols[6].markdown("<div class='data-row'>-</div>", unsafe_allow_html=True)
        r_cols[7].markdown("<div class='data-row'>-</div>", unsafe_allow_html=True)
        r_cols[8].markdown("<div class='data-row'>HR Admin</div>", unsafe_allow_html=True)
        r_cols[9].button("📝", key=f"ed_{i}")
        r_cols[10].button("📲", key=f"wa_{i}")

    st.markdown('</div>', unsafe_allow_html=True)
