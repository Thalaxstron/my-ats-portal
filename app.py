import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE SETUP & SESSION ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. PREMIUM CSS (Blue-Red Gradient + White Icons + Blue Typing) ---
st.markdown("""
    <style>
    /* Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #0d47a1 10%, #d32f2f 100%);
        background-attachment: fixed;
    }
    
    /* Login Layout */
    .login-container {
        text-align: center;
        max-width: 450px;
        margin: auto;
        padding-top: 50px;
    }

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 32px;
        margin-bottom: 10px;
    }

    .ats-title {
        color: white;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 40px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* White Labels for Email/Password */
    .field-label {
        color: white !important;
        font-weight: bold;
        text-align: left;
        margin-bottom: 8px;
        display: block;
        font-size: 14px;
    }

    /* Input Box Styles - Font Colour Blue while typing */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* Blue typing font as requested */
        font-weight: bold !important;
        height: 48px !important;
        border: 2px solid transparent !important;
    }
    
    .stTextInput input:focus {
        border: 2px solid #0d47a1 !important;
    }

    /* Access Button */
    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        width: 100%;
        margin-top: 25px;
        border: 2px solid white;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background: white;
        color: #0d47a1;
    }

    /* Dashboard Visibility Fix */
    header, footer {visibility: hidden;}
    .css-1offfwp e16nr0p33 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

def get_next_ref_id(sheet):
    all_ids = sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(str(val)[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. APP INITIALIZATION ---
try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# --- 5. APPLICATION FLOW ---

if not st.session_state.logged_in:
    # --- MODERN LOGIN SCREEN ---
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
    st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
    
    col_l, col_m, col_r = st.columns([1, 2, 1])
    with col_m:
        # Email Field with White Logo/Label
        st.markdown('<p class="field-label">⚪ EMAIL ID</p>', unsafe_allow_html=True)
        u_mail = st.text_input("email", placeholder="Enter Business Email", label_visibility="collapsed")
        
        st.write(" ")
        # Password Field with White Logo/Label
        st.markdown('<p class="field-label">⚪ PASSWORD</p>', unsafe_allow_html=True)
        u_pass = st.text_input("pass", placeholder="Enter Password", type="password", label_visibility="collapsed")
        
        if st.button("LOGIN SUCCESSFUL"):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
            
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user_full_name = user_match.iloc[0]['Username']
                st.success("Access Granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")
    st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- DASHBOARD & NAVIGATION ---
    st.sidebar.markdown(f"### 👤 Recruiter: {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Main Menu", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    elif menu == "Dashboard & Tracking":
        st.header("📊 Real-time Candidate Tracking")
        raw_data = cand_sheet.get_all_records()
        if raw_data:
            df = pd.DataFrame(raw_data)
            
            # --- Table View ---
            st.markdown("---")
            t_col = st.columns([1, 2, 1.5, 1.2, 1.2, 1.2, 0.5])
            headers = ["Ref ID", "Name", "Client", "Int. Date", "Status", "Onboarded", "Edit"]
            for col, h in zip(t_col, headers): col.markdown(f"**{h}**")
            
            for idx, row in df.iterrows():
                r_col = st.columns([1, 2, 1.5, 1.2, 1.2, 1.2, 0.5])
                r_col[0].write(row['Reference_ID'])
                r_col[1].write(row['Candidate Name'])
                r_col[2].write(row['Client Name'])
                r_col[3].write(row['Interview Date'])
                r_col[4].write(row['Status'])
                r_col[5].write(row['Joining Date'] if row['Joining Date'] else "-")
                
                if r_col[6].button("📝", key=f"ed_{idx}"):
                    st.session_state.edit_id = row['Reference_ID']
                    st.rerun()
            
            # Sidebar Edit Module
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"Editing: {st.session_state.edit_id}")
                    # Logic for updating record...
                    if st.button("Close Editor"):
                        del st.session_state.edit_id
                        st.rerun()
        else:
            st.info("No data found in ATS_Data.")

    elif menu == "New Entry":
        st.header("📝 Create New Shortlist")
        c_df = pd.DataFrame(client_sheet.get_all_records())
        
        with st.form("new_entry_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Candidate Name")
                phone = st.text_input("Mobile Number")
            with col2:
                client_choice = st.selectbox("Client", c_df['Client Name'].unique())
                int_date = st.date_input("Interview Commitment Date")
            
            if st.form_submit_button("Save & Generate WhatsApp"):
                if name and phone:
                    ref = get_next_ref_id(cand_sheet)
                    today = datetime.now().strftime("%d-%m-%Y")
                    # Append Row
                    cand_sheet.append_row([ref, today, name, phone, client_choice, "", int_date.strftime("%d-%m-%Y"), "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    
                    # WA Link
                    msg = f"Hi {name}, your interview is scheduled for {client_choice} on {int_date}."
                    st.success(f"Candidate {name} Saved!")
                    st.markdown(f"[📲 Send WhatsApp Invite](https://wa.me/91{phone}?text={urllib.parse.quote(msg)})")
                else:
                    st.warning("Please enter Name and Phone.")
