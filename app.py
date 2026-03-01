import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials

# --- 1. THEME & FIXED LAYOUT (Points 1, 2, 24, 81) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Gradient Background (Point 2) */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }

    /* Fixed Top Header (Point 24, 81) */
    .header-wrapper {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
    }

    /* Fixed Table Column Headers (Point 27, 81) */
    .sticky-table-headers {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; display: flex; align-items: center;
        border-bottom: 1px solid #ccc;
    }

    .header-cell {
        color: white; font-weight: bold; text-align: center; font-size: 13px;
        border-right: 1px solid white; height: 100%; display: flex; align-items: center; justify-content: center;
    }

    /* Scrollable Data Area (Point 25, 26) */
    .data-content {
        margin-top: 260px; background-color: white; min-height: 500px; width: 100%;
    }

    /* White Inputs with Dark Blue Text (Point 6, 7, 70) */
    div[data-baseweb="input"], input {
        background-color: white !important; color: #0d47a1 !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AUTH CHECK ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

# --- LOGIN PAGE (Ithu already Step 1-la fix panniyachi) ---
if not st.session_state.auth:
    # ... (Login Code goes here)
    # Testing purpose-kaga ippo direct-ah dashboard kaatuvom
    if st.button("Temporary Login for Testing"):
        st.session_state.auth = True
        st.session_state.user = {"Username": "Thalax", "Role": "ADMIN"}
        st.rerun()
else:
    u = st.session_state.user

    # --- 3. PAGE HEADER (Points 14-23, 81) ---
    # Left side: Company Info | Right side: Control Buttons
    st.markdown(f"""
        <div class="header-wrapper">
            <div style="display: flex; justify-content: space-between;">
                <div style="color: white;">
                    <h2 style="margin:0;">Takecare Manpower Services Pvt Ltd</h2>
                    <p style="margin:0; font-style:italic;">Successful HR Firm</p>
                    <p style="margin:10px 0 0 0; font-size:18px;">Welcome back, {u['Username']}!</p>
                    <div style="background:white; color:#0d47a1; padding:5px 10px; border-radius:4px; font-weight:bold; margin-top:5px;">
                        📞 Target for Today: 80+ Calls / 3-5 Interview / 1+ Joining
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Placing Streamlit Buttons on the Right Side of Header (Point 20-23)
    _, r_side = st.columns([3, 1])
    with r_side:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        st.button("Logout 🚪", use_container_width=True) # Point 20
        st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed") # Point 22, 79
        c1, c2 = st.columns(2)
        c1.button("Filter ⚙️", use_container_width=True) # Point 21, 71
        c2.button("+ New Shortlist", type="primary", use_container_width=True) # Point 23, 29

    # --- 4. FIXED TABLE HEADERS (Point 27, 81) ---
    # Intha widths namma data table column sizes-oda match aaganum
    h_labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboarded", "SR Date", "HR Name", "Action", "WA Invite"]
    h_widths = [8, 12, 10, 15, 12, 10, 10, 8, 10, 5, 5] # Percentages
    
    cols_html = "".join([f'<div style="width:{w}%;" class="header-cell">{l}</div>' for l, w in zip(h_labels, h_widths)])
    st.markdown(f'<div class="sticky-table-headers">{cols_html}</div>', unsafe_allow_html=True)

    # --- 5. EMPTY DATA AREA (Point 25, 26) ---
    st.markdown('<div class="data-content">', unsafe_allow_html=True)
    
    st.write("### Data Table Innum Add Pannala...")
    st.info("Boss, ippo Framework ready! Mela header freeze aagi irukkum. Kela white area-la thaan namma data-vai fill panna porom.")
    
    st.markdown('</div>', unsafe_allow_html=True)
