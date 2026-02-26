import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

# --- CUSTOM CSS (Pleasant Look) ---
st.markdown("""
    <style>
    .main { background-color: #f7f9fc; }
    .stButton>button { background-color: #004aad; color: white; border-radius: 20px; font-weight: bold; }
    .stHeader { color: #004aad; font-family: 'Helvetica'; }
    .sidebar .sidebar-content { background-image: linear-gradient(#004aad, #0072ff); color: white; }
    div[data-testid="stExpander"] { border: 1px solid #004aad; border-radius: 10px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
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
    st.error(f"Database Error: {e}")
    st.stop()

# --- HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = []
    for val in all_ids[1:]:
        if str(val).startswith("E"):
            try: valid_ids.append(int(str(val)[1:]))
            except: continue
    next_num = max(valid_ids) + 1 if valid_ids else 1
    return f"E{next_num:05d}"

# --- APP LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- ATTRACTIVE LOGIN PAGE ---
    st.markdown("<h1 style='text-align: center; color: #004aad;'>Takecare Manpower Services</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Portal Login</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            u_mail = st.text_input("📧 Email ID")
            u_pass = st.text_input("🔑 Password", type="password")
            if st.button("Login to Portal"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Login Details")
            st.caption("🔒 Forgot Password? Please contact Admin to reset.")

else:
    # --- SIDEBAR WITH LOGO ---
    st.sidebar.image("https://via.placeholder.com/150?text=Takecare+Logo", width=150) # Inga unga Logo URL kudunga
    st.sidebar.title(f"Welcome, {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Navigate", ["New Shortlist", "Status Tracking", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    # --- MODULE 1: NEW ENTRY ---
    if menu == "New Shortlist":
        st.header("📝 Candidate Shortlist Entry")
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        clients_df.columns = [c.strip() for c in clients_df.columns]
        client_options = ["-- Select Client --"] + sorted(clients_df['Client Name'].unique().tolist())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("Candidate Name")
                c_phone = st.text_input("Contact Number")
                selected_client = st.selectbox("Client Name", client_options)
            with c2:
                if selected_client != "-- Select Client --":
                    client_rows = clients_df[clients_df['Client Name'] == selected_client]
                    all_pos = []
                    for idx, row in client_rows.iterrows():
                        all_pos.extend([p.strip() for p in str(row['Position']).split(',')])
                    job_title = st.selectbox("Select Position", sorted(list(set(all_pos))))
                    client_info = client_rows.iloc[0]
                    db_address = client_info.get('Address', 'Check HR')
                    db_map = client_info.get('Map Link') or 'No Link'
                    db_contact_person = client_info.get('Contact Person', 'HR Manager')
                else:
                    job_title = st.selectbox("Select Position", ["Select client first"])
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save & Generate WhatsApp"):
                if selected_client == "-- Select Client --" or not c_name or not c_phone:
                    st.warning("Please fill all details!")
                else:
                    ref_id = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date_str = comm_date.strftime("%d-%m-%Y")
                    new_data = [ref_id, today, c_name, c_phone, selected_client, job_title, c_date_str, "Shortlisted", st.session_state.user_full_name, "", "", ""]
                    cand_sheet.append_row(new_data)
                    
                    wa_msg = f"Dear *{c_name}*,\n\nCongratulations! You're invited for an interview.\n\n*Position:* {job_title}\n*Date:* {c_date_str}\n*Venue:* {selected_client}, {db_address}\n*Map:* {db_map}\n*Contact:* {db_contact_person}\n\nRegards,\n{st.session_state.user_full_name}\nTakecare Team"
                    st.success(f"✅ Saved! Ref: {ref_id}")
                    st.markdown(f"[📲 Send WhatsApp](https://wa.me/91{c_phone}?text={urllib.parse.quote(wa_msg)})")

    # --- MODULE 2: STATUS TRACKING ---
    elif menu == "Status Tracking":
        st.header("🔄 Candidate Status Management")
        
        # Load ATS Data
        data = cand_sheet.get_all_records()
        if not data:
            st.info("No data found in ATS_Data.")
        else:
            df = pd.DataFrame(data)
            
            # Filter Options
            search = st.text_input("🔍 Search by Name or Contact")
            if search:
                df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]
            
            st.write(f"Showing {len(df)} candidates")
            
            for i, row in df.iterrows():
                with st.expander(f"{row['Reference_ID']} - {row['Candidate Name']} ({row['Status']})"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Client:** {row['Client Name']}")
                        st.write(f"**Job:** {row['Job Title']}")
                    with col2:
                        new_status = st.selectbox("Update Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(row['Status']) if row['Status'] in ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"] else 0, key=f"stat_{i}")
                    with col3:
                        feedback = st.text_input("Feedback", value=row.get('Feedback', ''), key=f"feed_{i}")
                    
                    # Special Fields for Onboarded
                    join_date_val = ""
                    sr_date_val = ""
                    if new_status == "Onboarded":
                        c_a, c_b = st.columns(2)
                        with c_a:
                            join_date = st.date_input("Joining Date", key=f"join_{i}")
                            join_date_val = join_date.strftime("%d-%m-%Y")
                        with c_b:
                            # SR Date Calculation
                            clients_df = pd.DataFrame(client_sheet.get_all_records())
                            c_info = clients_df[clients_df['Client Name'] == row['Client Name']]
                            sr_days = int(c_info.iloc[0]['SR Days']) if not c_info.empty else 0
                            sr_date = join_date + timedelta(days=sr_days)
                            sr_date_val = sr_date.strftime("%d-%m-%Y")
                            st.write(f"**Auto SR Date:** {sr_date_val}")

                    if st.button("Update Candidate", key=f"btn_{i}"):
                        # Find row in Sheet (Row 1 is header, so +2 for 0-index)
                        # Intha logic kandippa correct row-ah update pannum
                        actual_row_index = i + 2 
                        
                        cand_sheet.update_cell(actual_row_index, 8, new_status) # Status Column
                        cand_sheet.update_cell(actual_row_index, 12, feedback) # Feedback Column
                        if new_status == "Onboarded":
                            cand_sheet.update_cell(actual_row_index, 10, join_date_val) # Joining Date
                            cand_sheet.update_cell(actual_row_index, 11, sr_date_val) # SR Date
                        
                        st.success(f"Updated {row['Candidate Name']}!")
                        st.rerun()
