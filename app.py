import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    .stHeader { color: white; }
    header, footer {visibility: hidden;}
    .stButton>button { border-radius: 8px; font-weight: bold; }
    [data-testid="stForm"] { background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.2); }
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
if 'user_full_name' not in st.session_state: st.session_state.user_full_name = ""
if 'show_new_entry' not in st.session_state: st.session_state.show_new_entry = False

# --- 5. REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 6. MAIN APP ---
if not st.session_state.logged_in:
    # --- LOGIN ---
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
            else: st.error("Invalid Login")
else:
    # --- DASHBOARD ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    
    # NEW ENTRY POPUP TRIGGER
    if st.sidebar.button("➕ ADD NEW CANDIDATE", use_container_width=True):
        st.session_state.show_new_entry = True
    
    if st.sidebar.button("📊 DASHBOARD REFRESH", use_container_width=True):
        st.rerun()

    if st.sidebar.button("🚪 LOGOUT", use_container_width=True):
        st.session_state.logged_in = False; st.rerun()

    # 1. NEW ENTRY SIDE-POPUP (Form)
    if st.session_state.show_new_entry:
        with st.sidebar:
            st.markdown("### 📝 New Entry Form")
            clients_df = pd.DataFrame(client_sheet.get_all_records())
            c_name = st.text_input("Candidate Name")
            c_phone = st.text_input("Phone Number")
            sel_client = st.selectbox("Select Client", ["-- Select --"] + sorted(clients_df['Client Name'].unique().tolist()))
            
            # --- MULTI-JOB LOGIC ---
            if sel_client != "-- Select --":
                client_row = clients_df[clients_df['Client Name'] == sel_client].iloc[0]
                # Comma separated positions-ah list-ah maathuradhu
                raw_positions = str(client_row['Position'])
                job_list = [j.strip() for j in raw_positions.replace('/', ',').split(',')]
                sel_job = st.selectbox("Select Position", job_list)
                
                # Hidden data for WhatsApp
                addr = client_row.get('Address', 'N/A')
                mlink = client_row.get('Map Link', 'No Link')
                cperson = client_row.get('Contact Person', 'HR')
            
            c_date = st.date_input("Interview Date")
            
            col_save, col_close = st.columns(2)
            if col_save.button("SAVE DATA"):
                if c_name and c_phone and sel_client != "-- Select --":
                    ref = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    int_date_str = c_date.strftime("%d-%m-%Y")
                    
                    cand_sheet.append_row([ref, today, c_name, c_phone, sel_client, sel_job, int_date_str, "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    
                    # WA Link
                    msg = f"Dear {c_name}, Your interview at {sel_client} for {sel_job} is fixed on {int_date_str}. Venue: {addr}. Map: {mlink}. Regards, {st.session_state.user_full_name}"
                    wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
                    
                    st.success("Saved!")
                    st.markdown(f'<a href="{wa_url}" target="_blank">📲 Send WhatsApp</a>', unsafe_allow_html=True)
                else: st.error("Fill all!")
            
            if col_close.button("CLOSE"):
                st.session_state.show_new_entry = False; st.rerun()

    # 2. TRACKING TABLE (Main Screen)
    st.header("Candidate Tracking")
    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        
        # Search & Filter
        s_col1, s_col2 = st.columns(2)
        search = s_col1.text_input("🔍 Search Name/Phone")
        if search: df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]
        
        # Table Header
        h_cols = st.columns([1, 2, 1.5, 1.5, 1.5, 1])
        headers = ["Ref", "Name", "Client", "Int.Date", "Status", "Edit"]
        for col, h in zip(h_cols, headers): col.write(f"**{h}**")

        for idx, row in df.iterrows():
            c = st.columns([1, 2, 1.5, 1.5, 1.5, 1])
            c[0].write(row['Reference_ID'])
            c[1].write(row['Candidate Name'])
            c[2].write(row['Client Name'])
            c[3].write(row['Interview Date'])
            c[4].write(row['Status'])
            if c[5].button("📝", key=f"ed_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # 3. EDIT LOGIC (Sidebar Popup for Editing)
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.markdown(f"### ⚙️ Edit: {st.session_state.edit_id}")
            e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
            
            new_status = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected"], index=["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected"].index(row['Status']) if row['Status'] in ["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected"] else 0)
            new_feed = st.text_area("Feedback", value=e_row['Feedback'])
            
            # --- DATE CALCULATION LOGIC ---
            up_int = e_row['Interview Date']
            up_join = e_row['Joining Date']
            up_sr = e_row['SR Date']

            if new_status == "Onboarded":
                join_dt = st.date_input("Joining Date")
                up_join = join_dt.strftime("%d-%m-%Y")
                # SR Calculation from Client Master
                c_df_m = pd.DataFrame(client_sheet.get_all_records())
                c_m_row = c_df_m[c_df_m['Client Name'] == e_row['Client Name']]
                sr_days = int(c_m_row.iloc[0]['SR Days']) if not c_m_row.empty else 0
                up_sr = (join_dt + timedelta(days=sr_days)).strftime("%d-%m-%Y")

            if st.button("UPDATE CANDIDATE"):
                all_ids = cand_sheet.col_values(1)
                row_idx = all_ids.index(st.session_state.edit_id) + 1
                cand_sheet.update_cell(row_idx, 8, new_status)
                cand_sheet.update_cell(row_idx, 10, up_join)
                cand_sheet.update_cell(row_idx, 11, up_sr)
                cand_sheet.update_cell(row_idx, 12, new_feed)
                st.success("Updated!"); del st.session_state.edit_id; st.rerun()
            
            if st.button("CANCEL"):
                del st.session_state.edit_id; st.rerun()
