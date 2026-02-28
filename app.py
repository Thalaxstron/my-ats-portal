import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI (Points 1, 2, 24, 70, 81) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Exact Image-based Alignment
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Header Styling (Point 24) */
    .fixed-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 999;
        padding: 20px 45px;
        height: 230px;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }

    /* Table Container - Excel Style (Point 25) */
    .excel-table-container {
        background-color: white;
        margin-top: 240px; 
        padding: 0px;
        border-radius: 0px;
    }

    /* Dark Blue Text in White Input Boxes (Point 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, input {
        background-color: white !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
    }

    .company-title { color: white; font-size: 32px; font-weight: bold; margin: 0; }
    .slogan { color: white; font-size: 20px; font-style: italic; margin-bottom: 10px; }
    .welcome-user { color: white; font-size: 22px; background: rgba(255,255,255,0.1); display: inline-block; padding: 5px 15px; border-radius: 5px; }
    .target-bar { 
        background-color: rgba(255,255,255,0.9); 
        color: #0d47a1; 
        padding: 8px 15px; 
        border-radius: 5px; 
        font-weight: bold; 
        margin-top: 10px;
        width: fit-content;
    }
    
    /* Excel Table Headers */
    .table-header {
        background-color: #0d47a1;
        color: white;
        padding: 10px;
        font-weight: bold;
        text-align: center;
        border: 0.5px solid white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def get_sheets_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = get_sheets_client()
sh = gc.open("ATS_Cloud_Database")
u_sheet = sh.worksheet("User_Master")
c_sheet = sh.worksheet("Client_Master")
d_sheet = sh.worksheet("ATS_Data")

# --- 3. LOGIC UTILS ---
def get_ref_id():
    ids = d_sheet.col_values(1)
    if len(ids) <= 1: return "E00001"
    return f"E{int(ids[-1][1:]) + 1:05d}"

def filter_by_status_age(df):
    # Points 62-64: Auto-Delete from view based on status age
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    
    # 7 Days for Shortlisted
    m1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    # 3 Days for Left/Not Joined
    m2 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    
    return df[~(m1 | m2) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. LOGIN LOGIC ---
if 'login' not in st.session_state: st.session_state.login = False

if not st.session_state.login:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    _, lbox, _ = st.columns([1, 1, 1])
    with lbox:
        with st.container(border=True):
            email = st.text_input("User ID")
            pw = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID'] == email) & (users['Password'].astype(str) == pw)]
                if not match.empty:
                    st.session_state.login = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Access Denied")
else:
    curr_u = st.session_state.u
    
    # --- 5. FIXED HEADER (Exactly as per your Image/Logic 81) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 55%;">
                    <div class="company-title">Takecare Manpower Services Pvt Ltd</div>
                    <div class="slogan">Successful HR Firm</div>
                    <div class="welcome-user">Welcome back, {curr_u['Username']}!</div>
                    <div class="target-bar">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Placing Action Buttons on the Right (Points 14-23)
    # Using columns for horizontal alignment within the fixed area
    top_spacer = st.container()
    with top_spacer:
        _, r_btns = st.columns([3, 1])
        with r_btns:
            st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
            if st.button("Log out 🚪", use_container_width=True):
                st.session_state.login = False
                st.rerun()
            
            search_key = st.text_input("Search (anything in this data sheet)", label_visibility="collapsed")
            
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                if curr_u['Role'] in ['ADMIN', 'TL']:
                    if st.button("Filter Symbol ⚙️"): pass
            with b_col2:
                # Point 29: New Shortlist Button
                if st.button("+ New Shortlist", type="primary"):
                    @st.dialog("➕ New Shortlist Entry")
                    def add_entry():
                        c_db = pd.DataFrame(c_sheet.get_all_records())
                        rid = get_ref_id()
                        col1, col2 = st.columns(2)
                        col1.text_input("Ref ID", rid, disabled=True)
                        col2.text_input("Date", datetime.now().strftime("%d-%m-%Y"), disabled=True)
                        name = col1.text_input("Candidate Name")
                        phone = col2.text_input("Contact Number")
                        client = col1.selectbox("Client", c_db['Client Name'].unique())
                        pos = col2.selectbox("Position", c_db[c_db['Client Name']==client]['Position'].unique())
                        comm_date = col1.date_input("Commitment Date")
                        if st.button("SUBMIT"):
                            d_sheet.append_row([rid, datetime.now().strftime("%d-%m-%Y"), name, phone, client, pos, comm_date.strftime("%d-%m-%Y"), "Shortlisted", curr_u['Username'], "", "", ""])
                            st.success("Added!"); time.sleep(1); st.rerun()
                    add_entry()

    # --- 6. EXCEL TRACKING DATA (Excel Font & Colour) ---
    st.markdown('<div class="excel-table-container">', unsafe_allow_html=True)
    
    raw_df = pd.DataFrame(d_sheet.get_all_records())
    
    # Filter by Role (66-68)
    if curr_u['Role'] == 'RECRUITER':
        df = raw_df[raw_df['HR Name'] == curr_u['Username']]
    elif curr_u['Role'] == 'TL':
        u_list = pd.DataFrame(u_sheet.get_all_records())
        team = u_list[u_list['Report_To'] == curr_u['Username']]['Username'].tolist()
        df = raw_df[raw_df['HR Name'].isin(team + [curr_u['Username']])]
    else: df = raw_df

    df = filter_by_status_age(df)
    if search_key:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_key, case=False)).any(axis=1)]

    # Table Header Rendering
    t_cols = st.columns([1, 1.5, 1.2, 1.5, 1.3, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboard", "SR Date", "HR Name", "Edit", "WA"]
    for col, l in zip(t_cols, labels):
        col.markdown(f'<div class="table-header">{l}</div>', unsafe_allow_html=True)

    # Table Data Rendering (Excel Style - White background, Dark Blue text)
    for i, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.3, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        
        # Point: Fixing the Time issue in Dates
        idate = str(row['Interview Date']).split(' ')[0]
        r_cols[4].write(idate)
        
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        
        # Edit Action (Points 47-60)
        if r_cols[9].button("📝", key=f"ed_{row['Reference_ID']}"):
            @st.dialog(f"Update: {row['Candidate Name']}")
            def edit_row(r):
                st.write(f"Ref: {r['Reference_ID']}")
                n_status = st.selectbox("Change Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
                n_date = st.date_input("Select Date")
                n_fb = st.text_input("Feedback (Max 20 chars)", max_chars=20)
                if st.button("SAVE"):
                    s_idx = raw_df[raw_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(s_idx, 8, n_status)
                    d_sheet.update_cell(s_idx, 12, n_fb)
                    
                    if n_status == "Interviewed": # Point 54: Update Int Date to Commitment Date column
                        d_sheet.update_cell(s_idx, 7, n_date.strftime("%d-%m-%Y"))
                    elif n_status == "Onboarded": # Point 61: SR Date logic
                        d_sheet.update_cell(s_idx, 10, n_date.strftime("%d-%m-%Y"))
                        c_data = pd.DataFrame(c_sheet.get_all_records())
                        srd = c_data[c_data['Client Name']==r['Client Name']]['SR Days'].values[0]
                        sr_val = (n_date + timedelta(days=int(srd))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(s_idx, 11, sr_val)
                    st.rerun()
            edit_row(row)

        # WhatsApp Invite (Point 46)
        if r_cols[10].button("📲", key=f"wa_{row['Reference_ID']}"):
            c_info = pd.DataFrame(c_sheet.get_all_records())
            info = c_info[c_info['Client Name'] == row['Client Name']].iloc[0]
            msg = f"Dear {row['Candidate Name']},\nInvite for Interview.\nRef: Takecare Manpower\nPosition: {row['Job Title']}\nDate: {idate}\nVenue: {info['Address']}\nMap: {info['Map Link']}\nContact: {info['Contact Person']}\nRegards, {curr_u['Username']}"
            url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{url}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
