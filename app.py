import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. PREMIUM CSS (Gradient + Professional Look) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    [data-testid="stVerticalBlock"] > div:has(div.login-card) {
        display: flex; flex-direction: column; align-items: center;
    }
    .login-card {
        background: rgba(255, 255, 255, 0.1); padding: 30px; border-radius: 15px;
        backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center; width: 100%; max-width: 400px; margin-top: 50px;
    }
    .company-header { color: white; font-family: 'Arial Black', sans-serif; font-size: 28px; }
    .ats-title { color: white; font-weight: bold; font-size: 20px; margin-bottom: 25px; }
    .stTextInput input { border-radius: 8px !important; }
    header, footer {visibility: hidden;}
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

# --- 4. REFRESH & SESSION LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 5. REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 6. MAIN APP ---
if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    _, col_m, _ = st.columns([1, 1.5, 1])
    with col_m:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown('<div class="company-header">TAKECARE MANPOWER</div>', unsafe_allow_html=True)
        st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
        u_mail = st.text_input("Email ID", key="user_email")
        u_pass = st.text_input("Password", type="password", key="user_pass")
        remember = st.checkbox("Remember Me")
        if st.button("ACCESS DASHBOARD", use_container_width=True):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            if not user_row.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_row.iloc[0]['Username']
                st.rerun()
            else: st.error("Invalid Credentials")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD AREA ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.selectbox("Menu", ["Dashboard & Tracking", "New Shortlist Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False; st.rerun()

    # --- MODULE: NEW SHORTLIST ENTRY ---
    if menu == "New Shortlist Entry":
        st.header("📝 Candidate Shortlist Entry")
        clients_df = pd.DataFrame(client_sheet.get_all_records())
        client_options = ["-- Select --"] + sorted(clients_df['Client Name'].unique().tolist())
        
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Candidate Name")
                phone = st.text_input("Contact Number")
                sel_client = st.selectbox("Client Name", client_options)
            with c2:
                if sel_client != "-- Select --":
                    rows = clients_df[clients_df['Client Name'] == sel_client]
                    pos_list = [p.strip() for p in str(rows.iloc[0]['Position']).split(',')]
                    job = st.selectbox("Position", pos_list)
                    addr = rows.iloc[0].get('Address', 'N/A')
                    mlink = rows.iloc[0].get('Map Link') or rows.iloc[0].get('Google Map Link') or 'No Link'
                    cperson = rows.iloc[0].get('Contact Person', 'HR')
                else:
                    job = st.selectbox("Position", ["Select Client First"])
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save & Generate WhatsApp Invite", use_container_width=True):
                if name and phone and sel_client != "-- Select --":
                    ref = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date = comm_date.strftime("%d-%m-%Y")
                    
                    # Save to Sheet
                    cand_sheet.append_row([ref, today, name, phone, sel_client, job, c_date, "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    
                    # WhatsApp Logic
                    msg = (f"Dear *{name}*,\n\nCongratulations! Upon reviewing your application, we would like to invite you for Direct interview and get to know you better.\n\n"
                           f"Please write your resume:\nReference: Takecare Manpower Services Pvt Ltd\n\n"
                           f"Position: {job}\nDate: {c_date}\nInterview Time: 10:30 am\n\n"
                           f"Interview venue:\n*{sel_client}*,\n{addr}\n"
                           f"Map Location: {mlink}\nContact Person: {cperson}\n\n"
                           f"Please Let me know when you arrive at the interview location. All the best....\n\n"
                           f"Regards\n*{st.session_state.user_full_name}*\nTakecare HR Team")
                    
                    wa_link = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                    st.success(f"Candidate {name} Shortlisted!")
                    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; background-color:#25D366; color:
