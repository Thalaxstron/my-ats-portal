import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- 1. SET PAGE & CLEAN UI ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 1. Global Reset */
    header {visibility: hidden;}
    .stApp { background: linear-gradient(135deg, #d32f2f, #0d47a1); background-attachment: fixed; }
    .block-container {padding: 0px !important; max-width: 100% !important;}

    /* 2. Fixed Header (215px) */
    .header-box {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 40px; border-bottom: 2px solid white; color: white;
    }

    /* 3. Right Side Controls - Pinned to Top */
    .control-panel {
        position: fixed; top: 20px; right: 40px; z-index: 2000;
        width: 250px; display: flex; flex-direction: column; gap: 10px;
    }

    /* 4. Sticky Table Header (45px) */
    .sticky-header-bar {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; border-bottom: 1px solid white;
        display: flex; align-items: center; color: white; font-weight: bold;
    }

    /* 5. Content Area - Scrollable */
    .scroll-content { margin-top: 260px; padding: 0 10px; width: 100%; }

    /* Column Width Management */
    .col-id { width: 6%; } .col-name { width: 12%; } .col-mob { width: 10%; }
    .col-pos { width: 14%; } .col-date { width: 10%; } .col-status { width: 10%; }
    .col-join { width: 10%; } .col-sr { width: 10%; } .col-hr { width: 10%; }
    .col-act { width: 8%; }

    /* Data Row Styling */
    .data-row {
        display: flex; align-items: center; width: 100%; 
        border-bottom: 1px solid rgba(255,255,255,0.1); padding: 10px 0;
        color: white; text-align: center; font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. HEADER CONTENT ---
st.markdown(f"""
<div class="header-box">
    <h1 style="margin:0; font-size:32px;">Takecare Manpower Service Pvt Ltd</h1>
    <h4 style="margin:0; opacity:0.8;">Successful HR Firm</h4>
    <p style="margin:10px 0; font-size:18px;">Welcome back, User!</p>
    <div style="background:white; color:#d32f2f; padding:5px 15px; border-radius:5px; font-weight:bold; display:inline-block;">
        Target: 80+ Calls / 3-5 Interview / 1+ Joining
    </div>
</div>
""", unsafe_allow_html=True)

# --- 3. RIGHT SIDE CONTROLS ---
with st.container():
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    st.button("Logout 🚪")
    st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
    c1, c2 = st.columns(2)
    with c1: st.button("Filter ⚙️")
    with c2: st.button("+ New", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 4. STICKY TABLE HEADER ---
# Column width sync logic
w = [0.7, 1.2, 1.0, 1.4, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4, 0.4]
labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Joined", "SR Date", "HR Name", "Edit", "WA"]

st.markdown('<div class="sticky-header-bar">', unsafe_allow_html=True)
h_cols = st.columns(w)
for col, label in zip(h_cols, labels):
    col.markdown(f"<p style='text-align:center; margin:0;'>{label}</p>", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 5. DATA AREA (Add your Logic here) ---
st.markdown('<div class="scroll-content">', unsafe_allow_html=True)

# Dummy Data for Structure Testing
for i in range(1, 15):
    row_cols = st.columns(w)
    row_cols[0].markdown(f"<p style='text-align:center;'>E0000{i}</p>", unsafe_allow_html=True)
    row_cols[1].markdown(f"<p style='text-align:center;'>Candidate {i}</p>", unsafe_allow_html=True)
    row_cols[2].markdown(f"<p style='text-align:center;'>9876543210</p>", unsafe_allow_html=True)
    row_cols[3].markdown(f"<p style='text-align:center;'>Recruiter</p>", unsafe_allow_html=True)
    row_cols[4].markdown(f"<p style='text-align:center;'>01-03-2026</p>", unsafe_allow_html=True)
    row_cols[5].markdown(f"<p style='text-align:center;'>Selected</p>", unsafe_allow_html=True)
    row_cols[6].markdown(f"<p style='text-align:center;'>-</p>", unsafe_allow_html=True)
    row_cols[7].markdown(f"<p style='text-align:center;'>-</p>", unsafe_allow_html=True)
    row_cols[8].markdown(f"<p style='text-align:center;'>HR Admin</p>", unsafe_allow_html=True)
    
    # Action Buttons
    row_cols[9].button("📝", key=f"ed_{i}")
    row_cols[10].button("📲", key=f"wa_{i}")

st.markdown('</div>', unsafe_allow_html=True)
