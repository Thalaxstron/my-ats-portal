import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# CSS for Red-Blue Gradient & Styling
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    .main-title { color: white; text-align: center; font-size: 38px; font-weight: bold; margin-bottom: 0px; text-transform: uppercase; }
    .login-header { color: white; text-align: center; font-size: 24px; margin-bottom: 20px; font-weight: bold; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 15px; text-align: center; }
    
    /* Input Boxes: White background with Blue text */
    input, select, textarea, div[data-baseweb="select"] > div { 
        background-color: white !important; 
        color: #0d47a1 !important; 
        font-weight: bold !important; 
    }
    label { color: white !important; font-weight: bold !important; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
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

# --- 4. LOGIN LOGIC ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-header'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            show_pass = st.checkbox("Show Password") # Sidebar toggle alternative inside box
            remember = st.checkbox("Remember Me")
            
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.markdown("<p style='text-align:center; color:white;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)

else:
    # --- 5. DASHBOARD (LOGGED IN) ---
    u = st.session_state.user_data
    
    # Header Section
    h_col1, h_col2, h_col3 = st.columns([3, 2, 1])
    h_col1.markdown(f"### TAKECARE MANPOWER SERVICES PVT LTD")
    h_col2.markdown(f"### Welcome back, {u['Username']}!")
    if h_col3.button("Log out"): 
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # --- NEW SHORTLIST DIALOG ---
    @st.dialog("➕ Add New Candidate Shortlist")
    def new_entry_popup():
        # Step 1: Pre-fetch data
        cl_df = pd.DataFrame(client_sheet.get_all_records())
        cl_df.columns = cl_df.columns.str.strip() # Space issue fix
        
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            sel_client = st.selectbox("Client Name", sorted(cl_df['Client Name'].unique().tolist()))
        
        with c2:
            positions = cl_df[cl_df['Client Name'] == sel_client]['Position'].tolist()
            sel_pos = st.selectbox("Position", positions)
            comm_date = st.date_input("Commitment Date", datetime.now())
            status = st.selectbox("Status", ["Shortlisted"])
        
        feedback = st.text_area("Feedback (Optional)")
        send_wa = st.checkbox("Send WhatsApp Invite Link", value=True)

        if st.button("SUBMIT"):
            if name and phone:
                ref_id = get_next_ref_id()
                today = datetime.now().strftime("%d-%m-%Y")
                c_date_str = comm_date.strftime("%d-%m-%Y")
                
                # WhatsApp Logic - FIXED KEYERROR
                if send_wa:
                    c_info = cl_df[(cl_df['Client Name'] == sel_client) & (cl_df['Position'] == sel_pos)].iloc[0]
                    # Using get() or direct key with space handling
                    addr = c_info.get('Address', 'Address N/A')
                    mlink = c_info.get('Map Link', 'N/A')
                    cpers = c_info.get('Contact Person', 'N/A')
                    
                    msg = f"Dear {name},\nCongratulations! Invite for Interview.\n\nPosition: {sel_pos}\nRef: Takecare Manpower\nDate: {c_date_str}\nTime: 10.30 AM\nVenue: {addr}\nMap: {mlink}\nContact: {cpers}\n\nPlease let me know when you arrive. All the best!\n\nRegards,\n{u['Username']}\nTakecare HR Team"
                    wa_url = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank">📲 Open WhatsApp to Send</a>', unsafe_allow_html=True)

                # Save to Sheet
                cand_sheet.append_row([ref_id, today, name, phone, sel_client, sel_pos, c_date_str, "Shortlisted", u['Username'], "", "", feedback])
                st.success("Shortlist Saved Successfully!")
                st.rerun()

    # --- DASHBOARD ACTIONS ---
    btn_col, search_col = st.columns([4, 1])
    if btn_col.button("+ New Shortlist"): new_entry_popup()
    search_q = search_col.text_input("🔍 Search Anything")

    # --- 6. DATA TABLE & AUTO-DELETE ---
    raw_df = pd.DataFrame(cand_sheet.get_all_records())
    if not raw_df.empty:
        raw_df.columns = raw_df.columns.str.strip()
        
        # Role Restrictions
        if u['Role'] == "RECRUITER":
            df = raw_df[raw_df['HR Name'] == u['Username']]
        elif u['Role'] == "TL":
            users = pd.DataFrame(user_sheet.get_all_records())
            team = users[users['Report_To'] == u['Username']]['Username'].tolist()
            df = raw_df[raw_df['HR Name'].isin(team + [u['Username']])]
        else:
            df = raw_df

        # Filter: Shortlisted > 7 Days Auto-Hide
        df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        df = df[~((df['Status'] == 'Shortlisted') & (df['Shortlisted Date DT'] < datetime.now() - timedelta(days=7)))]

        # UI Table
        st.markdown("---")
        t_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 0.5])
        headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboarded", "SR Date", "Edit"]
        for col, h in zip(t_cols, headers): col.write(f"**{h}**")

        for i, row in df.iterrows():
            if search_q.lower() not in str(row).lower(): continue
            r_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 0.5])
            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            if r_cols[8].button("📝", key=f"e_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

    # --- 7. EDIT SIDEBAR ---
    if 'edit_id' in st.session_state:
        with st.sidebar:
            st.header(f"Update: {st.session_state.edit_id}")
            row_data = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
            
            new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Not Joined"])
            new_fb = st.text_area("Feedback", value=row_data['Feedback'])
            
            # Onboarded Logic
            if new_st == "Onboarded":
                j_date = st.date_input("Joining Date")
                cl_master = pd.DataFrame(client_sheet.get_all_records())
                cl_master.columns = cl_master.columns.str.strip()
                sr_val = cl_master[cl_master['Client Name'] == row_data['Client Name']]['SR Days'].values[0]
                sr_date = (j_date + timedelta(days=int(sr_val))).strftime("%d-%m-%Y")
                st.info(f"SR Date: {sr_date}")

            if st.button("UPDATE NOW"):
                all_recs = cand_sheet.get_all_records()
                idx = next(i for i, r in enumerate(all_recs) if r['Reference_ID'] == st.session_state.edit_id) + 2
                
                cand_sheet.update_cell(idx, 8, new_st)
                cand_sheet.update_cell(idx, 12, new_fb)
                if new_st == "Onboarded":
                    cand_sheet.update_cell(idx, 10, j_date.strftime("%d-%m-%Y"))
                    cand_sheet.update_cell(idx, 11, sr_date)
                
                st.success("Updated!")
                del st.session_state.edit_id
                st.rerun()
