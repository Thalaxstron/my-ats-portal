import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Takecare Manpower Services", layout="wide")

# --- CUSTOM CSS FOR ATTRACTIVE LOGIN ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #004aad; color: white; }
    .login-header { text-align: center; color: #004aad; font-family: 'Arial'; }
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
    cand_sheet = sh.worksheet("Master_Data")
except Exception as e:
    st.error("Database Connection error. Check your Google Sheet names.")
    st.stop()

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 class='login-header'>Takecare Manpower Services Pvt Ltd</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Cloud ATS Portal Login</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        username = st.text_input("Username (Mail ID)")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_data = users_df[(users_df['Mail ID'] == username) & (users_df['Password'].astype(str) == password)]
            
            if not user_data.empty:
                st.session_state.logged_in = True
                st.session_state.user_name = user_data.iloc[0]['User Name']
                st.session_state.role = user_data.iloc[0]['Role']
                st.session_state.user_mail = username
                st.rerun()
            else:
                st.error("Invalid Username or Password")
        
        if st.button("Forgot Password?", key="forgot"):
            st.info("Please contact Admin to reset your password.")

else:
    # --- DASHBOARD START ---
    st.sidebar.title(f"Welcome, {st.session_state.user_name}")
    st.sidebar.write(f"Role: {st.session_state.role}")
    
    menu = ["Shortlisted (New Entry)", "Interviewed", "Onboarded", "Reports", "Master (Admin Only)"]
    choice = st.sidebar.selectbox("Navigate", menu)

    # --- LOGIC: REFERENCE ID GENERATION ---
    def generate_ref_id():
        data = cand_sheet.col_values(1) # Get Reference_ID column
        if len(data) <= 1:
            return "E0001"
        last_id = data[-1]
        if last_id.startswith("E"):
            num = int(last_id[1:]) + 1
            return f"E{num:04d}"
        return "E0001"

    # --- MODULE 1: SHORTLISTED (NEW ENTRY) ---
    if choice == "Shortlisted (New Entry)":
        st.header("📝 New Candidate Shortlist")
        
        # Load Clients
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_list = clients_df['Client Name'].tolist()
        
        with st.form("shortlist_form"):
            c1, c2 = st.columns(2)
            with c1:
                cand_name = st.text_input("Candidate Name")
                contact = st.text_input("Contact Number")
                client_name = st.selectbox("Select Client", client_list)
            with c2:
                # Filter positions based on client
                positions = clients_df[clients_df['Client Name'] == client_name]['Position'].iloc[0].split(',')
                job_title = st.selectbox("Select Job Title", [p.strip() for p in positions])
                interview_date = st.date_input("Interview Commitment Date")
            
            submit = st.form_submit_button("Submit & Generate WhatsApp Invite")
            
            if submit:
                # Duplicate Check
                all_contacts = cand_sheet.col_values(4)
                if contact in all_contacts:
                    st.warning("⚠️ Candidate with this number already exists!")
                else:
                    ref_id = generate_ref_id()
                    curr_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # Save to Sheet
                    new_entry = [ref_id, curr_date, cand_name, contact, client_name, job_title, 
                                 str(interview_date), st.session_state.user_name, "Shortlisted", 
                                 "", "", "", ""]
                    cand_sheet.append_row(new_entry)
                    
                    # WhatsApp Template Logic
                    client_info = clients_df[clients_df['Client Name'] == client_name].iloc[0]
                    msg = f"Dear {cand_name},\n\nCongratulations! You are invited for an interview.\n\nPosition: {job_title}\nInterview Date: {interview_date}\nVenue: {client_info['Address']}\nMap: {client_info['Google Map Link']}\nContact: {client_info['Contact Person']}\n\nRegards,\n{st.session_state.user_name}\nTakecare HR Team"
                    encoded_msg = urllib.parse.quote(msg)
                    wa_link = f"https://wa.me/91{contact}?text={encoded_msg}"
                    
                    st.success(f"✅ Candidate Added! ID: {ref_id}")
                    st.markdown(f"[Click here to send WhatsApp Invite]( {wa_link} )")

    # --- Logout Button ---
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
