import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

# --- 2. PREMIUM CSS (Red-Blue Gradient) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    header, footer {visibility: hidden;}
    .stButton>button { border-radius: 8px; font-weight: bold; }
    [data-testid="stHeader"] { background: transparent; }
    div.stDialog > div:first-child { background-color: white !important; border-radius: 15px; }
    label { color: white !important; }
    .stMarkdown p { color: white; }
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
    st.error(f"Database Error: {e}"); st.stop()

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = {}

# --- 5. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 6. POPUP: NEW SHORTLIST ENTRY ---
@st.dialog("➕ New Shortlist Entry")
def new_entry_popup():
    clients_master_df = pd.DataFrame(client_sheet.get_all_records())
    
    ref_id = get_next_ref_id()
    st.info(f"Reference ID: {ref_id}")
    
    c_name = st.text_input("Candidate Name")
    c_phone = st.text_input("Contact Number")
    
    # Client Selection
    client_names = sorted(clients_master_df['Client Name'].unique().tolist())
    sel_client = st.selectbox("Client Name", ["-- Select --"] + client_names)
    
    # Position Selection (Logic to fetch multiple positions for same client)
    job_list = []
    if sel_client != "-- Select --":
        client_rows = clients_master_df[clients_master_df['Client Name'] == sel_client]
        job_list = client_rows['Position'].tolist()
    
    sel_job = st.selectbox("Position", job_list if job_list else ["Select Client First"])
    comm_date = st.date_input("Commitment Date (Interview Date)", datetime.now())
    feedback = st.text_area("Feedback (Optional)")
    send_wa = st.checkbox("✅ Tick to Send WhatsApp Invite", value=True)
    
    if st.button("SUBMIT SHORTLIST", use_container_width=True):
        if c_name and c_phone and sel_client != "-- Select --":
            today = datetime.now().strftime("%d-%m-%Y")
            c_date_str = comm_date.strftime("%d-%m-%Y")
            hr_name = st.session_state.user_data['Username']
            
            # Save to Sheet
            new_row = [ref_id, today, c_name, c_phone, sel_client, sel_job, c_date_str, "Shortlisted", hr_name, "", "", feedback]
            cand_sheet.append_row(new_row)
            
            if send_wa:
                # Get Client Details for Invite
                c_info = clients_master_df[(clients_master_df['Client Name'] == sel_client) & (clients_master_df['Position'] == sel_job)].iloc[0]
                msg = f"Dear {c_name},\n\nCongratulations! Invite for Interview.\nRef: Takecare Manpower\nPosition: {sel_job}\nDate: {c_date_str}\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nRegards,\n{hr_name}\nTakecare HR Team"
                wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank">📲 Open WhatsApp to Send Invite</a>', unsafe_allow_html=True)
            
            st.success(f"Entry Saved: {ref_id}")
            if st.button("Close"): st.rerun()
        else:
            st.error("Please fill mandatory fields!")

# --- 7. LOGIN LOGIC ---
if not st.session_state.logged_in:
    _, col_m, _ = st.columns([1, 2, 1])
    with col_m:
        st.markdown("<h2 style='text-align:center;'>TAKECARE MANPOWER SERVICES PVT LTD</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align:center;'>ATS LOGIN</h4>", unsafe_allow_html=True)
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember Me")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 8. DASHBOARD LOGIC ---
else:
    u_role = st.session_state.user_data['Role']
    u_name = st.session_state.user_data['Username']

    st.sidebar.markdown(f"### 👤 {u_name} ({u_role})")
    if st.sidebar.button("➕ NEW SHORTLIST", use_container_width=True):
        new_entry_popup()
    
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

    # Data Display & Filtering
    st.header("Candidate Tracking System")
    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # --- ROLE BASED ACCESS LOGIC ---
        if u_role == "RECRUITER":
            df = df[df['HR Name'] == u_name]
        elif u_role == "TL":
            # Show entries of recruiters reporting to this TL
            users_df = pd.DataFrame(user_sheet.get_all_records())
            team_members = users_df[users_df['Report_To'] == u_name]['Username'].tolist()
            df = df[df['HR Name'].isin(team_members + [u_name])]
        
        # --- AUTO-DELETE (HIDDEN) LOGIC ---
        df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        today_dt = datetime.now()
        # Filter out 7+ days Shortlisted
        df = df[~((df['Status'] == "Shortlisted") & (df['Shortlisted Date'] < today_dt - timedelta(days=7)))]

        # Search box
        search = st.text_input("🔍 Search Candidate Name / Mobile")
        if search:
            df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]

        # Display Table
        cols = st.columns([1, 2, 1.5, 1.5, 1.5, 0.8])
        fields = ["Ref ID", "Name", "Client", "Comm. Date", "Status", "Action"]
        for col, f in zip(cols, fields): col.write(f"**{f}**")

        for idx, row in df.iterrows():
            c = st.columns([1, 2, 1.5, 1.5, 1.5, 0.8])
            c[0].write(row['Reference_ID'])
            c[1].write(row['Candidate Name'])
            c[2].write(row['Client Name'])
            c[3].write(row['Interview Date'])
            c[4].write(row['Status'])
            if c[5].button("📝", key=f"edit_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # --- 9. ACTION / EDIT POPUP (Sidebar) ---
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.markdown("---")
            st.subheader(f"Update: {st.session_state.edit_id}")
            e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
            
            new_status = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Not Joined"])
            new_int_date = e_row['Interview Date']
            
            if new_status == "Interviewed":
                new_int_date = st.date_input("Update Interview Date").strftime("%d-%m-%Y")
            
            new_join_date = ""
            new_sr_date = ""
            if new_status == "Onboarded":
                j_dt = st.date_input("Onboarding Date")
                new_join_date = j_dt.strftime("%d-%m-%Y")
                # SR Calculation
                cl_master = pd.DataFrame(client_sheet.get_all_records())
                sr_days = int(cl_master[cl_master['Client Name'] == e_row['Client Name']].iloc[0]['SR Days'])
                new_sr_date = (j_dt + timedelta(days=sr_days)).strftime("%d-%m-%Y")
            
            new_feed = st.text_area("Update Feedback")
            
            if st.button("CONFIRM UPDATE"):
                all_ids = cand_sheet.col_values(1)
                row_idx = all_ids.index(st.session_state.edit_id) + 1
                cand_sheet.update_cell(row_idx, 7, new_int_date)
                cand_sheet.update_cell(row_idx, 8, new_status)
                cand_sheet.update_cell(row_idx, 10, new_join_date)
                cand_sheet.update_cell(row_idx, 11, new_sr_date)
                cand_sheet.update_cell(row_idx, 12, new_feed)
                st.success("Updated!"); del st.session_state.edit_id; st.rerun()
