import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Red-Blue Gradient and Professional Look
st.markdown("""
    <style>
    /* Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Login & Headers */
    .main-title { color: white; text-align: center; font-size: 35px; font-weight: bold; margin-bottom: 0px; padding-top: 20px; }
    .sub-title { color: white; text-align: center; font-size: 22px; margin-bottom: 30px; font-weight: bold; }
    .company-header { color: white; font-size: 26px; font-weight: bold; line-height: 1.1; }
    .company-slogan { color: white; font-size: 16px; margin-bottom: 15px; }
    .welcome-text { color: white; font-size: 20px; font-weight: bold; margin-bottom: 5px; }
    
    /* Target Bar */
    .target-bar { 
        background-color: #1565c0; color: white; padding: 12px; 
        border-radius: 8px; font-weight: bold; margin-bottom: 20px; 
        border: 1px solid rgba(255,255,255,0.3);
    }
    
    /* Table Styling */
    .data-header { 
        background-color: rgba(255,255,255,0.1); color: white; 
        font-weight: bold; padding: 10px; border-bottom: 2px solid white;
        text-align: center; font-size: 13px;
    }
    .white-container { background-color: white; padding: 20px; border-radius: 10px; }
    
    /* Input Boxes Customization */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        border-radius: 5px !important;
    }
    input, select, textarea {
        color: #0d47a1 !important;
        font-weight: bold !important;
    }
    label { color: white !important; font-weight: bold !important; }
    
    /* Buttons */
    .stButton>button { border-radius: 5px; font-weight: bold; }
    .st-emotion-cache-12fmjuu { color: #0d47a1 !important; } /* Fix for dark blue text in white boxes */
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
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
    log_sheet = sh.worksheet("Activity_Logs")
except Exception as e:
    st.error(f"⚠️ Database Connection Error: {e}")
    st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

def log_activity(user, action, candidate, details):
    ts = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    log_sheet.append_row([ts, user, action, candidate, details])

# --- 4. SESSION INITIALIZATION ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_data' not in st.session_state: st.session_state.user_data = None

# --- 5. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.3, 1])
    with col_m:
        with st.container():
            st.markdown('<div style="background-color:rgba(255,255,255,0.1); padding:30px; border-radius:15px; border: 1px solid white;">', unsafe_allow_html=True)
            u_mail = st.text_input("Email ID", placeholder="Enter your registered mail")
            u_pass = st.text_input("Password", type="password", placeholder="Enter your password")
            col_rem, col_show = st.columns(2)
            with col_rem: st.checkbox("Remember me")
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("❌ Incorrect username or password")
            
            st.markdown("<p style='text-align:center; color:white; font-size:12px;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 6. DASHBOARD (LOGGED IN) ---
u = st.session_state.user_data

# Header Layout
h_left, h_mid, h_right = st.columns([3, 3, 2])

with h_left:
    st.markdown("<div class='company-header'>Takecare Manpower Service Pvt Ltd</div>", unsafe_allow_html=True)
    st.markdown("<div class='company-slogan'>Successful HR Firm</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='welcome-text'>Welcome back, {u['Username']}!</div>", unsafe_allow_html=True)

with h_right:
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1.2])
    with btn_col3:
        if st.button("Log out", type="secondary"):
            st.session_state.logged_in = False
            st.rerun()
    with btn_col2:
        if u['Role'] in ["ADMIN", "TL"]:
            show_filter = st.button("🔍 Filter")
        else: show_filter = False

with h_mid:
    search_q = st.text_input("SEARCH", placeholder="Search anything in this data sheet...", label_visibility="collapsed")

st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

# --- 7. NEW SHORTLIST DIALOG ---
@st.dialog("➕ Add New Candidate Shortlist")
def new_shortlist_popup():
    c_master = pd.DataFrame(client_sheet.get_all_records())
    c_master.columns = c_master.columns.str.strip()
    
    col1, col2 = st.columns(2)
    with col1:
        ref_id = get_next_ref_id()
        st.write(f"**Reference ID:** {ref_id}")
        c_name = st.text_input("Candidate Name")
        c_phone = st.text_input("Contact Number")
        # Client filter based on User Master list or Full list for Admin
        if u['Role'] == "ADMIN":
            client_options = sorted(c_master['Client Name'].unique().tolist())
        else:
            allowed_clients = [x.strip() for x in str(u['Client_List']).split(',')]
            client_options = sorted([c for c in c_master['Client Name'].unique() if c in allowed_clients])
            
        sel_client = st.selectbox("Client Name", ["-- Select --"] + client_options)
    
    with col2:
        st.write(f"**Date:** {datetime.now().strftime('%d-%m-%Y')}")
        pos_list = c_master[c_master['Client Name'] == sel_client]['Position'].tolist() if sel_client != "-- Select --" else []
        sel_pos = st.selectbox("Position or Job Title", pos_list)
        comm_date = st.date_input("Commitment Date / Interview Date")
        status_init = st.selectbox("Status", ["Shortlisted"])
        
    feedback = st.text_area("Feedback (Optional)")
    send_wa = st.checkbox("Whatsapp Invite Link", value=True)
    
    btn_sub, btn_can = st.columns(2)
    if btn_sub.button("SUBMIT", use_container_width=True, type="primary"):
        if c_name and c_phone and sel_client != "-- Select --":
            today_str = datetime.now().strftime("%d-%m-%Y")
            comm_date_str = comm_date.strftime("%d-%m-%Y")
            
            # Save Data
            new_row = [ref_id, today_str, c_name, c_phone, sel_client, sel_pos, comm_date_str, status_init, u['Username'], "", "", feedback]
            cand_sheet.append_row(new_row)
            log_activity(u['Username'], "NEW_SHORTLIST", c_name, f"Added to {sel_client}")
            
            # WhatsApp Logic
            if send_wa:
                c_info = c_master[(c_master['Client Name'] == sel_client) & (c_master['Position'] == sel_pos)].iloc[0]
                msg = (f"Dear {c_name},\n\nCongratulations! We invite you for a Direct Interview.\n\n"
                       f"Reference: Takecare Manpower Services Pvt Ltd\n"
                       f"Position: {sel_pos}\n"
                       f"Interview Date: {comm_date_str}\n"
                       f"Interview Time: 10.30 AM\n"
                       f"Interview Venue: {c_info['Address']}\n"
                       f"Map Location: {c_info['Map Link']}\n"
                       f"Contact Person: {c_info['Contact Person']}\n\n"
                       f"Please let me know when you arrive. All the best!\n\n"
                       f"Regards,\n{u['Username']}\nTakecare HR Team")
                wa_url = f"https://wa.me/91{c_phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={wa_url}">', unsafe_allow_html=True)
            
            st.success("Candidate Shortlisted!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Please fill required fields!")

    if btn_can.button("CANCEL", use_container_width=True):
        st.rerun()

# Floating New Shortlist Button
_, col_new = st.columns([5, 1])
with col_new:
    if st.button("+ New Shortlist", use_container_width=True, type="primary"):
        new_shortlist_popup()

# --- 8. DATA PROCESSING (FILTERING & AUTO-DELETE) ---
raw_data = cand_sheet.get_all_records()
if not raw_data:
    st.info("No records found in database.")
    st.stop()

df = pd.DataFrame(raw_data)
df.columns = df.columns.str.strip()

# Access Control
if u['Role'] == "RECRUITER":
    df = df[df['HR Name'] == u['Username']]
elif u['Role'] == "TL":
    users_df = pd.DataFrame(user_sheet.get_all_records())
    team = users_df[users_df['Report_To'] == u['Username']]['Username'].tolist()
    df = df[df['HR Name'].isin(team + [u['Username']])]

# Auto-Delete Visual Logic (Remove from UI only)
today = datetime.now()
df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
df['Interview Date DT'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')

# Logic: Shortlisted > 7 days, Interviewed/Selected/Rejected > 30 days, Left/Not Joined > 3 days
df = df[~( (df['Status'] == 'Shortlisted') & (df['Shortlisted Date DT'] < today - timedelta(days=7)) )]
df = df[~( (df['Status'].isin(['Interviewed', 'Selected', 'Rejected', 'Hold'])) & (df['Interview Date DT'] < today - timedelta(days=30)) )]
df = df[~( (df['Status'].isin(['Left', 'Not Joined'])) & (df['Interview Date DT'] < today - timedelta(days=3)) )]

# --- 9. ATS TRACKING TABLE ---
st.markdown("<div style='background-color: white; border-radius: 10px; padding: 10px;'>", unsafe_allow_html=True)
t_cols = st.columns([0.7, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.4])
headers = ["Ref ID", "Candidate", "Contact", "Job Title", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit"]
for col, h in zip(t_cols, headers):
    col.markdown(f"<div class='data-header' style='color:black;'>{h}</div>", unsafe_allow_html=True)

for idx, row in df.iterrows():
    if search_q and search_q.lower() not in str(row).lower(): continue
    
    r_cols = st.columns([0.7, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.4])
    r_cols[0].write(row['Reference_ID'])
    r_cols[1].write(row['Candidate Name'])
    r_cols[2].write(row['Contact Number'])
    r_cols[3].write(row['Job Title'])
    r_cols[4].write(row['Interview Date'])
    
    # Status Color Logic
    status_color = "#0d47a1"
    if row['Status'] == "Selected": status_color = "green"
    elif row['Status'] == "Rejected": status_color = "red"
    elif row['Status'] == "Onboarded": status_color = "#1565c0"
    
    r_cols[5].markdown(f"<span style='color:{status_color}; font-weight:bold;'>{row['Status']}</span>", unsafe_allow_html=True)
    r_cols[6].write(row['Joining Date'])
    r_cols[7].write(row['SR Date'])
    r_cols[8].write(row['HR Name'])
    
    if r_cols[9].button("📝", key=f"edit_{row['Reference_ID']}"):
        st.session_state.active_edit = row['Reference_ID']

st.markdown("</div>", unsafe_allow_html=True)

# --- 10. EDIT STATUS DIALOG ---
if 'active_edit' in st.session_state:
    @st.dialog(f"Update Status - {st.session_state.active_edit}")
    def edit_popup():
        curr_id = st.session_state.active_edit
        row_data = df[df['Reference_ID'] == curr_id].iloc[0]
        
        st.write(f"Candidate: **{row_data['Candidate Name']}** | {row_data['Contact Number']}")
        
        new_stat = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success", "Not Joined"])
        
        upd_date = None
        if new_stat in ["Interviewed", "Onboarded"]:
            label = "Interview Date" if new_stat == "Interviewed" else "Joining Date"
            upd_date = st.date_input(label)
            
        new_feed = st.text_input("Feedback Update", value=row_data['Feedback'])
        
        col_s1, col_s2 = st.columns(2)
        if col_s1.button("SUBMIT UPDATE", type="primary"):
            # Find index in Google Sheet
            all_rows = cand_sheet.get_all_records()
            gs_idx = next(i for i, r in enumerate(all_rows) if r['Reference_ID'] == curr_id) + 2
            
            # Update Status & Feedback
            cand_sheet.update_cell(gs_idx, 8, new_stat)
            cand_sheet.update_cell(gs_idx, 12, new_feed)
            
            if new_stat == "Interviewed":
                cand_sheet.update_cell(gs_idx, 7, upd_date.strftime("%d-%m-%Y"))
            
            if new_stat == "Onboarded":
                j_date_str = upd_date.strftime("%d-%m-%Y")
                cand_sheet.update_cell(gs_idx, 10, j_date_str)
                # SR Date calculation
                c_m = pd.DataFrame(client_sheet.get_all_records())
                c_m.columns = c_m.columns.str.strip()
                sr_days = c_m[c_m['Client Name'] == row_data['Client Name']]['SR Days'].values[0]
                sr_date = (upd_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                cand_sheet.update_cell(gs_idx, 11, sr_date)
            
            log_activity(u['Username'], "STATUS_CHANGE", row_data['Candidate Name'], f"Changed to {new_stat}")
            del st.session_state.active_edit
            st.success("Updated Successfully!")
            time.sleep(1)
            st.rerun()
            
        if col_s2.button("CANCEL"):
            del st.session_state.active_edit
            st.rerun()
            
    edit_popup()
