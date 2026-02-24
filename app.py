import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

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

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #004aad;'>Takecare Manpower Services Pvt Ltd</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username (Mail ID)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            # Google Sheet-il 'Mail_ID' endra peyar irukka vendum
            user_data = users_df[(users_df['Mail_ID'] == username) & (users_df['Password'].astype(str) == password)]
            
            if not user_data.empty:
                st.session_state.logged_in = True
                st.session_state.user_name = user_data.iloc[0]['Username']
                st.session_state.role = user_data.iloc[0]['Role']
                st.session_state.user_mail = username
                st.rerun()
            else:
                st.error("Invalid Username or Password")

else:
    # --- DASHBOARD ---
    st.sidebar.title(f"Welcome, {st.session_state.user_name}")
    choice = st.sidebar.selectbox("Navigate", ["Shortlisted (New Entry)", "Reports"])

    if choice == "Shortlisted (New Entry)":
        st.header("📝 New Candidate Shortlist")
        
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_list = clients_df['Client Name'].tolist()
        
        with st.form("shortlist_form"):
            c1, c2 = st.columns(2)
            with c1:
                cand_name = st.text_input("Candidate Name")
                contact = st.text_input("Contact Number")
                client_name = st.selectbox("Select Client", client_list)
            with c2:
                # Client-ai select pannum pothu 'Position' and 'SR Days' values-ai yedukkum
                client_info = clients_df[clients_df['Client Name'] == client_name].iloc[0]
                positions = str(client_info['Position']).split(',')
                job_title = st.selectbox("Select Job Title", [p.strip() for p in positions])
                interview_date = st.date_input("Interview Date")
                sr_days = client_info['SR Days'] # Intha column ippo code-la use aaguthu
            
            if st.form_submit_button("Submit"):
                new_entry = [f"E{datetime.now().strftime('%M%S')}", datetime.now().strftime("%Y-%m-%d"), 
                             cand_name, contact, client_name, job_title, str(interview_date), 
                             "Shortlisted", st.session_state.user_name, "", str(sr_days), ""]
                cand_sheet.append_row(new_entry)
                
                # WhatsApp message-la Map Link and Contact Person serthuvittaen
                msg = f"Dear {cand_name},\nPosition: {job_title}\nVenue: {client_info['Address']}\nMap: {client_info['Map Link']}\nContact: {client_info['Contact Person']}"
                st.success(f"✅ Added! SR Days for this client: {sr_days}")
                st.markdown(f"[Send WhatsApp](https://wa.me/91{contact}?text={urllib.parse.quote(msg)})")
