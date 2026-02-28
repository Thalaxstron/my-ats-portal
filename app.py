import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & THEME (Points 1, 2, 24, 70) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    /* Fixed Header (Point 24) */
    .fixed-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: white;
        z-index: 1000;
        padding: 15px 30px;
        border-bottom: 3px solid #0d47a1;
    }
    /* White Boxes with Dark Blue Text (Point 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, .stTextInput input {
        background-color: white !important;
        color: #0d47a1 !important;
    }
    .main-title { color: #0d47a1; font-size: 26px; font-weight: bold; margin:0; }
    .target-bar { background-color: #e3f2fd; color: #0d47a1; padding: 10px; border-radius: 8px; font-weight: bold; border-left: 5px solid #0d47a1; margin-top:5px;}
    .ats-container { background-color: white; padding: 25px; border-radius: 15px; color: black; margin-top: 230px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
data_sheet = sh.worksheet("ATS_Data")

# --- 3. CORE LOGIC ---
def get_next_ref_id():
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    last_id = all_ids[-1]
    if last_id.startswith("E"):
        num = int(last_id[1:]) + 1
        return f"E{num:05d}"
    return "E00001"

def apply_auto_delete(df):
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df['Interview Date'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')
    m1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    m2 = (df['Status'].isin(['Interviewed', 'Selected', 'Hold', 'Rejected'])) & (df['Interview Date'] < today - timedelta(days=30))
    m3 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    return df[~(m1 | m2 | m3) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. SESSION & LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(user_sheet.get_all_records())
                match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")

# --- 5. MAIN DASHBOARD ---
else:
    user = st.session_state.user_data
    
    # FIXED HEADER (Points 14-24)
    st.markdown(f"""
        <div class="fixed-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div class="main-title">Takecare Manpower Services Pvt Ltd</div>
                    <div style="color:#555; font-style:italic; font-size:14px;">Successful HR Firm</div>
                    <div style="color:#0d47a1; font-size:18px; margin-top:5px;">Welcome back, <b>{user['Username']}</b>!</div>
                    <div class="target-bar">📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # ACTION ROW
    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns([2, 0.8, 1, 0.8])
    with t1: search_query = st.text_input("🔍 Search Candidate (Type and Enter)", key="s_box")
    with t4: 
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # POPUP: NEW SHORTLIST (Points 29-43)
    @st.dialog("➕ New Shortlist Entry")
    def add_candidate():
        c_df = pd.DataFrame(client_sheet.get_all_records())
        c1, c2 = st.columns(2)
        rid = get_next_ref_id()
        c1.text_input("Ref ID", value=rid, disabled=True)
        sdate = c2.text_input("Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
        name = c1.text_input("Candidate Name")
        phone = c2.text_input("Contact Number")
        cl_name = c1.selectbox("Client", options=c_df['Client Name'].unique())
        pos_list = c_df[c_df['Client Name'] == cl_name]['Position'].tolist()
        job = c2.selectbox("Position", options=pos_list)
        idate = c1.date_input("Commitment Date")
        if st.button("SUBMIT"):
            data_sheet.append_row([rid, sdate, name, phone, cl_name, job, idate.strftime("%d-%m-%Y"), "Shortlisted", user['Username'], "", "", ""])
            st.success("Entry Added!"); time.sleep(1); st.rerun()

    with t3:
        if st.button("+ New Shortlist", type="primary", use_container_width=True): add_candidate()

    # ATS TABLE CONTAINER
    st.markdown('<div class="ats-container">', unsafe_allow_html=True)
    raw_df = pd.DataFrame(data_sheet.get_all_records())
    
    # ROLE ACCESS (Points 66-68)
    if user['Role'] == 'RECRUITER':
        df = raw_df[raw_df['HR Name'] == user['Username']]
    elif user['Role'] == 'TL':
        u_df = pd.DataFrame(user_sheet.get_all_records())
        team = u_df[u_df['Report_To'] == user['Username']]['Username'].tolist()
        df = raw_df[raw_df['HR Name'].isin(team + [user['Username']])]
    else: df = raw_df

    df = apply_auto_delete(df)
    if search_query:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    # TABLE RENDER
    cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8, 0.8])
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "Edit", "WA"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")

    for idx, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        
        # EDIT BUTTON (Points 47-60)
        if r_cols[8].button("📝", key=f"e_{row['Reference_ID']}"):
            @st.dialog(f"Update: {row['Candidate Name']}")
            def edit_status(r):
                ns = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
                nd = st.date_input("Date")
                fb = st.text_input("Feedback", max_chars=20)
                if st.button("SAVE"):
                    sidx = raw_df[raw_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    data_sheet.update_cell(sidx, 8, ns)
                    data_sheet.update_cell(sidx, 12, fb)
                    if ns == "Onboarded":
                        cm = pd.DataFrame(client_sheet.get_all_records())
                        # Calculate SR Date (Point 61)
                        srd = cm[cm['Client Name'] == r['Client Name']]['SR Days'].values[0]
                        sr_val = (nd + timedelta(days=int(srd))).strftime("%d-%m-%Y")
                        data_sheet.update_cell(sidx, 10, nd.strftime("%d-%m-%Y"))
                        data_sheet.update_cell(sidx, 11, sr_val)
                    st.rerun()
            edit_status(row)

        # WHATSAPP BUTTON (Points 44-46)
        if r_cols[9].button("📲", key=f"w_{row['Reference_ID']}"):
            cm_df = pd.DataFrame(client_sheet.get_all_records())
            # Safer fetch to avoid KeyError
            client_data = cm_df[cm_df['Client Name'] == row['Client Name']]
            if not client_data.empty:
                c_info = client_data.iloc[0]
                # Ensure these headers match your Client_Master exactly
                addr = c_info.get('Address', 'Check Office')
                mlink = c_info.get('Map Link', 'N/A')
                cper = c_info.get('Contact Person', 'HR Manager')
                
                msg = f"Dear {row['Candidate Name']},\n\nInvite for Interview.\nRef: Takecare Manpower\nPosition: {row['Job Title']}\nDate: {row['Interview Date']}\nTime: 10.30 AM\nVenue: {addr}\nMap: {mlink}\nContact: {cper}\n\nRegards, {user['Username']}"
                encoded = urllib.parse.quote(msg)
                wa_url = f"https://wa.me/91{row['Contact Number']}?text={encoded}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_url}\'">', unsafe_allow_html=True)
            else:
                st.error("Client details not found in Client_Master!")

    st.markdown('</div>', unsafe_allow_html=True)
