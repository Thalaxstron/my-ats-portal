
import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# Custom CSS for the Red-Blue Gradient Background & UI
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    [data-testid="stHeader"] { background: transparent; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .main-title { color: white; text-align: center; font-size: 40px; font-weight: bold; margin-bottom: 0px; }
    .sub-title { color: white; text-align: center; font-size: 25px; margin-bottom: 20px; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    /* White boxes with Blue text for inputs */
    input, select, textarea { color: #0d47a1 !important; font-weight: bold !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
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
    st.error(f"Database Error: {e}"); st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN LOGIC ---
if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            remember = st.checkbox("Remember Me")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip() # Fix for KeyError 'Role'
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

else:
    # --- 6. DASHBOARD (LOGGED IN) ---
    u_data = st.session_state.user_data
    
    # Header Section (Matching your image)
    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 2, 1.5, 0.5])
    with h_col1: st.subheader("TAKECARE") # Logo Placeholder
    with h_col2: st.markdown(f"### Welcome back, {u_data['Username']}!")
    with h_col4: 
        if st.button("Log out"): 
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # --- ACTION BUTTONS ---
    tab_list = ["Dashboard"]
    if u_data['Role'] == "ADMIN": tab_list.append("Client Master")
    
    # Floating '+' Button Logic via Dialog
    @st.dialog("➕ Add New Candidate Shortlist")
    def new_entry_popup():
        ref_id = get_next_ref_id()
        st.write(f"**Reference ID:** {ref_id}")
        
        c_name = st.text_input("Candidate Name")
        c_phone = st.text_input("Contact Number (WhatsApp)")
        
        c_master = pd.DataFrame(client_sheet.get_all_records())
        sel_client = st.selectbox("Client Name", ["-- Select --"] + sorted(c_master['Client Name'].unique().tolist()))
        
        # Position mapping
        pos_options = []
        if sel_client != "-- Select --":
            pos_options = c_master[c_master['Client Name'] == sel_client]['Position'].tolist()
        
        sel_pos = st.selectbox("Position", pos_options if pos_options else ["Select Client First"])
        comm_date = st.date_input("Commitment Date", datetime.now())
        feedback = st.text_area("Feedback")
        send_wa = st.checkbox("Send WhatsApp Invite Link", value=True)

        if st.button("SUBMIT"):
            if c_name and c_phone and sel_client != "-- Select --":
                today = datetime.now().strftime("%d-%m-%Y")
                c_date_str = comm_date.strftime("%d-%m-%Y")
                
                # Save to Data Sheet
                cand_sheet.append_row([ref_id, today, c_name, c_phone, sel_client, sel_pos, c_date_str, "Shortlisted", u_data['Username'], "", "", feedback])
                
                if send_wa:
                    # Fetch Client Details for WA Template
                    c_info = c_master[(c_master['Client Name'] == sel_client) & (c_master['Position'] == sel_pos)].iloc[0]
                    msg = f"Dear {c_name},\nCongratulations! Direct Interview Invite.\n\nPosition: {sel_pos}\nRef: Takecare Manpower\nDate: {c_date_str}\nTime: 10.30 AM\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nPlease let me know when you arrive. All the best!\n\nRegards,\n{u_data['Username']}\nTakecare HR Team"
                    wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank">📲 Open WhatsApp to Send</a>', unsafe_allow_html=True)
                
                st.success("Saved Successfully!")
                st.rerun()

    col_btn, col_search = st.columns([4, 1])
    with col_btn:
        if st.button("+ New Shortlist"): new_entry_popup()
    with col_search:
        search_query = st.text_input("🔍 Search")

    # --- 7. DATA TABLE & FILTERS ---
    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()

        # Role-Based Visibility
        if u_data['Role'] == "RECRUITER":
            df = df[df['HR Name'] == u_data['Username']]
        elif u_data['Role'] == "TL":
            users_df = pd.DataFrame(user_sheet.get_all_records())
            team = users_df[users_df['Report_To'] == u_data['Username']]['Username'].tolist()
            df = df[df['HR Name'].isin(team + [u_data['Username']])]

        # Auto-Delete Visual Logic
        now = datetime.now()
        df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        # Remove Shortlisted > 7 days
        df = df[~((df['Status'] == "Shortlisted") & (df['Shortlisted Date'] < now - timedelta(days=7)))]

        # Display Headers
        st.markdown("---")
        t_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 1, 0.5])
        headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboard", "SR Date", "Edit"]
        for col, h in zip(t_cols, headers): col.write(f"**{h}**")

        for idx, row in df.iterrows():
            # Search Filter
            if search_query.lower() not in str(row).lower(): continue
            
            r_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 1, 0.5])
            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            
            if r_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # --- 8. EDIT SIDEBAR ---
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.header(f"Update: {st.session_state.edit_id}")
            current_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
            
            new_status = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Not Joined"])
            new_feedback = st.text_area("Feedback", value=current_row['Feedback'])
            
            # Logic for Onboarded / SR Date
            if new_status == "Onboarded":
                join_date = st.date_input("Joining Date")
                # Calculate SR Date based on Client_Master days
                c_master = pd.DataFrame(client_sheet.get_all_records())
                sr_days = c_master[c_master['Client Name'] == current_row['Client Name']]['SR Days'].values[0]
                sr_date = (join_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                st.info(f"Calculated SR Date: {sr_date}")
            
            if st.button("Update Sheet"):
                # Find the row index in GSheet (idx + 2 because of header)
                gsheet_row_idx = df.index[df['Reference_ID'] == st.session_state.edit_id][0] + 2
                cand_sheet.update_cell(gsheet_row_idx, 8, new_status)
                cand_sheet.update_cell(gsheet_row_idx, 12, new_feedback)
                if new_status == "Onboarded":
                    cand_sheet.update_cell(gsheet_row_idx, 10, join_date.strftime("%d-%m-%Y"))
                    cand_sheet.update_cell(gsheet_row_idx, 11, sr_date)
                
                st.success("Updated!")
                del st.session_state.edit_id
                st.rerun()
