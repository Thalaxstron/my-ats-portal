import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & RESPONSIVE UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Responsive Design & Professional Look
st.markdown("""
    <style>
    /* Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Responsive Text & Headers */
    .main-title { color: white; text-align: center; font-size: clamp(24px, 5vw, 40px); font-weight: bold; margin-bottom: 5px; padding-top: 20px; }
    .sub-title { color: white; text-align: center; font-size: clamp(18px, 3vw, 24px); margin-bottom: 30px; font-weight: bold; }
    .company-header { color: white; font-size: 24px; font-weight: bold; line-height: 1.1; }
    .company-slogan { color: white; font-size: 14px; margin-bottom: 10px; opacity: 0.9; }
    .welcome-text { color: white; font-size: 18px; font-weight: bold; margin-bottom: 5px; }
    
    /* Target Bar */
    .target-bar { 
        background-color: #1565c0; color: white; padding: 12px; 
        border-radius: 8px; font-weight: bold; margin-bottom: 20px; 
        border: 1px solid rgba(255,255,255,0.3); text-align: center;
    }
    
    /* Form Inputs & White Boxes */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea {
        background-color: white !important;
        border-radius: 8px !important;
    }
    input, select, textarea {
        color: #0d47a1 !important;
        font-weight: bold !important;
        cursor: text !important;
    }
    label { color: white !important; font-weight: bold !important; }

    /* ATS Tracking Container */
    .ats-container {
        background-color: white; 
        border-radius: 12px; 
        padding: 15px; 
        max-height: 600px; 
        overflow-y: auto;
    }
    
    /* Buttons */
    .stButton>button { border-radius: 8px; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    
    /* WhatsApp Link Style */
    .wa-link {
        background-color: #25D366; color: white !important;
        padding: 12px; border-radius: 8px; text-decoration: none;
        display: block; text-align: center; font-weight: bold; margin-top: 10px;
    }
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
except Exception as e:
    st.error(f"⚠️ Connection Error: {e}"); st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:04d}" if valid_ids else "E0001"

# --- 4. LOGIN LOGIC ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'show_pass' not in st.session_state: st.session_state.show_pass = False

if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.5, 1])
    with col_m:
        with st.container():
            st.markdown('<div style="background-color:rgba(255,255,255,0.1); padding:40px; border-radius:20px; border: 1px solid white;">', unsafe_allow_html=True)
            u_mail = st.text_input("Email ID", placeholder="Enter registered mail")
            
            # Password with Show/Hide
            pass_type = "default" if st.session_state.show_pass else "password"
            u_pass = st.text_input("Password", type=pass_type)
            if st.checkbox("Show Password"): st.session_state.show_pass = not st.session_state.show_pass
            
            st.checkbox("Remember me")
            
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("❌ Incorrect username or password")
            
            st.markdown("<p style='text-align:center; color:white; font-size:13px; margin-top:15px;'>Forgot password? Contact Admin</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 5. DASHBOARD LAYOUT ---
u = st.session_state.user_data
h_left, h_mid, h_right = st.columns([3, 2, 2])

with h_left:
    st.markdown("<div class='company-header'>Takecare Manpower Service Pvt Ltd</div>", unsafe_allow_html=True)
    st.markdown("<div class='company-slogan'>Successful HR Firm</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='welcome-text'>Welcome back, {u['Username']}!</div>", unsafe_allow_html=True)

with h_right:
    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
    if btn_c3.button("Logout"): 
        st.session_state.logged_in = False
        st.rerun()
    if u['Role'] in ["ADMIN", "TL"]:
        if btn_c2.button("🔍 Filter"): st.session_state.filter_active = not st.session_state.get('filter_active', False)
    
    # Search Bar (Top Left of Logout)
    search_q = st.text_input("SEARCH", placeholder="Search...", label_visibility="collapsed")

st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

# --- 6. NEW SHORTLIST (POP-UP DIALOG) ---
@st.dialog("➕ Add New Candidate Shortlist")
def new_candidate():
    c_master = pd.DataFrame(client_sheet.get_all_records())
    
    row1_c1, row1_c2 = st.columns(2)
    with row1_c1:
        ref_id = get_next_ref_id()
        st.info(f"Reference ID: {ref_id}")
        name = st.text_input("Candidate Name")
        phone = st.text_input("Contact Number")
        client_list = sorted(c_master['Client Name'].unique().tolist())
        sel_client = st.selectbox("Client Name", ["-- Select --"] + client_list)

    with row1_c2:
        st.write(f"Shortlisted Date: {datetime.now().strftime('%d-%m-%Y')}")
        pos_list = c_master[c_master['Client Name'] == sel_client]['Position'].tolist() if sel_client != "-- Select --" else []
        sel_pos = st.selectbox("Position", pos_list)
        comm_date = st.date_input("Commitment Date")
        st.selectbox("Status", ["Shortlisted"], disabled=True)

    feedback = st.text_area("Feedback (Optional)")
    wa_check = st.checkbox("Whatsapp Invite Link", value=True)
    
    btn_sub, btn_can = st.columns(2)
    if btn_sub.button("SUBMIT", use_container_width=True, type="primary"):
        if name and phone and sel_client != "-- Select --":
            # Save to Sheet
            today = datetime.now().strftime("%d-%m-%Y")
            new_row = [ref_id, today, name, phone, sel_client, sel_pos, comm_date.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", feedback]
            cand_sheet.append_row(new_row)
            
            if wa_check:
                c_info = c_master[c_master['Client Name'] == sel_client].iloc[0]
                msg = (f"Dear {name},\n\nCongratulations! We invite you for a Direct Interview.\n\n"
                       f"Reference: Takecare Manpower Services Pvt Ltd\n"
                       f"Position: {sel_pos}\n"
                       f"Interview Date: {comm_date.strftime('%d-%m-%Y')}\n"
                       f"Venue: {c_info.get('Address', 'Office')}\n"
                       f"Map: {c_info.get('Map Link', '')}\n"
                       f"Contact: {c_info.get('Contact Person', '')}\n\n"
                       f"Regards,\n{u['Username']}\nTakecare HR Team")
                wa_url = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-link">📤 Click to Send WhatsApp Invite</a>', unsafe_allow_html=True)
                time.sleep(2)
            st.success("Shortlisted Successfully!")
            st.rerun()
    
    if btn_can.button("CANCEL", use_container_width=True): st.rerun()

# Floating New Shortlist Button
_, col_new = st.columns([5, 1])
with col_new:
    if st.button("+ New Shortlist", type="primary", use_container_width=True): new_candidate()

# --- 7. FILTER LOGIC (ADMIN/TL) ---
if st.session_state.get('filter_active', False):
    with st.container():
        st.markdown('<div style="background-color:white; padding:15px; border-radius:10px; margin-bottom:15px;">', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)
        with f1: f_client = st.selectbox("Client", ["All"] + sorted(pd.DataFrame(client_sheet.get_all_records())['Client Name'].tolist()))
        with f2: f_user = st.selectbox("Recruiter", ["All"] + sorted(pd.DataFrame(user_sheet.get_all_records())['Username'].tolist()))
        with f3: f_date = st.date_input("Interview Date Range", [])
        with f4: 
            if st.button("Apply Filter"): st.session_state.filters = {'c': f_client, 'u': f_user, 'd': f_date}
            if st.button("Close"): st.session_state.filter_active = False; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- 8. ATS DATA PROCESSING (AUTO-DELETE LOGIC) ---
df = pd.DataFrame(cand_sheet.get_all_records())
df.columns = df.columns.str.strip()

# Access Control
if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
elif u['Role'] == "TL":
    team = pd.DataFrame(user_sheet.get_all_records())
    team_list = team[team['Report_To'] == u['Username']]['Username'].tolist() + [u['Username']]
    df = df[df['HR Name'].isin(team_list)]

# Date Conversion for Logic
today = datetime.now()
df['SDate_DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
df['IDate_DT'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')

# Auto-Delete Filtering (UI Only)
df = df[~( (df['Status'] == 'Shortlisted') & (df['SDate_DT'] < today - timedelta(days=7)) )]
df = df[~( (df['Status'].isin(['Interviewed', 'Selected', 'Rejected', 'Hold'])) & (df['IDate_DT'] < today - timedelta(days=30)) )]
df = df[~( (df['Status'].isin(['Left', 'Not Joined'])) & (df['IDate_DT'] < today - timedelta(days=3)) )]

# --- 9. ATS TRACKING TABLE ---
st.markdown("<div class='ats-container'>", unsafe_allow_html=True)
if search_q:
    df = df[df.apply(lambda row: search_q.lower() in row.astype(str).str.lower().values, axis=1)]

# Table Display
cols = st.columns([0.8, 1.5, 1.2, 1.5, 1.2, 1.2, 1, 0.5])
headers = ["ID", "Candidate", "Phone", "Client", "Int. Date", "Status", "SR Date", "Edit"]
for col, h in zip(cols, headers): col.markdown(f"<b style='color:#0d47a1'>{h}</b>", unsafe_allow_html=True)

for idx, row in df.iterrows():
    r_cols = st.columns([0.8, 1.5, 1.2, 1.5, 1.2, 1.2, 1, 0.5])
    r_cols[0].write(row['Reference_ID'])
    r_cols[1].write(row['Candidate Name'])
    r_cols[2].write(row['Contact Number'])
    r_cols[3].write(row['Client Name'])
    r_cols[4].write(row['Interview Date'])
    r_cols[5].write(row['Status'])
    r_cols[6].write(row['SR Date'])
    if r_cols[7].button("📝", key=f"ed_{row['Reference_ID']}"):
        st.session_state.active_edit = row['Reference_ID']

st.markdown("</div>", unsafe_allow_html=True)

# --- 10. EDIT STATUS & FEEDBACK ---
if 'active_edit' in st.session_state:
    @st.dialog("Update Candidate Status")
    def edit_status():
        ref = st.session_state.active_edit
        row_data = df[df['Reference_ID'] == ref].iloc[0]
        
        st.write(f"Update for: **{row_data['Candidate Name']}**")
        new_stat = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success", "Not Joined"])
        
        upd_date = None
        if new_stat in ["Interviewed", "Onboarded"]:
            label = "Interview Date" if new_stat == "Interviewed" else "Onboarded Date"
            upd_date = st.date_input(label)
        
        new_feed = st.text_input("Feedback Update (Max 20 chars)", value=row_data['Feedback'][:20])
        
        c1, c2 = st.columns(2)
        if c1.button("SUBMIT UPDATE", type="primary"):
            all_rows = cand_sheet.get_all_records()
            gs_idx = next(i for i, r in enumerate(all_rows) if r['Reference_ID'] == ref) + 2
            
            cand_sheet.update_cell(gs_idx, 8, new_stat) # Status
            cand_sheet.update_cell(gs_idx, 12, new_feed) # Feedback
            
            if new_stat == "Interviewed":
                cand_sheet.update_cell(gs_idx, 7, upd_date.strftime("%d-%m-%Y"))
            elif new_stat == "Onboarded":
                cand_sheet.update_cell(gs_idx, 10, upd_date.strftime("%d-%m-%Y"))
                # SR Date Calculation
                c_master = pd.DataFrame(client_sheet.get_all_records())
                sr_days = c_master[c_master['Client Name'] == row_data['Client Name']]['SR Days'].values[0]
                sr_date = (upd_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                cand_sheet.update_cell(gs_idx, 11, sr_date)

            st.success("Updated!"); time.sleep(1); del st.session_state.active_edit; st.rerun()
        
        if c2.button("CANCEL"): del st.session_state.active_edit; st.rerun()

    edit_status()
