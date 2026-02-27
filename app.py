import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important; background-attachment: fixed; }
    .company-name { color: white; font-size: 28px; font-weight: bold; line-height: 1.2; }
    .company-sub { color: white; font-size: 18px; margin-bottom: 10px; }
    .welcome-text { color: white; font-size: 22px; font-weight: bold; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    
    /* Input Styling */
    input, select, textarea, div[data-baseweb="select"] > div { 
        background-color: white !important; 
        color: #0d47a1 !important; 
        font-weight: bold !important; 
    }
    label { color: white !important; font-weight: bold !important; }
    .data-header { color: white; font-weight: bold; border-bottom: 2px solid white; padding: 5px; font-size: 14px; text-align: center; }
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

# --- 3. HELPER: REFERENCE ID GENERATOR ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if val.startswith("E") and val[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. LOGIN LOGIC ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
    st.stop()

# --- 5. DASHBOARD ---
u = st.session_state.user_data
t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns([2.5, 2.5, 2, 1, 0.8])

with t_col1:
    st.markdown("<div class='company-name'>Takecare Manpower Service Pvt Ltd</div><div class='company-sub'>Successful HR Firm</div>", unsafe_allow_html=True)
with t_col2: 
    st.markdown(f"<div class='welcome-text'>Welcome back, {u['Username']}!</div>", unsafe_allow_html=True)
with t_col3: 
    search_q = st.text_input("Search", label_visibility="collapsed", placeholder="Search anything in data...")
with t_col4:
    filter_val = st.selectbox("Filter", ["All", "Client Wise", "Recruiter Wise"], label_visibility="collapsed") if u['Role'] != "RECRUITER" else "All"
with t_col5:
    if st.button("Log out"): st.session_state.logged_in = False; st.rerun()

st.markdown("<div class='target-bar'>Target for Today: 📞 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

# --- 6. ADMIN: CLIENT MASTER MANAGEMENT ---
if u['Role'] == "ADMIN":
    with st.expander("🏢 Manage Client Master (Admin Only)"):
        # Add New
        st.subheader("Add New Client/Position")
        ac1, ac2, ac3 = st.columns(3)
        c_name_n = ac1.text_input("Client Name")
        c_pos_n = ac2.text_input("Position Name")
        c_hr_n = ac3.text_input("HR Name")
        ac4, ac5, ac6 = st.columns([2, 1, 1])
        c_addr_n = ac4.text_input("Full Address")
        c_map_n = ac5.text_input("Map Link")
        c_sr_n = ac6.number_input("SR Days", value=60)
        
        if st.button("SAVE CLIENT"):
            client_sheet.append_row([c_name_n, c_pos_n, c_addr_n, c_map_n, c_hr_n, str(c_sr_n)])
            st.success("Client Data Saved!")
            st.rerun()
        
        st.markdown("---")
        # Delete Existing
        st.subheader("Delete Client Entry")
        cl_df_manage = pd.DataFrame(client_sheet.get_all_records())
        cl_df_manage.columns = cl_df_manage.columns.str.strip()
        del_target = st.selectbox("Select Client/Position to Delete", 
                                  cl_df_manage['Client Name'] + " - " + cl_df_manage['Position'])
        if st.button("DELETE SELECTED", type="primary"):
            row_idx = cl_df_manage.index[
                (cl_df_manage['Client Name'] + " - " + cl_df_manage['Position']) == del_target
            ][0] + 2
            client_sheet.delete_rows(int(row_idx))
            st.warning("Client Deleted!")
            st.rerun()

# --- 7. NEW SHORTLIST DIALOG ---
@st.dialog("➕ Add New Candidate Shortlist")
def new_entry_dialog():
    cl_df = pd.DataFrame(client_sheet.get_all_records())
    cl_df.columns = cl_df.columns.str.strip()
    c1, c2 = st.columns(2)
    name = c1.text_input("Candidate Name")
    phone = c1.text_input("Contact Number")
    sel_client = c1.selectbox("Select Client", sorted(cl_df['Client Name'].unique().tolist()))
    
    pos_options = cl_df[cl_df['Client Name'] == sel_client]['Position'].tolist()
    sel_pos = c2.selectbox("Select Position", pos_options)
    c_date = c2.date_input("Interview Commitment Date")
    feedback = st.text_area("Initial Feedback")
    send_wa = st.checkbox("Send WhatsApp Invite", value=True)
    
    if st.button("SUBMIT SHORTLIST", use_container_width=True):
        if name and phone:
            ref_id = get_next_ref_id()
            today = datetime.now().strftime("%d-%m-%Y")
            c_info = cl_df[(cl_df['Client Name'] == sel_client) & (cl_df['Position'] == sel_pos)].iloc[0]
            
            if send_wa:
                msg = f"Dear {name},\nCongratulations! Invite for Interview.\n\nPosition: {sel_pos}\nDate: {c_date}\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nRegards,\n{u['Username']}\nTakecare HR Team"
                wa_link = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wa_link}" target="_blank">📲 Open WhatsApp to Send</a>', unsafe_allow_html=True)
            
            cand_sheet.append_row([ref_id, today, name, phone, sel_client, sel_pos, c_date.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", feedback])
            st.success("Candidate Added!")
            st.rerun()

# New Shortlist Button
_, b_col = st.columns([5, 1])
if b_col.button("+ New Shortlist", use_container_width=True): new_entry_dialog()

# --- 8. DATA TABLE DISPLAY ---
raw_df = pd.DataFrame(cand_sheet.get_all_records())
if not raw_df.empty:
    raw_df.columns = raw_df.columns.str.strip()
    
    # Access Rules
    if u['Role'] == "RECRUITER":
        df = raw_df[raw_df['HR Name'] == u['Username']]
    elif u['Role'] == "TL":
        users = pd.DataFrame(user_sheet.get_all_records())
        team = users[users['Report_To'] == u['Username']]['Username'].tolist()
        df = raw_df[raw_df['HR Name'].isin(team + [u['Username']])]
    else:
        df = raw_df

    # Auto-Delete Visual Logic (7 days for Shortlisted)
    today_dt = datetime.now()
    df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df = df[~((df['Status'] == 'Shortlisted') & (df['Shortlisted Date DT'] < today_dt - timedelta(days=7)))]

    st.markdown("---")
    cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.5])
    headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit"]
    for col, h in zip(cols, headers): col.markdown(f"<div class='data-header'>{h}</div>", unsafe_allow_html=True)

    for idx, row in df.iterrows():
        if search_q.lower() not in str(row).lower(): continue
        r_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.5])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        if r_cols[9].button("📝", key=f"e_{row['Reference_ID']}"):
            st.session_state.edit_id = row['Reference_ID']

# --- 9. EDIT ACTION (SIDEBAR) ---
if 'edit_id' in st.session_state:
    with st.sidebar:
        st.header(f"Edit {st.session_state.edit_id}")
        curr = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
        
        new_status = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Not Joined"])
        new_feedback = st.text_area("Feedback Update", value=curr['Feedback'])
        
        if new_status == "Onboarded":
            j_date = st.date_input("Joining Date")
            cl_m = pd.DataFrame(client_sheet.get_all_records())
            cl_m.columns = cl_m.columns.str.strip()
            sr_val = cl_m[cl_m['Client Name'] == curr['Client Name']]['SR Days'].values[0]
            sr_date = (j_date + timedelta(days=int(sr_val))).strftime("%d-%m-%Y")
            st.info(f"Auto SR Date: {sr_date}")

        if st.button("SAVE UPDATES"):
            all_recs = cand_sheet.get_all_records()
            gs_idx = next(i for i, r in enumerate(all_recs) if r['Reference_ID'] == st.session_state.edit_id) + 2
            
            cand_sheet.update_cell(gs_idx, 8, new_status)
