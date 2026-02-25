import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & STABILITY ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# Persistent Session Logic: Intha block thaan refresh panna dashboard-laye irukka vaikum
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. THEME & UI (Unga Flask-style Gradient Design) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
    }
    .login-box {
        background: white;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0px 0px 15px rgba(0,0,0,0.5);
        text-align: center;
        color: #2c5364;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: #2c5364;
        color: white;
        border-radius: 5px;
        width: 100%;
    }
    /* Keeping text readable on dark background */
    h1, h2, h3, span, label, .stMarkdown { color: white !important; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
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

# --- 4. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(str(val)[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 5. APP NAVIGATION ---

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.write("#")
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div class="login-box">
                <h2 style="color: #2c5364 !important; margin-bottom:0;">Takecare Manpower Services Pvt Ltd</h2>
                <p style="color: #2c5364 !important; font-weight: bold; font-size: 20px;">ATS LOGIN</p>
            </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            u_mail = st.text_input("Business Email")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Email or Password")

else:
    # --- LOGGED IN AREA ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Main Menu", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_full_name = ""
        st.rerun()

    # --- DASHBOARD & TRACKING ---
    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking")
        data = cand_sheet.get_all_records()
        if not data:
            st.info("No records found.")
        else:
            df = pd.DataFrame(data)
            # Filters
            f1, f2, f3 = st.columns(3)
            with f1: search = st.text_input("🔍 Search Name/Contact")
            with f2: hr_f = st.selectbox("HR Filter", ["All"] + sorted(df['HR Name'].unique().tolist()))
            with f3: cl_f = st.selectbox("Client Filter", ["All"] + sorted(df['Client Name'].unique().tolist()))

            if search:
                df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]
            if hr_f != "All": df = df[df['HR Name'] == hr_f]
            if cl_f != "All": df = df[df['Client Name'] == cl_f]

            # TABLE VIEW
            st.markdown("---")
            t_col = st.columns([1, 2, 1.5, 1.2, 1.2, 1.2, 0.5])
            headers = ["Ref ID", "Name", "Client", "Comm. Date", "Status", "Onboard", "Edit"]
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

            # Sidebar Edit
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"Update {st.session_state.edit_id}")
                    e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
                    new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], 
                                         index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(e_row['Status']))
                    new_feed = st.text_area("Feedback", value=e_row['Feedback'])
                    
                    # Onboard Logic
                    up_join, up_sr = e_row['Joining Date'], e_row['SR Date']
                    if new_st == "Onboarded":
                        j_d = st.date_input("Join Date")
                        up_join = j_d.strftime("%d-%m-%Y")
                        c_df = pd.DataFrame(client_sheet.get_all_records())
                        c_info = c_df[c_df['Client Name'] == e_row['Client Name']]
                        days = int(c_info.iloc[0]['SR Days']) if not c_info.empty else 0
                        up_sr = (j_d + timedelta(days=days)).strftime("%d-%m-%Y")

                    if st.button("Confirm Update"):
                        all_ids = cand_sheet.col_values(1)
                        row_num = all_ids.index(st.session_state.edit_id) + 1
                        cand_sheet.update_cell(row_num, 8, new_st)
                        cand_sheet.update_cell(row_num, 10, up_join)
                        cand_sheet.update_cell(row_num, 11, up_sr)
                        cand_sheet.update_cell(row_num, 12, new_feed)
                        del st.session_state.edit_id
                        st.rerun()

    # --- NEW ENTRY ---
    elif menu == "New Entry":
        st.header("📝 Candidate Entry")
        c_df = pd.DataFrame(client_sheet.get_all_records())
        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Candidate Name")
                c_phone = st.text_input("Phone Number")
                c_client = st.selectbox("Select Client", ["-- Select --"] + sorted(c_df['Client Name'].tolist()))
            with col2:
                if c_client != "-- Select --":
                    rows = c_df[c_df['Client Name'] == c_client]
                    pos = [p.strip() for p in str(rows.iloc[0]['Position']).split(',')]
                    c_job = st.selectbox("Position", pos)
                else: c_job = st.selectbox("Position", ["Select Client First"])
                c_date = st.date_input("Commitment Date", datetime.now())
            
            if st.button("Save & Generate WhatsApp"):
                if c_name and c_phone and c_client != "-- Select --":
                    ref = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    cand_sheet.append_row([ref, today, c_name, c_phone, c_client, c_job, c_date.strftime("%d-%m-%Y"), "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    st.success(f"Saved! Ref ID: {ref}")
                    # WhatsApp generation logic can be added here
                else: st.error("Fill all fields")
