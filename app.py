import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. UI SETUP (Points 1, 2, 14-24, 70, 81) ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Full Gradient Background */
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    
    /* Fixed Header Area - 2.5cm approximately */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 210px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 15px 40px; border-bottom: 2px solid white;
    }

    /* ATS Table - Excel Style Container */
    .scroll-table { background-color: white; margin-top: 220px; border-radius: 0px; }

    /* Input Boxes: White with Royal Blue Font (#0d47a1) */
    div[data-baseweb="input"], input, select {
        background-color: white !important; color: #0d47a1 !important; font-weight: bold !important;
    }

    /* Column Header Styling */
    .col-header { 
        background-color: #0d47a1; color: white; padding: 10px; 
        text-align: center; border: 0.5px solid white; font-weight: bold; font-size: 14px;
    }
    
    /* Typography for Header */
    .comp-name { color: white; font-size: 28px; font-weight: bold; margin:0; }
    .slogan { color: white; font-size: 18px; font-style: italic; margin:0; }
    .welcome { color: white; font-size: 20px; margin-top: 10px; }
    .target { 
        background: white; color: #0d47a1; padding: 5px 10px; 
        border-radius: 5px; margin-top: 5px; display: inline-block; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_db_connection():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

gc = get_db_connection()
sh = gc.open("ATS_Cloud_Database")
u_sheet, c_sheet, d_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

# --- 3. UTILS (Points 35, 61-65) ---
def get_ref_id():
    ids = d_sheet.col_values(1)
    if len(ids) <= 1: return "E00001"
    return f"E{int(ids[-1][1:]) + 1:05d}"

def fix_date(d):
    if pd.isna(d) or d == "": return ""
    return str(d).split(' ')[0]

# --- 4. APP FLOW ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    # Login Page (Point 3-12)
    st.markdown("<h1 style='text-align:center; color:white;'>ATS PORTAL</h1>", unsafe_allow_html=True)
    _, lbox, _ = st.columns([1, 1, 1])
    with lbox:
        uid = st.text_input("User ID")
        ups = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            users = pd.DataFrame(u_sheet.get_all_records())
            match = users[(users['Mail_ID']==uid) & (users['Password'].astype(str)==ups)]
            if not match.empty:
                st.session_state.auth = True
                st.session_state.u = match.iloc[0].to_dict()
                st.rerun()
else:
    u = st.session_state.u
    
    # --- FIXED HEADER (Exact 81 Point Alignment) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 50%;">
                    <div class="comp-name">Takecare Manpower Services Pvt Ltd</div>
                    <div class="slogan">Successful HR Firm</div>
                    <div class="welcome">Welcome back, {u['Username']}!</div>
                    <div class="target">📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Right: 4 Action Buttons (Point 14-23)
    _, r_side = st.columns([3, 1])
    with r_side:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True): st.session_state.auth = False; st.rerun()
        search_q = st.text_input("Search", placeholder="Search Candidate...", label_visibility="collapsed")
        f_col, n_col = st.columns(2)
        with f_col:
            if u['Role'] in ['ADMIN', 'TL']: st.button("Filter ⚙️", use_container_width=True)
        with n_col:
            if st.button("+ New Shortlist", type="primary", use_container_width=True):
                @st.dialog("Add Entry")
                def add():
                    c_db = pd.DataFrame(c_sheet.get_all_records())
                    rid = get_ref_id()
                    c1, c2 = st.columns(2)
                    nm = c1.text_input("Candidate Name")
                    ph = c2.text_input("Contact Number")
                    cl = c1.selectbox("Client", c_db['Client Name'].unique())
                    jt = c2.selectbox("Job Title", c_db[c_db['Client Name']==cl]['Position'].unique())
                    dt = c1.date_input("Interview Date")
                    if st.button("SUBMIT"):
                        d_sheet.append_row([rid, datetime.now().strftime("%d-%m-%Y"), nm, ph, cl, jt, dt.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", ""])
                        st.rerun()
                add()

    # --- ATS TABLE (Excel Look & Feel) ---
    st.markdown('<div class="scroll-table">', unsafe_allow_html=True)
    df = pd.DataFrame(d_sheet.get_all_records())
    
    # Filter Logic (66-68)
    if u['Role'] == 'RECRUITER': df = df[df['HR Name'] == u['Username']]
    if search_q: df = df[df.astype(str).apply(lambda x: x.str.contains(search_q, case=False)).any(axis=1)]

    # Headers based on your specific list
    h_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8, 0.8])
    labels = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Joined", "SR Date", "Edit", "WA"]
    for col, l in zip(h_cols, labels): col.markdown(f'<div class="col-header">{l}</div>', unsafe_allow_html=True)

    for idx, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(fix_date(row['Interview Date']))
        r_cols[5].write(row['Status'])
        r_cols[6].write(fix_date(row['Joining Date']))
        r_cols[7].write(fix_date(row['SR Date']))
        
        # Point 47: Action Pencil
        if r_cols[8].button("📝", key=f"e{idx}"):
            @st.dialog("Update Status")
            def update(r):
                ns = st.selectbox("Status", ["Interviewed", "Selected", "Onboarded", "Rejected", "Left"])
                nd = st.date_input("Select Date")
                fb = st.text_input("Feedback", max_chars=20)
                if st.button("SAVE"):
                    s_idx = df[df['Reference_ID']==r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(s_idx, 8, ns) # Status update
                    d_sheet.update_cell(s_idx, 12, fb)
                    if ns == "Interviewed": d_sheet.update_cell(s_idx, 7, nd.strftime("%d-%m-%Y"))
                    if ns == "Onboarded":
                        d_sheet.update_cell(s_idx, 10, nd.strftime("%d-%m-%Y"))
                        cm = pd.DataFrame(c_sheet.get_all_records())
                        days = cm[cm['Client Name']==r['Client Name']]['SR Days'].values[0]
                        sr_val = (nd + timedelta(days=int(days))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(s_idx, 11, sr_val) # SR Date calculation
                    st.rerun()
            update(row)

        # Point 46: WA Invite
        if r_cols[9].button("📲", key=f"w{idx}"):
            c_info = pd.DataFrame(c_sheet.get_all_records())
            ci = c_info[c_info['Client Name']==row['Client Name']].iloc[0]
            msg = f"Dear {row['Candidate Name']},\nInvite for {row['Job Title']}.\nDate: {row['Interview Date']}\nVenue: {ci.get('Address','')}\nMap: {ci.get('Map Link','')}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'https://wa.me/91{row["Contact Number"]}?text={urllib.parse.quote(msg)}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
