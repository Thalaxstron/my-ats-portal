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
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1:
        return "E00001"
    last_id = all_ids[-1]
    try:
        if last_id.startswith("E"):
            num = int(last_id[1:]) + 1
            return f"E{num:05d}"
        else:
            return f"E{len(all_ids):05d}"
    except:
        return f"E{len(all_ids):05d}"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: #004aad;'>Takecare ATS Portal</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        u_mail = st.text_input("Email ID")
        u_pass = st.text_input("Password", type="password")
        if st.button("Login"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_row.iloc[0]['Username']
                st.rerun()
            else:
                st.error("Invalid Login Details")
else:
    st.sidebar.title(f"HR: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Menu", ["New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    if menu == "New Entry":
        st.header("📝 Candidate Shortlist Entry")
        
        # Client Data Loading
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_options = ["-- Select Client --"] + sorted(clients_df['Client Name'].unique().tolist())
        
        # UI WITHOUT st.form for Dynamic Updates
        c1, c2 = st.columns(2)
        with c1:
            c_name = st.text_input("Candidate Name", key="cname")
            c_phone = st.text_input("Contact Number", key="cphone")
            selected_client = st.selectbox("Client Name", client_options, key="client_sel")
        
        with c2:
            # Position logic - Refresh aagum pothu correct-ah position kattiye theerum
            if selected_client != "-- Select Client --":
                # Multiple rows for same client handling
                specific_client_rows = clients_df[clients_df['Client Name'] == selected_client]
                
                # Ellaa position-aiyum serthu oru list-ah mathurom
                all_pos = []
                for idx, row in specific_client_rows.iterrows():
                    all_pos.extend([p.strip() for p in str(row['Position']).split(',')])
                
                job_title = st.selectbox("Select Position", sorted(list(set(all_pos))))
                
                # Fetch first row details for Venue/Map
                client_info = specific_client_rows.iloc[0]
                addr = client_info.get('Address', 'Contact HR')
                mlink = client_info.get('Map Link', 'No Link')
                cperson = client_info.get('Contact Person', 'HR Team')
                sr_days = client_info.get('SR Days', '0')
            else:
                job_title = st.selectbox("Select Position", ["Please select client"])
            
            comm_date = st.date_input("Commitment Date", datetime.now())

        if st.button("Save Entry & Get WhatsApp Link"):
            if selected_client == "-- Select Client --" or not c_name or not c_phone:
                st.warning("All fields are mandatory!")
            else:
                try:
                    ref_id = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date_str = comm_date.strftime("%d-%m-%Y")
                    
                    # Row data for ATS_Data
                    new_data = [
                        ref_id, today, c_name, c_phone, selected_client, 
                        job_title, c_date_str, "Shortlisted", 
                        st.session_state.user_full_name, "", "", ""
                    ]
                    cand_sheet.append_row(new_data)
                    
                    # Professional WhatsApp Format
                    wa_msg = (
                        f"*INTERVIEW INVITE - {selected_client}*\n"
                        f"----------------------------------\n"
                        f"Dear *{c_name}*,\n\n"
                        f"Your interview for *{job_title}* has been scheduled.\n\n"
                        f"📅 *Date:* {c_date_str}\n"
                        f"📍 *Venue:* {addr}\n"
                        f"🗺️ *Map:* {mlink}\n"
                        f"📞 *Contact Person:* {cperson}\n\n"
                        f"Regards,\n{st.session_state.user_full_name}\n*Takecare Manpower Services*"
                    )
                    
                    st.success(f"✅ Data Saved! Reference ID: {ref_id}")
                    st.markdown(f"[📲 Click to Send WhatsApp to {c_name}](https://wa.me/91{c_phone}?text={urllib.parse.quote(wa_msg)})")
                except Exception as e:
                    st.error(f"Error during save: {e}")
