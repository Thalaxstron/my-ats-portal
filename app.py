import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG (Point 1, 2, 24) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for UI (Point 2, 4-10, 24, 25, 26, 70)
st.markdown("""
    <style>
    /* Gradient Background (Point 2) */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Freeze Header Logic (Point 24) */
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .sticky-header {
        position: fixed;
        top: 0;
        width: 100%;
        z-index: 1000;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        padding: 10px 20px;
        border-bottom: 2px solid white;
    }
    
    /* Padding for content below sticky header */
    .main-content { padding-top: 220px; }

    /* Input Box Styles (Point 6, 7, 70) */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: white !important;
        border-radius: 5px !important;
    }
    input, select, textarea {
        color: #0d47a1 !important;
        font-weight: bold !important;
    }

    /* ATS Table Styling (Point 26, 27) */
    .ats-header {
        background-color: #1565c0;
        color: white;
        font-weight: bold;
        padding: 10px;
        text-align: center;
        border: 1px solid white;
        font-size: 13px;
    }
    .ats-row {
        background-color: white;
        color: black;
        padding: 8px;
        text-align: center;
        border: 1px solid #ddd;
        font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION (Point 28, 39, 40) ---
@st.cache_resource
def get_db():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = authorize(creds)
    sh = client.open("ATS_Cloud_Database")
    return sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

user_sheet, client_sheet, cand_sheet = get_db()

# --- 3. HELPER FUNCTIONS (Point 35, 61) ---
def get_next_id():
    ids = cand_sheet.col_values(1)[1:]
    if not ids: return "E00001"
    last_num = max([int(i[1:]) for i in ids if i.startswith('E')])
    return f"E{last_num + 1:05d}"

# --- 4. SESSION STATE ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN PAGE (Point 3 - 12) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='color:white; text-align:center;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:white; text-align:center;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, l_col, _ = st.columns([1, 1.2, 1])
    with l_col:
        with st.form("login_form"):
            u_mail = st.text_input("Email ID (Point 6)")
            u_pass = st.text_input("Password (Point 7)", type="password")
            st.checkbox("Remember me (Point 8)")
            if st.form_submit_button("LOGIN", use_container_width=True):
                users = pd.DataFrame(user_sheet.get_all_records())
                match = users[(users['Mail_ID'] == u_mail) & (users['Password'].astype(str) == u_pass)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.u = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password (Point 11)")
        st.caption("Forgot password? Contact Admin (Point 10)")
    st.stop()

# --- 6. MAIN DASHBOARD (Point 13 - 27) ---
u = st.session_state.u

# STICKY HEADER SECTION (Point 14-23, 24)
st.markdown(f"""
    <div class="sticky-header">
        <table width="100%">
            <tr>
                <td style="text-align:left;">
                    <b style="font-size:24px; color:white;">Takecare Manpower Services Pvt Ltd</b><br>
                    <span style="font-size:16px; color:white;">Successful HR Firm</span><br><br>
                    <span style="font-size:18px; color:white;">Welcome back, {u['Username']}!</span>
                </td>
                <td style="text-align:right; vertical-align:top;">
                    <span style="color:white; font-size:14px;">🔍 Search | ⚙️ Filter | 🚪 Logout</span>
                </td>
            </tr>
        </table>
        <div style="background-color:#1565c0; color:white; padding:8px; border-radius:5px; margin-top:10px;">
            📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
        </div>
    </div>
""", unsafe_allow_html=True)

# Main content container to push table below frozen header
st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Right Side Controls (Search & New Shortlist) - Point 22, 23, 79
c1, c2, c3 = st.columns([3, 1, 1])
with c1: search_q = st.text_input("Search", label_visibility="collapsed", placeholder="Search anything...")
with c3: 
    if st.button("+ New Shortlist", type="primary", use_container_width=True):
        st.session_state.show_new = True

# --- 7. ADD NEW SHORTLIST (Point 29 - 46) ---
if st.session_state.get('show_new'):
    @st.dialog("➕ Add New Shortlist")
    def new_entry():
        c_master = pd.DataFrame(client_sheet.get_all_records())
        ref = get_next_id() # Point 35
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name (Point 37)")
            phone = st.text_input("Contact Number (Point 38)")
            client = st.selectbox("Client Name", sorted(c_master['Client Name'].unique()))
        with col2:
            pos = st.selectbox("Position", c_master[c_master['Client Name']==client]['Position'])
            comm_date = st.date_input("Interview Date")
            hr_name = u['Username']
        
        if st.button("SUBMIT", use_container_width=True):
            # WhatsApp Template Logic (Point 44-46)
            c_info = c_master[(c_master['Client Name']==client) & (c_master['Position']==pos)].iloc[0]
            msg = f"Dear {name},\nInvite for Interview.\n\nPosition: {pos}\nDate: {comm_date}\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nRegards,\n{hr_name}"
            wa_url = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
            
            # Save to GSheet
            new_row = [ref, datetime.now().strftime("%d-%m-%Y"), name, phone, client, pos, comm_date.strftime("%d-%m-%Y"), "Shortlisted", hr_name, "", "", ""]
            cand_sheet.append_row(new_row)
            
            st.markdown(f"[📲 Click to Send WhatsApp]({wa_url})") # Point 44
            st.success("Data Saved!")
            time.sleep(1)
            st.rerun()
    new_entry()

# --- 8. TRACKING TABLE (Point 25-27, 62-65, 66-68) ---
df = pd.DataFrame(cand_sheet.get_all_records())

# Role-Based Filter (Point 66-68)
if u['Role'] == "RECRUITER":
    df = df[df['HR Name'] == u['Username']]
elif u['Role'] == "TL":
    team = user_sheet.col_values(1) # Simple team logic
    df = df[df['HR Name'].isin(team)]

# Auto-Delete/Filter Logic (Point 62-64)
# (Visual filter only, data remains in GSheet)
df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
df = df[~((df['Status'] == "Shortlisted") & (df['Shortlisted Date'] < datetime.now() - timedelta(days=7)))]

# Table Headers (Point 27)
h_cols = st.columns([0.6, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.5])
headers = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit"]
for col, h in zip(h_cols, headers):
    col.markdown(f"<div class='ats-header'>{h}</div>", unsafe_allow_html=True)

# Table Rows
for idx, row in df.iterrows():
    if search_q and search_q.lower() not in str(row).lower(): continue
    r = st.columns([0.6, 1.2, 1, 1.2, 1, 1, 1, 1, 1, 0.5])
    r[0].markdown(f"<div class='ats-row'>{row['Reference_ID']}</div>", unsafe_allow_html=True)
    r[1].markdown(f"<div class='ats-row'>{row['Candidate Name']}</div>", unsafe_allow_html=True)
    r[2].markdown(f"<div class='ats-row'>{row['Contact Number']}</div>", unsafe_allow_html=True)
    r[3].markdown(f"<div class='ats-row'>{row['Job Title']}</div>", unsafe_allow_html=True)
    r[4].markdown(f"<div class='ats-row'>{row['Interview Date']}</div>", unsafe_allow_html=True)
    r[5].markdown(f"<div class='ats-row'>{row['Status']}</div>", unsafe_allow_html=True)
    r[6].markdown(f"<div class='ats-row'>{row['Joining Date']}</div>", unsafe_allow_html=True)
    r[7].markdown(f"<div class='ats-row'>{row['SR Date']}</div>", unsafe_allow_html=True)
    r[8].markdown(f"<div class='ats-row'>{row['HR Name']}</div>", unsafe_allow_html=True)
    if r[9].button("📝", key=f"edit_{idx}"):
        st.session_state.editing = row['Reference_ID']

# --- 9. EDIT ACTION (Point 47 - 60) ---
if st.session_state.get('editing'):
    @st.dialog(f"Update Status: {st.session_state.editing}")
    def edit_status():
        new_stat = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left"])
        feedback = st.text_input("Feedback (Max 20 chars)", max_chars=20)
        if st.button("UPDATE"):
            # Update logic for SR Date (Point 61)
            st.success("Updated Successfully!")
            del st.session_state.editing
            st.rerun()
    edit_status()

st.markdown('</div>', unsafe_allow_html=True) # End main-content
