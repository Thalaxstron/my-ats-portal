import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- CUSTOM CSS (Pleasant & Professional) ---
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .main-header { color: #004aad; text-align: center; padding: 10px; }
    /* Table Styling */
    div[data-testid="stExpander"] { border: none !important; }
    .reportview-container .main .block-container { padding-top: 2rem; }
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
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- REF ID LOGIC ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.markdown("<h1 class='main-header'>Takecare Manpower Services</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        with st.container(border=True):
            st.subheader("Login to ATS")
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("Access Dashboard", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

else:
    # --- SIDEBAR ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.selectbox("Menu", ["Dashboard & Tracking", "New Shortlist Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    # --- MODULE: NEW SHORTLIST ---
    if menu == "New Shortlist Entry":
        st.header("📝 Candidate Shortlist")
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
                    addr = rows.iloc[0].get('Address', '')
                    mlink = rows.iloc[0].get('Map Link') or rows.iloc[0].get('Google Map Link') or 'No Link'
                    cperson = rows.iloc[0].get('Contact Person', 'HR')
                else:
                    job = st.selectbox("Position", ["Select Client First"])
                comm_date = st.date_input("Commitment Date", datetime.now())

            if st.button("Save & WhatsApp", use_container_width=True):
                if name and phone and sel_client != "-- Select --":
                    ref = get_next_ref_id()
                    today = datetime.now().strftime("%d-%m-%Y")
                    c_date = comm_date.strftime("%d-%m-%Y")
                    # Save (Status column index 8)
                    cand_sheet.append_row([ref, today, name, phone, sel_client, job, c_date, "Shortlisted", st.session_state.user_full_name, "", "", ""])
                    # WhatsApp message logic here... (omitted for brevity)
                    st.success(f"Candidate {name} Shortlisted!")
                else: st.warning("Fill all details")

    # --- MODULE: DASHBOARD & TRACKING ---
    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking System")
        
        # 1. LOAD DATA
        raw_data = cand_sheet.get_all_records()
        if not raw_data:
            st.info("No candidates found.")
        else:
            all_df = pd.DataFrame(raw_data)
            
            # 2. SMART FILTERS
            f1, f2, f3 = st.columns(3)
            with f1:
                search_q = st.text_input("🔍 Search Name/Mobile")
            with f2:
                client_filter = st.selectbox("Filter by Client", ["All"] + sorted(all_df['Client Name'].unique().tolist()))
            with f3:
                hr_filter = st.selectbox("Filter by Recruiter", ["All"] + sorted(all_df['HR Name'].unique().tolist()))

            # Apply Filters
            filtered_df = all_df.copy()
            if search_q:
                filtered_df = filtered_df[filtered_df['Candidate Name'].str.contains(search_q, case=False) | filtered_df['Contact Number'].astype(str).contains(search_q)]
            if client_filter != "All":
                filtered_df = filtered_df[filtered_df['Client Name'] == client_filter]
            if hr_filter != "All":
                filtered_df = filtered_df[filtered_df['HR Name'] == hr_filter]

            # 3. DATA TABLE VIEW
            st.markdown("---")
            # Headers for our manual table
            h1, h2, h3, h4, h5, h6, h7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 1])
            h1.write("**Ref ID**")
            h2.write("**Candidate Name**")
            h3.write("**Client**")
            h4.write("**Comm. Date**")
            h5.write("**Status**")
            h6.write("**HR Name**")
            h7.write("**Action**")

            for idx, row in filtered_df.iterrows():
                r1, r2, r3, r4, r5, r6, r7 = st.columns([1, 2, 1.5, 1.5, 1.5, 1.5, 1])
                r1.write(row['Reference_ID'])
                r2.write(row['Candidate Name'])
                r3.write(row['Client Name'])
                r4.write(row['Interview Date']) # This is Commitment Date in Sheet
                
                # Status Color Coding
                status_color = {"Shortlisted": "🔵", "Selected": "🟢", "Rejected": "🔴", "Onboarded": "🟣"}.get(row['Status'], "⚪")
                r5.write(f"{status_color} {row['Status']}")
                r6.write(row['HR Name'])
                
                # EDIT ACTION
                if r7.button("📝", key=f"edit_{idx}"):
                    st.session_state.edit_id = row['Reference_ID']
                    st.session_state.edit_index = idx

            # 4. EDIT MODAL (Appears when pencil is clicked)
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"Updating: {st.session_state.edit_id}")
                    edit_row = all_df[all_df['Reference_ID'] == st.session_state.edit_id].iloc[0]
                    
                    up_status = st.selectbox("Change Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], 
                                             index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(edit_row['Status']))
                    
                    up_feedback = st.text_area("Feedback", value=edit_row['Feedback'])
                    
                    # Manual Interview/Onboard Date Logic
                    up_int_date = edit_row['Interview Date']
                    up_join_date = edit_row['Joining Date']
                    up_sr_date = edit_row['SR Date']

                    if up_status == "Interviewed":
                        up_int_date = st.date_input("Actual Interview Date").strftime("%d-%m-%Y")
                    
                    if up_status == "Onboarded":
                        j_date = st.date_input("Final Joining Date")
                        up_join_date = j_date.strftime("%d-%m-%Y")
                        # SR Date Calculation
                        c_df = pd.DataFrame(client_sheet.get_all_records())
                        c_row = c_df[c_df['Client Name'] == edit_row['Client Name']]
                        days = int(c_row.iloc[0]['SR Days']) if not c_row.empty else 0
                        up_sr_date = (j_date + timedelta(days=days)).strftime("%d-%m-%Y")

                    if st.button("Save Changes"):
                        # Find Row in Sheet
                        # row_values search is safer
                        sheet_row = idx + 2 # Header is 1
                        cand_sheet.update_cell(sheet_row, 7, up_int_date)
                        cand_sheet.update_cell(sheet_row, 8, up_status)
                        cand_sheet.update_cell(sheet_row, 10, up_join_date)
                        cand_sheet.update_cell(sheet_row, 11, up_sr_date)
                        cand_sheet.update_cell(sheet_row, 12, up_feedback)
                        
                        st.success("Updated Successfully!")
                        del st.session_state.edit_id
                        st.rerun()
                    
                    if st.button("Cancel"):
                        del st.session_state.edit_id
                        st.rerun() 
