import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { background-color: #004aad; color: white; border-radius: 8px; width: 100%; }
    .stHeader { color: #004aad; }
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
    st.error(f"Database Connection error: {e}")
    st.stop()

# --- HELPER FUNCTIONS ---
def get_next_ref_id():
    data = cand_sheet.col_values(1)
    if len(data) <= 1:
        return "E00001"
    last_id = data[-1]
    if last_id.startswith("E"):
        try:
            num = int(last_id[1:]) + 1
            return f"E{num:05d}"
        except:
            return "E00001"
    return "E00001"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN ---
    st.markdown("<h1 style='text-align: center;'>Takecare ATS Login</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username_input = st.text_input("Username (Mail ID)")
        password_input = st.text_input("Password", type="password")
        if st.button("Login"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_data = users_df[(users_df['Mail_ID'] == username_input) & (users_df['Password'].astype(str) == password_input)]
            if not user_data.empty:
                st.session_state.logged_in = True
                st.session_state.user_name = user_data.iloc[0]['Username']
                st.session_state.user_mail = username_input
                st.rerun()
            else:
                st.error("Invalid Login")
else:
    # --- DASHBOARD ---
    st.sidebar.title(f"Hi {st.session_state.user_name}")
    menu = st.sidebar.radio("Navigation", ["Shortlist (New Entry)", "Track Status", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Shortlist (New Entry)":
        st.header("📝 New Candidate Entry")
        
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_list = clients_df['Client Name'].unique().tolist()
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                cand_name = st.text_input("Candidate Name")
                contact = st.text_input("Contact Number")
                client_name = st.selectbox("Select Client", client_list)
            
            with c2:
                selected_client_data = clients_df[clients_df['Client Name'] == client_name].iloc[0]
                positions = str(selected_client_data['Position']).split(',')
                job_title = st.selectbox("Select Job Title", [p.strip() for p in positions])
                commitment_date = st.date_input("Commitment Date", datetime.now())
                sr_days_val = selected_client_data.get('SR Days', 0)

            if st.button("Submit & Save"):
                if cand_name and contact:
                    ref_id = get_next_ref_id()
                    shortlist_date = datetime.now().strftime("%d-%m-%Y")
                    comm_date_str = commitment_date.strftime("%d-%m-%Y")
                    
                    # ATS_Data Headers Order:
                    # RefID, ShortlistDate, Name, Contact, Client, Job, CommDate, Status, HR, JoinDate, SRDate, Feedback
                    new_row = [
                        ref_id, shortlist_date, cand_name, contact, 
                        client_name, job_title, comm_date_str, "Shortlisted", 
                        st.session_state.user_name, "", "", ""
                    ]
                    cand_sheet.append_row(new_row)
                    
                    # WhatsApp
                    addr = selected_client_data.get('Address', '')
                    mlink = selected_client_data.get('Map Link', '')
                    msg = f"Dear {cand_name},\n\nYour interview for {job_title} at {client_name} is fixed on {comm_date_str}.\n\nVenue: {addr}\nMap: {mlink}\n\nAll the best!\nTakecare HR"
                    
                    st.success(f"✅ Saved! Ref ID: {ref_id}")
                    st.markdown(f"[📲 Send WhatsApp Invite](https://wa.me/91{contact}?text={urllib.parse.quote(msg)})")
                else:
                    st.error("Please fill all details")

    elif menu == "Track Status":
        st.header("🔄 Candidate Status Tracking")
        # Inga dhaan neenga sonna 'Interviewed', 'Selected' status update pannanum.
        # Idharku oru list view table create panni edit panra maari kondu varalaam.
        st.info("Ippo New Entry fix panniyachu. Adhuthu indha status update module-ah ready pannuvoma?")
