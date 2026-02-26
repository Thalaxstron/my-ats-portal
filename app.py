import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Ensure st.secrets has "gcp_service_account"
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database") 
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data") 
except Exception as e:
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1) # Reference_ID column
    if len(all_ids) <= 1:
        return "E00001"
    
    valid_ids = []
    for val in all_ids[1:]:
        if str(val).startswith("E"):
            try:
                valid_ids.append(int(str(val)[1:]))
            except:
                continue
    
    if not valid_ids:
        return "E00001"
    
    next_num = max(valid_ids) + 1
    return f"E{next_num:05d}"

# --- 4. AUTHENTICATION LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #004aad;'>Takecare ATS Portal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Login Details")

# --- 5. MAIN APPLICATION (LOGGED IN) ---
else:
    # Sidebar Navigation
    st.sidebar.title(f"👤 HR: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Main Menu", ["New Entry", "Dashboard & Tracking", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    # --- MODULE: NEW ENTRY ---
    if menu == "New Entry":
        st.header("📝 Candidate Shortlist Entry")
        
        # Load Client Master Data
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        clients_df.columns = [c.strip() for c in clients_df.columns]
        client_options = ["-- Select Client --"] + sorted(clients_df['Client Name'].unique().tolist())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("Candidate Name")
                c_phone = st.text_input("Contact Number (10 digits)")
                selected_client = st.selectbox("Client Name", client_options)
            
            with c2:
                if selected_client != "-- Select Client --":
                    client_rows = clients_df[clients_df['Client Name'] == selected_client]
                    all_pos = []
                    for _, row in client_rows.iterrows():
                        all_pos.extend([p.strip() for p in str(row['Position']).split(',')])
                    
                    job_title = st.selectbox("Select Position", sorted(list(set(all_pos))))
                    client_info = client_rows.iloc[0]
                    db_address = client_info.get('Address', 'Check with HR')
                    
                    # Map Link logic
                    db_map = "No Link"
                    for col in ['Map Link', 'Google Map Link', 'Map']:
                        if col in client_info and str(client_info[col]).strip() != "":
                            db_map = str(client_info[col]).strip()
                            break
                    db_contact_person = client_info.get('Contact Person', 'HR Manager')
                else:
                    job_title = st.selectbox("Select Position", ["Please select client"])
                    db_address, db_map, db_contact_person = "", "", ""
                
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save & Generate WhatsApp", use_container_width=True):
                if selected_client == "-- Select Client --" or not c_name or not c_phone:
                    st.warning("Please fill all fields!")
                else:
                    try:
                        ref_id = get_next_ref_id()
                        today = datetime.now().strftime("%d-%m-%Y")
                        c_date_str = comm_date.strftime("%d-%m-%Y")
                        
                        # Data order matching your Google Sheet columns
                        new_data = [
                            ref_id, today, c_name, c_phone, selected_client, 
                            job_title, c_date_str, "Shortlisted", 
                            st.session_state.user_full_name, "", "", ""
                        ]
                        cand_sheet.append_row(new_data)
                        
                        # WhatsApp Message Template
                        wa_msg = (
                            f"Dear *{c_name}*,\n\n"
                            f"Congratulations! You are shortlisted for the interview.\n\n"
                            f"*Position:* {job_title}\n"
                            f"*Date:* {c_date_str}\n"
                            f"*Client:* {selected_client}\n"
                            f"*Venue:* {db_address}\n"
                            f"*Map:* {db_map}\n"
                            f"*Contact Person:* {db_contact_person}\n\n"
                            f"Regards,\n{st.session_state.user_full_name}\nTakecare Team"
                        )
