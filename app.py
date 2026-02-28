import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI (Points 1, 2, 24, 70, 81) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Exact Alignment (Point 81) & Colors (Point 70)
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Header 2cm Feel (Points 14-24, 81) */
    .fixed-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000;
        padding: 15px 45px;
        height: 220px;
        border-bottom: 2px solid rgba(255,255,255,0.2);
    }

    /* Input Boxes: White background, Dark Blue text (Point 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, input {
        background-color: white !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }

    /* ATS Table Container (Point 25) */
    .ats-wrapper {
        background-color: white;
        margin-top: 235px; 
        border: 1px solid #ddd;
    }

    /* Excel Header Style */
    .excel-head {
        background-color: #0d47a1;
        color: white;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        border: 0.5px solid white;
        font-size: 13px;
    }

    .text-left-header { color: white; line-height: 1.2; }
    .company-name { font-size: 30px; font-weight: bold; }
    .slogan { font-size: 18px; font-style: italic; opacity: 0.9; }
    .target-box { 
        background-color: rgba(255,255,255,0.95); color: #0d47a1; 
        padding: 6px 12px; border-radius: 4px; 
        font-weight: bold; margin-top: 8px; display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
@st.cache_resource
def init_db():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = init_db()
sh = gc.open("ATS_Cloud_Database")
u_sheet = sh.worksheet("User_Master")
c_sheet = sh.worksheet("Client_Master")
d_sheet = sh.worksheet("ATS_Data")

# --- 3. HELPER LOGIC (Points 35, 61-65) ---
def generate_ref_id():
    ids = d_sheet.col_values(1)
    if len(ids) <= 1: return "E00001"
    return f"E{int(ids[-1][1:]) + 1:05d}"

def clean_time(val):
    if pd.isna(val) or val == "": return ""
    return str(val).split(' ')[0]

def apply_visibility_logic(df):
    # Points 62-64: Auto-Delete/Hide from view
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    # 7 Days rule for Shortlisted
    m1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    # 3 Days rule for Left/Not Joined
    m2 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    return df[~(m1 | m2)]

# --- 4. AUTHENTICATION (Points 3-12) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES</h1>", unsafe_allow_html=True)
    _, lcol, _ = st.columns([1, 1, 1])
    with lcol:
        with st.container(border=True):
            email = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID'] == email) & (users['Password'].astype(str) == pwd)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    u = st.session_state.user
    
    # --- 5. FIXED HEADER LAYOUT (Point 81 Alignment) ---
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between;">
                <div class="text-left-header">
                    <div class="company-name">Takecare Manpower Services Pvt Ltd</div>
                    <div class="slogan">Successful HR Firm</div>
                    <div style="font-size: 20px; margin-top:10px;">Welcome back, {u['Username']}!</div>
                    <div class="target-box">📞 Target: 80+ Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Right Side Controls Alignment (Points 14-23)
    _, r_side = st.columns([3, 1])
    with r_side:
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
        
        search_term = st.text_input("Search", label_visibility="collapsed", placeholder="Search Search...")
        
        b1, b2 = st.columns(2)
        with b1:
            if u['Role'] in ['ADMIN', 'TL']:
                if st.button("Filter ⚙️"):
                    @st.dialog("Advanced Filter")
                    def filter_dialog():
                        st.date_input("From Date")
                        st.date_input("To Date")
                        st.selectbox("Select Client", ["All"])
                        st.button("Apply Filter")
                    filter_dialog()
        with b2:
            if st.button("+ New Shortlist", type="primary"):
                @st.dialog("➕ Add New Candidate")
                def add_new():
                    c_list = pd.DataFrame(c_sheet.get_all_records())
                    rid = generate_ref_id()
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Candidate Name")
                    phone = c2.text_input("Contact Number")
                    client = c1.selectbox("Client Name", c_list['Client Name'].unique())
                    job = c2.selectbox("Job Title", c_list[c_list['Client Name']==client]['Position'].unique())
                    idate = c1.date_input("Commitment/Int Date")
                    if st.button("SUBMIT ENTRY", use_container_width=True):
                        # Headers: Reference_ID, Shortlisted Date, Candidate Name, Contact Number, Client Name, Job Title, Interview Date, Status, HR Name, Joining Date, SR Date, Feedback
                        d_sheet.append_row([rid, datetime.now().strftime("%d-%m-%Y"), name, phone, client, job, idate.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", ""])
                        st.success("Saved!"); time.sleep(1); st.rerun()
                add_new()

    # --- 6. DATA PROCESSING ---
    full_df = pd.DataFrame(d_sheet.get_all_records())
    
    # Role Access (Points 66-68)
    if u['Role'] == 'RECRUITER':
        disp_df = full_df[full_df['HR Name'] == u['Username']]
    elif u['Role'] == 'TL':
        u_master = pd.DataFrame(u_sheet.get_all_records())
        team = u_master[u_master['Report_To'] == u['Username']]['Username'].tolist()
        disp_df = full_df[full_df['HR Name'].isin(team + [u['Username']])]
    else:
        disp_df = full_df

    disp_df = apply_visibility_logic(disp_df)
    if search_term:
        disp_df = disp_df[disp_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)]

    # --- 7. ATS TABLE DISPLAY (Excel Look) ---
    st.markdown('<div class="ats-wrapper">', unsafe_allow_html=True)
    
    # Column Widths Alignment
    t_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
    headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Joined", "SR Date", "HR", "Edit", "WA"]
    for col, h in zip(t_cols, headers):
        col.markdown(f'<div class="excel-head">{h}</div>', unsafe_allow_html=True)

    for idx, row in disp_df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(clean_time(row['Interview Date']))
        r_cols[5].write(row['Status'])
        r_cols[6].write(clean_time(row['Joining Date']))
        r_cols[7].write(clean_time(row['SR Date']))
        r_cols[8].write(row['HR Name'])
        
        # Point 47: Edit Logic
        if r_cols[9].button("📝", key=f"ed_{idx}"):
            @st.dialog(f"Edit: {row['Candidate Name']}")
            def update_status(r):
                st.write(f"Ref ID: {r['Reference_ID']}")
                new_s = st.selectbox("Status", ["Interviewed", "Selected", "Onboarded", "Rejected", "Hold", "Left", "Not Joined"])
                new_d = st.date_input("Update Date")
                new_f = st.text_input("Feedback", max_chars=20)
                if st.button("UPDATE DATA"):
                    s_row = full_df[full_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(s_row, 8, new_s) # Status
                    d_sheet.update_cell(s_row, 12, new_f) # Feedback
                    
                    if new_s == "Interviewed":
                        d_sheet.update_cell(s_row, 7, new_d.strftime("%d-%m-%Y")) # Updates Int Date
                    elif new_s == "Onboarded":
                        d_sheet.update_cell(s_row, 10, new_d.strftime("%d-%m-%Y")) # Joined Date
                        # Point 61: SR Date Calculation
                        c_db = pd.DataFrame(c_sheet.get_all_records())
                        s_days = c_db[c_db['Client Name'] == r['Client Name']]['SR Days'].values[0]
                        sr_date = (new_d + timedelta(days=int(s_days))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(s_row, 11, sr_date)
                    st.rerun()
            update_status(row)

        # Point 44-46: WhatsApp Logic
        if r_cols[10].button("📲", key=f"wa_{idx}"):
            c_db = pd.DataFrame(c_sheet.get_all_records())
            c_info = c_db[c_db['Client Name'] == row['Client Name']].iloc[0]
            msg = (f"Dear {row['Candidate Name']},\nInvite for Interview.\n"
                   f"Company: {row['Client Name']}\nPosition: {row['Job Title']}\n"
                   f"Date: {clean_time(row['Interview Date'])}\nVenue: {c_info.get('Address','')}\n"
                   f"Map: {c_info.get('Map Link','')}\nRegards, {u['Username']}")
            wa_link = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_link}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
