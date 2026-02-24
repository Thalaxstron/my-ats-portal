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

# --- REF ID LOGIC (Correct Format) ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1:
        return "E00001"
    
    # Last ID-ah eduthu number-ah split panrom
    last_id = all_ids[-1]
    try:
        if last_id.startswith("E"):
            num = int(last_id[1:]) + 1
            return f"E{num:05d}"
        else:
            return "E00001"
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
            # Mail_ID match panni Username-ah session-la vaikirom
            user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_row.iloc[0]['Username'] # HR Name inga irundhu varum
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
        client_options = ["-- Select Client --"] + clients_df['Client Name'].unique().tolist()
        
        with st.form("entry_form"):
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("Candidate Name")
                c_phone = st.text_input("Contact Number")
                # Client Select
                selected_client = st.selectbox("Client Name", client_options)
            
            with c2:
                # Position logic based on client selection
                if selected_client != "-- Select Client --":
                    client_row = clients_df[clients_df['Client Name'] == selected_client].iloc[0]
                    pos_list = [p.strip() for p in str(client_row['Position']).split(',')]
                    job_title = st.selectbox("Select Position", pos_list)
                    addr = client_row['Address']
                    mlink = client_row['Map Link']
                    cperson = client_row['Contact Person']
                else:
                    job_title = st.selectbox("Select Position", ["Please select a client first"])
                
                comm_date = st.date_input("Commitment Date", datetime.now())

            submit = st.form_submit_button("Save & Generate WhatsApp")

            if submit:
                if selected_client == "-- Select Client --" or not c_name or not c_phone:
                    st.warning("Please fill all fields properly!")
                else:
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
                    
                    # WhatsApp Format
                    wa_msg = (
                        f"*INTERVIEW INVITE - {selected_client}*\n\n"
                        f"Dear {c_name},\n"
                        f"Your interview for *{job_title}* is scheduled.\n\n"
                        f"📅 *Date:* {c_date_str}\n"
                        f"📍 *Venue:* {addr}\n"
                        f"🗺️ *Map:* {mlink}\n"
                        f"📞 *Contact:* {cperson}\n\n"
                        f"Regards,\n{st.session_state.user_full_name}\n*Takecare Manpower Services*"
                    )
                    
                    st.success(f"✅ Success! Ref ID: {ref_id}")
                    st.markdown(f"[📲 Send WhatsApp to {c_name}](https://wa.me/91{c_phone}?text={urllib.parse.quote(wa_msg)})")
