import streamlit as st
import pandas as pd

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Takecare ATS", layout="wide")

# --- 2. PREMIUM CSS FOR ALIGNMENT ---
st.markdown("""
    <style>
    /* Gradient Background */
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%); background-attachment: fixed; }
    
    /* Fixed Header Area */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 230px; 
        background: rgba(255, 255, 255, 0.95); z-index: 1000;
        padding: 10px 30px; border-bottom: 2px solid #0d47a1;
    }
    
    /* Data Scroll Area */
    .data-container { margin-top: 250px; padding: 20px; color: white; }
    
    /* Alignment of Elements */
    .header-top { display: flex; justify-content: space-between; align-items: center; }
    .company-title { font-size: 25px; font-weight: bold; color: #d32f2f; margin: 0; }
    .slogan { font-size: 20px; color: #0d47a1; margin: 0; }
    
    /* Inputs */
    .stTextInput input { border-radius: 5px; border: 1px solid #0d47a1; }
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIN PAGE (Point 2-12) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, c, _ = st.columns([1, 1, 1])
    with c:
        st.markdown("<h2 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center; color:white;'>ATS LOGIN</h4>", unsafe_allow_html=True)
        u = st.text_input("Email ID")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            # Logic here
            st.session_state.logged_in = True
            st.rerun()

# --- 4. DASHBOARD (Point 14-24) ---
else:
    # Frozern Header Section
    st.markdown("""
    <div class="fixed-header">
        <div class="header-top">
            <div>
                <p class="company-title">Takecare Manpower Service Pvt Ltd</p>
                <p class="slogan">Successful HR Firm</p>
            </div>
            <div style="text-align: right;">
                <p style="font-size: 18px; margin:0;">Welcome back, User!</p>
                <p style="font-size: 18px; margin:0;">Target: 80+ Calls / 3-5 Interview / 1+ Joining</p>
                <button onclick="window.location.reload();">Logout</button>
            </div>
        </div>
        <hr style="margin: 10px 0;">
        <div style="display: flex; gap: 10px;">
            <input type="text" placeholder="Search...">
            <button>Filter</button>
            <button style="background-color: #d32f2f; color: white;">+ New Shortlist</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scrollable Data Area
    st.markdown('<div class="data-container">', unsafe_allow_html=True)
    
    # 11 Column Headers Row
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Action", "WA"]
    cols = st.columns(len(headers))
    for i, h in enumerate(headers):
        cols[i].markdown(f"**{h}**")
        
    st.divider()
    # Data rows would come here...
    st.markdown('</div>', unsafe_allow_html=True)
