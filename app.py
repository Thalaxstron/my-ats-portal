import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & PERSISTENT SESSION ---
st.set_page_config(page_title="Takecare ATS", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. PROFESSIONAL CSS (CLEAN LOOK) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #F0F2F6; }
    
    /* Custom Login Container */
    .login-box {
        background-color: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Buttons */
    .stButton>button {
        background-image: linear-gradient(to right, #004aad, #0072ff);
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
    }
    
    /* Table Styling */
    .reportview-container { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
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

# --- 4. LOGIC FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(str(val)[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 5. APP FLOW ---

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        st.write("#") # Spacer
        st.markdown("""
            <div class='login-box'>
                <h1 style='color: #004aad;'>Takecare ATS</h1>
                <p style='color: #666;'>Manpower Services Pvt Ltd</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=True):
            u_mail = st.text_input("📧 Business Email")
            u_pass = st.text_input("🔑 Password", type="password")
            if st.button("Login"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Login Details")
            st.info("Forgot password? Contact Systems Admin.")

# --- DASHBOARD SCREEN ---
else:
    # Sidebar
    st.sidebar.title("Takecare ATS")
    st.sidebar.write(f"Logged in as: **{st.session_state.user_full_name}**")
    menu = st.sidebar.radio("Main Menu", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_full_name = ""
        st.rerun()

    # --- NEW ENTRY MODULE ---
    if menu == "New Entry":
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
                    all_pos = []
                    for idx, row in rows.iterrows():
                        all_pos.extend([p.strip() for p in str(row['Position']).split(',')])
                    job = st.selectbox("Position", sorted(list(set(all_pos))))
                    addr = rows.iloc[0].get('Address', '')
                    mlink = rows.iloc[0].get('Map Link') or 'No Link'
                    cperson = rows.iloc[0].get('Contact Person', 'HR')
                else:
                    job = st.selectbox("Position", ["Please select client"])
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save & Generate WhatsApp"):
                if name and phone and sel_client != "-- Select --":
                    ref = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date = comm_date.strftime("%d-%m-%Y")
                    # Save (RefID, ShortDate, Name, Phone, Client, Job, CommDate, Status, HR, JoinDate, SRDate, Feedback)
                    cand_sheet.append_row([ref, today, name, phone, sel_client, job, c_date, "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    
                    wa_msg = f"Dear *{name}*,\n\nYou are invited for an interview.\n*Position:* {job}\n*Date:* {c_date}\n*Venue:* {sel_client}, {addr}\n*Map:* {mlink}\n*Contact:* {cperson}"
                    st.success(f"Candidate {name} Saved!")
                    st.markdown(f"[📲 Send WhatsApp](https://wa.me/91{phone}?text={urllib.parse.quote(wa_msg)})")
                else: st.error("Incomplete Details")

    # --- TRACKING MODULE ---
    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking Dashboard")
        
        raw_data = cand_sheet.get_all_records()
        if not raw_data: st.info("No candidates yet.")
        else:
            df = pd.DataFrame(raw_data)
            
            # FILTERS
            f1, f2 = st.columns(2)
            with f1: search_name = st.text_input("🔍 Search Name/Number")
            with f2: hr_filter = st.selectbox("Filter HR", ["All"] + sorted(df['HR Name'].unique().tolist()))

            # Apply Filter
            if search_name:
                df = df[df['Candidate Name'].str.contains(search_name, case=False) | df['Contact Number'].astype(str).contains(search_name)]
            if hr_filter != "All":
                df = df[df['HR Name'] == hr_filter]

            # TABLE HEADER
            st.markdown("---")
            t1, t2, t3, t4, t5, t6, t7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 0.5])
            t1.write("**Ref ID**")
            t2.write("**Name**")
            t3.write("**Client**")
            t4.write("**Comm. Date**")
            t5.write("**Status**")
            t6.write("**Onboard Date**") # New Column added to Table
            t7.write("**Edit**")

            for idx, row in df.iterrows():
                r1, r2, r3, r4, r5, r6, r7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 0.5])
                r1.write(row['Reference_ID'])
                r2.write(row['Candidate Name'])
                r3.write(row['Client Name'])
                r4.write(row['Interview Date'])
                r5.write(row['Status'])
                r6.write(row['Joining Date'] if row['Joining Date'] else "-")
                
                if r7.button("📝", key=f"edit_{idx}"):
                    st.session_state.edit_id = row['Reference_ID']
                    st.session_state.edit_idx = idx

            # EDIT SIDEBAR (Persistence logic included)
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.subheader(f"Update: {st.session_state.edit_id}")
                    e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
                    
                    new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], 
                                         index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(e_row['Status']))
                    
                    new_feed = st.text_area("Feedback", value=e_row['Feedback'])
                    
                    # Date variables
                    up_int = e_row['Interview Date']
                    up_join = e_row['Joining Date']
                    up_sr = e_row['SR Date']

                    if new_st == "Interviewed":
                        up_int = st.date_input("Interview Date").strftime("%d-%m-%Y")
                    if new_st == "Onboarded":
                        j_date = st.date_input("Join Date")
                        up_join = j_date.strftime("%d-%m-%Y")
                        # SR Logic
                        c_df = pd.DataFrame(client_sheet.get_all_records())
                        c_row = c_df[c_df['Client Name'] == e_row['Client Name']]
                        days = int(c_row.iloc[0]['SR Days']) if not c_row.empty else 0
                        up_sr = (j_date + timedelta(days=days)).strftime("%d-%m-%Y")

                    if st.button("Confirm Update"):
                        # Sheet is 1-indexed, +2 to skip header and 0-index
                        row_num = st.session_state.edit_idx + 2
                        cand_sheet.update_cell(row_num, 7, up_int)
                        cand_sheet.update_cell(row_num, 8, new_st)
                        cand_sheet.update_cell(row_num, 10, up_join)
                        cand_sheet.update_cell(row_num, 11, up_sr)
                        cand_sheet.update_cell(row_num, 12, new_feed)
                        
                        st.success("Updated!")
                        del st.session_state.edit_id
                        st.rerun()
