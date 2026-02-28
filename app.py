import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. UI SETUP (Points 1, 2, 70, 81) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    /* Gradient Background */
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    
    /* Fixed Header Styling (Exact Image Match) */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
    }

    /* Excel Table Background */
    .ats-wrapper { background-color: white; margin-top: 225px; padding: 0px; border-radius: 0px; }

    /* Sticky Excel Headers (Royal Blue) */
    .excel-header {
        position: sticky; top: 215px; z-index: 999;
        background-color: #0d47a1; color: white; display: flex;
        border-bottom: 1px solid #ccc;
    }
    .header-item {
        flex: 1; padding: 12px 5px; text-align: center;
        font-weight: bold; border: 0.5px solid white; font-size: 13px;
    }

    /* Input Box Styles - White with Dark Blue Text */
    div[data-baseweb="input"], input, select {
        background-color: white !important; color: #0d47a1 !important;
        font-weight: bold !important; border: 1px solid #ccc !important;
    }

    .comp-name { color: white; font-size: 30px; font-weight: bold; margin: 0; }
    .slogan { color: white; font-size: 18px; font-style: italic; margin-bottom: 5px; }
    .welcome-text { color: white; font-size: 19px; margin-top: 10px; }
    .target-box { 
        background: white; color: #0d47a1; padding: 6px 15px; 
        border-radius: 5px; font-weight: bold; display: inline-block; margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
@st.cache_resource
def get_gc():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = get_gc()
sh = gc.open("ATS_Cloud_Database")
u_sheet, c_sheet, d_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

# --- 3. UTILS ---
def generate_rid():
    ids = d_sheet.col_values(1)
    return f"E{int(ids[-1][1:]) + 1:04d}" if len(ids) > 1 else "E0001"

def date_only(d): # Points 41, 56, 73 - Clean Date Formatting
    if pd.isna(d) or d == "" or d == "None": return ""
    return str(d).split(' ')[0]

# --- 4. AUTH ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h1 style='text-align:center; color:white; margin-top:80px;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, lcol, _ = st.columns([1, 1, 1])
    with lcol:
        with st.container(border=True):
            uid = st.text_input("Email ID")
            upw = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID']==uid) & (users['Password'].astype(str)==upw)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.info("Forgot password? Contact Admin")
else:
    u = st.session_state.user

    # --- FIXED HEADER (Points 14-24, 81) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div class="comp-name">Takecare Manpower Service Pvt Ltd</div>
                    <div class="slogan">Successful HR Firm</div>
                    <div class="welcome-text">Welcome back, {u['Username']}!</div>
                    <div class="target-box">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Right Side Controls (Logout, Search, Filter, Add)
    _, r_side = st.columns([3, 1])
    with r_side:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True): st.session_state.auth = False; st.rerun()
        s_val = st.text_input("Search Candidate", placeholder="🔍 Search...", label_visibility="collapsed")
        
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if u['Role'] in ['ADMIN', 'TL']:
                if st.button("Filter ⚙️", use_container_width=True):
                    @st.dialog("Data Filter")
                    def fpop():
                        st.date_input("From Date"); st.date_input("To Date")
                        st.button("Search")
                    fpop()
        with b_col2:
            if st.button("+ New Shortlist", type="primary", use_container_width=True):
                @st.dialog("➕ New Shortlist Entry")
                def addpop():
                    rid = generate_rid()
                    clients = pd.DataFrame(c_sheet.get_all_records())
                    c1, c2 = st.columns(2)
                    nm = c1.text_input("Candidate Name")
                    ph = c2.text_input("Contact Number")
                    cl = c1.selectbox("Client Name", clients['Client Name'].unique())
                    jt = c2.selectbox("Job Title", clients[clients['Client Name']==cl]['Position'].unique())
                    dt = c1.date_input("Commitment Date")
                    if st.button("SUBMIT"):
                        d_sheet.append_row([rid, datetime.now().strftime("%d-%m-%Y"), nm, ph, cl, jt, dt.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", ""])
                        st.rerun()
                addpop()

    # --- ATS TRACKING TABLE ---
    st.markdown('<div class="ats-wrapper">', unsafe_allow_html=True)
    
    # Headers Mapping
    h_labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboarded", "SR Date", "HR Name", "Edit", "WA"]
    h_widths = [1, 1.5, 1.2, 1.8, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8, 0.8]
    cols = st.columns(h_widths)
    for c, l in zip(cols, h_labels): c.markdown(f'<div class="header-item">{l}</div>', unsafe_allow_html=True)

    # Data Processing
    df = pd.DataFrame(d_sheet.get_all_records())
    if u['Role'] == 'RECRUITER': df = df[df['HR Name'] == u['Username']]
    if s_val: df = df[df.astype(str).apply(lambda x: x.str.contains(s_val, case=False)).any(axis=1)]

    # Render Rows
    for i, row in df.iterrows():
        r_cols = st.columns(h_widths)
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(date_only(row['Interview Date']))
        r_cols[5].write(row['Status'])
        r_cols[6].write(date_only(row['Joining Date']))
        r_cols[7].write(date_only(row['SR Date']))
        r_cols[8].write(row['HR Name'])
        
        # Action Edit
        if r_cols[9].button("📝", key=f"e_{i}"):
            @st.dialog("Update Status")
            def edit_row(r):
                ns = st.selectbox("Status", ["Interviewed", "Selected", "Onboarded", "Rejected", "Left", "Project Success"])
                nd = st.date_input("Select Date")
                fb = st.text_input("Feedback (20 chars)", max_chars=20)
                if st.button("SAVE"):
                    idx = df[df['Reference_ID']==r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(idx, 8, ns)
                    d_sheet.update_cell(idx, 12, fb)
                    if ns == "Interviewed": d_sheet.update_cell(idx, 7, nd.strftime("%d-%m-%Y"))
                    if ns == "Onboarded":
                        d_sheet.update_cell(idx, 10, nd.strftime("%d-%m-%Y"))
                        cl_db = pd.DataFrame(c_sheet.get_all_records())
                        days = cl_db[cl_db['Client Name']==r['Client Name']]['SR Days'].values[0]
                        sr_d = (nd + timedelta(days=int(days))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(idx, 11, sr_d)
                    st.rerun()
            edit_row(row)

        # WA Invite (Points 44-46)
        if r_cols[10].button("📲", key=f"w_{i}"):
            c_db = pd.DataFrame(c_sheet.get_all_records())
            ci = c_db[c_db['Client Name']==row['Client Name']].iloc[0]
            msg = f"Dear {row['Candidate Name']},\nInvite for Interview.\nPosition: {row['Job Title']}\nDate: {row['Interview Date']}\nVenue: {ci['Address']}\nRegards, {u['Username']}"
            wa_link = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_link}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
