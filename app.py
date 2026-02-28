import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Master CSS for Exact Image-to-Code Alignment
st.markdown("""
    <style>
    /* Full Page Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Container for Header (Points 24, 81) */
    .header-wrapper {
        position: fixed; top: 0; left: 0; width: 100%;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 999; padding: 20px 45px 10px 45px;
        height: 200px; border-bottom: 2px solid white;
    }

    /* Table Container - Pure White for Excel Feel */
    .excel-container {
        background-color: white;
        margin-top: 210px; /* Space for fixed header */
        padding: 0px; border-radius: 0px; min-height: 80vh;
    }

    /* Fixed Table Header (Excel Blue) */
    .sticky-table-head {
        position: sticky; top: 200px; z-index: 998;
        background-color: #0d47a1; display: flex;
        border-bottom: 1px solid #ccc;
    }

    .header-cell {
        color: white; font-weight: bold; padding: 12px 5px;
        text-align: center; border: 0.5px solid white; font-size: 13px;
    }

    /* Data Row Styling */
    .data-row {
        display: flex; border-bottom: 0.5px solid #eee; background-color: white;
    }
    .data-cell {
        color: #0d47a1; padding: 10px 5px; text-align: center;
        font-size: 13px; font-weight: 500; border-right: 0.5px solid #f0f0f0;
    }

    /* White Inputs with Royal Blue Text (Point 70) */
    div[data-baseweb="input"], input, select {
        background-color: white !important; color: #0d47a1 !important;
        font-weight: bold !important; border: 1px solid #ccc !important;
    }

    .comp-title { color: white; font-size: 30px; font-weight: bold; margin: 0; }
    .slogan { color: white; font-size: 18px; font-style: italic; margin-bottom: 10px; }
    .target-pill { 
        background: white; color: #0d47a1; padding: 6px 12px; 
        border-radius: 5px; font-weight: bold; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE (Google Sheets) ---
@st.cache_resource
def connect_sheets():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

gc = connect_sheets()
sh = gc.open("ATS_Cloud_Database")
u_sheet, c_sheet, d_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

# --- 3. LOGIC UTILS ---
def generate_id():
    ids = d_sheet.col_values(1)
    return f"E{int(ids[-1][1:]) + 1:05d}" if len(ids) > 1 else "E00001"

def strip_time(val):
    return str(val).split(' ')[0] if val else ""

# --- 4. APP AUTHENTICATION ---
if 'user' not in st.session_state:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:100px;'>TAKECARE ATS LOGIN</h1>", unsafe_allow_html=True)
    _, lbox, _ = st.columns([1, 1, 1])
    with lbox:
        with st.container(border=True):
            e = st.text_input("User ID (Email)")
            p = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID']==e) & (users['Password'].astype(str)==p)]
                if not match.empty:
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
    st.stop()

# --- 5. DASHBOARD ---
u = st.session_state.user

# FIXED PAGE HEADER (Points 14-24, 81)
st.markdown(f"""
    <div class="header-wrapper">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div class="comp-title">Takecare Manpower Services Pvt Ltd</div>
                <div class="slogan">Successful HR Firm</div>
                <div style="color:white; font-size:18px; margin: 8px 0;">Welcome back, {u['Username']}!</div>
                <div class="target-pill">📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Right Side Action Buttons
_, r_btns = st.columns([3, 1])
with r_btns:
    st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
    if st.button("Logout 🚪", use_container_width=True): del st.session_state.user; st.rerun()
    search = st.text_input("Search", placeholder="Search Data...", label_visibility="collapsed")
    f_c, n_c = st.columns(2)
    f_c.button("Filter ⚙️", use_container_width=True)
    if n_col := n_c.button("+ New Shortlist", type="primary", use_container_width=True):
        @st.dialog("➕ Add New Entry")
        def add_entry():
            clients = pd.DataFrame(c_sheet.get_all_records())
            rid = generate_id()
            c1, c2 = st.columns(2)
            name = c1.text_input("Candidate Name")
            phone = c2.text_input("Contact Number")
            cl = c1.selectbox("Client", clients['Client Name'].unique())
            jt = c2.selectbox("Job Title", clients[clients['Client Name']==cl]['Position'].unique())
            dt = c1.date_input("Interview Date")
            if st.button("SAVE"):
                d_sheet.append_row([rid, datetime.now().strftime("%d-%m-%Y"), name, phone, cl, jt, dt.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", ""])
                st.rerun()
        add_entry()

# --- 6. EXCEL-STYLE TRACKING TABLE ---
st.markdown('<div class="excel-container">', unsafe_allow_html=True)

# Table Header Labels (Exact Mapping)
headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Joined", "SR Date", "Edit", "WA"]
widths = [10, 15, 12, 18, 12, 10, 10, 10, 5, 5]

# Render Sticky Headers
h_cols = st.columns(widths)
for col, h in zip(h_cols, headers):
    col.markdown(f'<div class="header-cell" style="background-color:#0d47a1;">{h}</div>', unsafe_allow_html=True)

# Fetch Data
df = pd.DataFrame(d_sheet.get_all_records())
if u['Role'] == 'RECRUITER': df = df[df['HR Name'] == u['Username']]
if search: df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

# Render Data Rows
for i, row in df.iterrows():
    r_cols = st.columns(widths)
    r_cols[0].markdown(f'<div class="data-cell">{row["Reference_ID"]}</div>', unsafe_allow_html=True)
    r_cols[1].markdown(f'<div class="data-cell">{row["Candidate Name"]}</div>', unsafe_allow_html=True)
    r_cols[2].markdown(f'<div class="data-cell">{row["Contact Number"]}</div>', unsafe_allow_html=True)
    r_cols[3].markdown(f'<div class="data-cell">{row["Job Title"]}</div>', unsafe_allow_html=True)
    r_cols[4].markdown(f'<div class="data-cell">{strip_time(row["Interview Date"])}</div>', unsafe_allow_html=True)
    r_cols[5].markdown(f'<div class="data-cell">{row["Status"]}</div>', unsafe_allow_html=True)
    r_cols[6].markdown(f'<div class="data-cell">{strip_time(row["Joining Date"])}</div>', unsafe_allow_html=True)
    r_cols[7].markdown(f'<div class="data-cell">{strip_time(row["SR Date"])}</div>', unsafe_allow_html=True)
    
    # Action Pencil
    if r_cols[8].button("📝", key=f"ed{i}"):
        @st.dialog("Update Status")
        def update_val(r):
            ns = st.selectbox("New Status", ["Interviewed", "Selected", "Onboarded", "Rejected", "Left"])
            nd = st.date_input("Action Date")
            if st.button("SAVE"):
                idx = df[df['Reference_ID']==r['Reference_ID']].index[0] + 2
                d_sheet.update_cell(idx, 8, ns)
                if ns == "Interviewed": d_sheet.update_cell(idx, 7, nd.strftime("%d-%m-%Y"))
                if ns == "Onboarded":
                    d_sheet.update_cell(idx, 10, nd.strftime("%d-%m-%Y"))
                    cm = pd.DataFrame(c_sheet.get_all_records())
                    days = cm[cm['Client Name']==r['Client Name']]['SR Days'].values[0]
                    sr_val = (nd + timedelta(days=int(days))).strftime("%d-%m-%Y")
                    d_sheet.update_cell(idx, 11, sr_val)
                st.rerun()
        update_val(row)

    # WA Button
    if r_cols[9].button("📲", key=f"wa{i}"):
        st.write("WA Link Triggered...") # Add actual URL logic here

st.markdown('</div>', unsafe_allow_html=True)
