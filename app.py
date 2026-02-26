import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. CSS ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    header, footer {visibility: hidden;}
    .stButton>button { border-radius: 8px; font-weight: bold; }
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
if 'user_full_name' not in st.session_state: st.session_state.user_full_name = ""

# --- 5. REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 6. POPUP LOGIC (st.dialog) ---
@st.dialog("➕ Add New Candidate Shortlist")
def show_new_entry_popup():
    clients_df = pd.DataFrame(client_sheet.get_all_records())
    
    c_name = st.text_input("Candidate Name")
    c_phone = st.text_input("Phone Number")
    sel_client = st.selectbox("Select Client", ["-- Select --"] + sorted(clients_df['Client Name'].unique().tolist()))
    
    # MULTI-JOB LOGIC
    job_list = ["Select Client First"]
    addr, mlink, cperson = "", "", ""
    if sel_client != "-- Select --":
        c_row = clients_df[clients_df['Client Name'] == sel_client].iloc[0]
        # Split by / or , to handle multiple jobs
        job_list = [j.strip() for j in str(c_row['Position']).replace('/', ',').split(',')]
        addr = c_row.get('Address', 'N/A')
        mlink = c_row.get('Map Link', 'No Link')
        cperson = c_row.get('Contact Person', 'HR')

    sel_job = st.selectbox("Select Position", job_list)
    c_date = st.date_input("Interview Date", datetime.now())
    
    if st.button("SAVE & GENERATE INVITE", use_container_width=True):
        if c_name and c_phone and sel_client != "-- Select --":
            ref = get_next_ref_id()
            today = datetime.now().strftime("%d-%m-%Y")
            formatted_int_date = c_date.strftime("%d-%m-%Y")
            
            # Save to Sheet
            cand_sheet.append_row([ref, today, c_name, c_phone, sel_client, sel_job, formatted_int_date, "Shortlisted", st.session_state.user_full_name, "", "", ""])
            
            # WhatsApp Msg
            msg = f"Dear {c_name}, Your interview for {sel_job} at {sel_client} is on {formatted_int_date}. Venue: {addr}. Map: {mlink}. HR: {cperson}"
            wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
            
            st.success(f"Saved: {ref}")
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold;">📲 SEND WHATSAPP</button></a>', unsafe_allow_html=True)
            if st.button("Close Popup"): st.rerun()
        else:
            st.error("Please fill all details")

# --- 7. MAIN APP ---
if not st.session_state.logged_in:
    _, col_m, _ = st.columns([1, 1.5, 1])
    with col_m:
        st.markdown("<h1 style='color:white; text-align:center;'>TAKECARE ATS</h1>", unsafe_allow_html=True)
        u_mail = st.text_input("Email ID")
        u_pass = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_row.iloc[0]['Username']
                st.rerun()
            else: st.error("Invalid Credentials")

else:
    # --- DASHBOARD ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    if st.sidebar.button("➕ NEW ENTRY", use_container_width=True):
        show_new_entry_popup()
    
    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

    st.header("Candidate Tracking System")
    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        search = st.text_input("🔍 Search Name/Phone")
        if search:
            df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]

        cols = st.columns([1, 2, 1.5, 1.5, 1.2, 1.5, 0.8])
        for col, field in zip(cols, ["Ref ID", "Name", "Client", "Int. Date", "Status", "HR", "Action"]):
            col.write(f"**{field}**")

        for idx, row in df.iterrows():
            c = st.columns([1, 2, 1.5, 1.5, 1.2, 1.5, 0.8])
            c[0].write(row['Reference_ID'])
            c[1].write(row['Candidate Name'])
            c[2].write(row['Client Name'])
            c[3].write(row['Interview Date'])
            c[4].write(row['Status'])
            c[5].write(row['HR Name'])
            if c[6].button("📝", key=f"edit_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # --- 8. EDIT MODAL (Sidebar Logic) ---
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.markdown("---")
            st.subheader(f"⚙️ Edit: {st.session_state.edit_id}")
            df_latest = pd.DataFrame(cand_sheet.get_all_records())
            e_row = df_latest[df_latest['Reference_ID'] == st.session_state.edit_id].iloc[0]
            
            u_status = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected", "Not Joined", "Left"], 
                                    index=["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected", "Not Joined", "Left"].index(e_row['Status']) if e_row['Status'] in ["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected", "Not Joined", "Left"] else 0)
            u_feed = st.text_area("Feedback", value=str(e_row['Feedback']))
            
            # --- SR CALCULATION LOGIC ---
            up_int_date = e_row['Interview Date']
            up_join_date = e_row['Joining Date']
            up_sr_date = e_row['SR Date']

            if u_status == "Interviewed":
                up_int_date = st.date_input("New Interview Date").strftime("%d-%m-%Y")
            
            if u_status == "Onboarded":
                j_dt = st.date_input("Joining Date", datetime.now())
                up_join_date = j_dt.strftime("%d-%m-%Y")
                cl_master = pd.DataFrame(client_sheet.get_all_records())
                cl_row = cl_master[cl_master['Client Name'] == e_row['Client Name']]
                days = int(cl_row.iloc[0]['SR Days']) if not cl_row.empty else 0
                up_sr_date = (j_dt + timedelta(days=days)).strftime("%d-%m-%Y")

            if st.button("SAVE UPDATES"):
                all_ids = cand_sheet.col_values(1)
                row_idx = all_ids.index(st.session_state.edit_id) + 1
                cand_sheet.update_cell(row_idx, 7, up_int_date)
                cand_sheet.update_cell(row_idx, 8, u_status)
                cand_sheet.update_cell(row_idx, 10, up_join_date)
                cand_sheet.update_cell(row_idx, 11, up_sr_date)
                cand_sheet.update_cell(row_idx, 12, u_feed)
                st.success("Updated!"); del st.session_state.edit_id; st.rerun()
            
            if st.button("CANCEL"): del st.session_state.edit_id; st.rerun()
