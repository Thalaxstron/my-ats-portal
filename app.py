import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

# --- 2. CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    [data-testid="stHeader"] { background: transparent; }
    input { color: #0d47a1 !important; font-weight: bold !important; }
    div.stDialog > div:first-child { background-color: white !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database") 
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data") 
except Exception as e:
    st.error(f"Database Connection Error: {e}"); st.stop()

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = None

# --- 5. REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 6. POPUP: NEW SHORTLIST ENTRY ---
@st.dialog("➕ Add New Candidate Shortlist")
def new_entry_popup():
    clients_master_df = pd.DataFrame(client_sheet.get_all_records())
    
    ref_id = get_next_ref_id()
    st.markdown(f"**Reference ID:** `{ref_id}`")
    
    c_name = st.text_input("Candidate Name")
    c_phone = st.text_input("Contact Number (WhatsApp)")
    
    client_names = sorted(clients_master_df['Client Name'].unique().tolist())
    sel_client = st.selectbox("Select Client", ["-- Select --"] + client_names)
    
    # Position logic for multiple entries
    job_list = []
    if sel_client != "-- Select --":
        job_list = clients_master_df[clients_master_df['Client Name'] == sel_client]['Position'].unique().tolist()
    
    sel_job = st.selectbox("Position", job_list if job_list else ["Select Client First"])
    comm_date = st.date_input("Interview Commitment Date", datetime.now())
    feedback = st.text_area("Feedback")
    send_wa = st.checkbox("Send WhatsApp Invite Link", value=True)
    
    if st.button("SUBMIT & SAVE"):
        if c_name and c_phone and sel_client != "-- Select --":
            today = datetime.now().strftime("%d-%m-%Y")
            c_date_str = comm_date.strftime("%d-%m-%Y")
            hr_name = st.session_state.user_data['Username']
            
            # 1. Save to Sheet
            cand_sheet.append_row([ref_id, today, c_name, c_phone, sel_client, sel_job, c_date_str, "Shortlisted", hr_name, "", "", feedback])
            
            # 2. WhatsApp Logic
            if send_wa:
                c_info = clients_master_df[(clients_master_df['Client Name'] == sel_client) & (clients_master_df['Position'] == sel_job)].iloc[0]
                msg = f"Dear {c_name},\nCongratulations! Direct Interview Invite.\n\nPosition: {sel_job}\nRef: Takecare Manpower\nDate: {c_date_str}\nTime: 10.30 AM\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nRegards,\n{hr_name}\nTakecare HR Team"
                wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank">📲 Click Here to Send WhatsApp</a>', unsafe_allow_html=True)
            
            st.success("Successfully Saved!")
            st.rerun()

# --- 7. MAIN LOGIC ---
if not st.session_state.logged_in:
    # LOGIN SCREEN
    st.markdown("<h2 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.5, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip() # Header spaces fix
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")

else:
    # DASHBOARD
    u_data = st.session_state.user_data
    st.sidebar.markdown(f"### 👤 {u_data['Username']}")
    st.sidebar.info(f"Role: {u_data['Role']}")
    
    if st.sidebar.button("➕ NEW SHORTLIST", use_container_width=True): new_entry_popup()
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

    # --- DATA FILTERING BY ROLE ---
    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()
        
        # Admin sees all, TL sees team, Recruiter sees own
        if u_data['Role'] == "RECRUITER":
            df = df[df['HR Name'] == u_data['Username']]
        elif u_data['Role'] == "TL":
            users_df = pd.DataFrame(user_sheet.get_all_records())
            team = users_df[users_df['Report_To'] == u_data['Username']]['Username'].tolist()
            df = df[df['HR Name'].isin(team + [u_data['Username']])]

        # --- AUTO DELETE LOGIC (Visual Filter Only) ---
        df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        now = datetime.now()
        
        # Remove Shortlisted > 7 days, Interviewed/Selected > 30 days
        df = df[~((df['Status'] == "Shortlisted") & (df['Shortlisted Date'] < now - timedelta(days=7)))]
        # Add other status deletion logic as needed...

        st.header("Candidate Tracking")
        search = st.text_input("🔍 Search Name or Number")
        if search:
            df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]

        # Display Table
        cols = st.columns([1, 2, 1.5, 1.5, 1.5, 1, 0.8])
        for col, h in zip(cols, ["Ref ID", "Candidate", "Client", "Int. Date", "Status", "HR", "Edit"]): col.write(f"**{h}**")

        for idx, row in df.iterrows():
            c = st.columns([1, 2, 1.5, 1.5, 1.5, 1, 0.8])
            c[0].write(row['Reference_ID'])
            c[1].write(row['Candidate Name'])
            c[2].write(row['Client Name'])
            c[3].write(row['Interview Date'])
            c[4].write(row['Status'])
            c[5].write(row['HR Name'])
            if c[6].button("📝", key=f"edit_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # --- EDIT ACTION SIDEBAR ---
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.markdown("---")
            st.subheader(f"Update: {st.session_state.edit_id}")
            # ... (Edit logic here: Interview Date update, Onboarded logic, SR Date calculation)
            # (Adhe pazhaya SR Date calculation logic-ai inga apply panni sheet update panlan)
            if st.button("Close Edit"): del st.session_state.edit_id; st.rerun()
