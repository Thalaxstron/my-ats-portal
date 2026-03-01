import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse
import time

# --- 1. CONFIG & STYLE (Points 1-9, 23) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Gradient Background */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Design Header (215px) */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 20px 50px; border-bottom: 2px solid white;
        color: white;
    }

    /* Fixed Table Header (45px) */
    .sticky-table-header {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; display: flex; align-items: center;
        border-bottom: 1px solid white; color: white; font-weight: bold;
    }

    /* Scrollable Content Area */
    .content-area { margin-top: 270px; padding: 10px; background: white; min-height: 80vh; border-radius: 10px 10px 0 0; }

    /* Input Box Styles */
    input, select, textarea { color: #0d47a1 !important; font-weight: bold !important; background: white !important; }
    
    /* Buttons */
    .stButton > button { border-radius: 5px; font-weight: bold; }
    .login-btn button { background-color: #d32f2f !important; color: white !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_conn():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

gc = get_conn()
if gc:
    try:
        sh = gc.open("ATS_Cloud_Database")
        user_sh = sh.worksheet("User_Master")
        data_sh = sh.worksheet("ATS_Data")
        client_sh = sh.worksheet("Client_Master")
    except Exception as e:
        st.error(f"Sheet Access Error: Share the sheet with your Service Account Email! \n {e}")
        st.stop()

# --- 3. SESSION STATE ---
if "auth" not in st.session_state: st.session_state.auth = False

# --- 4. LOGIN PAGE (Points 3-12) ---
if not st.session_state.auth:
    st.markdown("<br><br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            m = st.text_input("Email ID")
            p = st.text_input("Password", type="password")
            rem = st.checkbox("Remember me")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==m) & (users['Password'].astype(str)==p)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 5. DASHBOARD (Points 13-68) ---
else:
    u = st.session_state.user
    
    # FROZEN HEADER CONTENT
    st.markdown(f"""
        <div class="fixed-header">
            <div style="float: left; width: 70%;">
                <h2 style="margin:0;">Takecare Manpower Service Pvt Ltd</h2>
                <h4 style="margin:0; font-style: italic; opacity: 0.9;">Successful HR Firm</h4>
                <p style="margin:5px 0; font-size:18px;">Welcome back, {u['Username']}!</p>
                <div style="background: rgba(255,255,255,0.2); padding: 8px; border-radius: 5px; display: inline-block;">
                    Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # HEADER BUTTONS (Right Side)
    with st.container():
        st.markdown('<div style="position: fixed; top: 20px; right: 50px; z-index: 1001; width: 250px;">', unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
        s_query = st.text_input("Search", placeholder="🔍 Search candidate...", label_visibility="collapsed")
        
        c1, c2 = st.columns(2)
        if u['Role'] in ['ADMIN', 'TL']:
            if c1.button("Filter ⚙️"): st.session_state.show_filter = True
        
        # NEW SHORTLIST DIALOG (Points 24-38)
        @st.dialog("➕ New Shortlist Entry")
        def add_new():
            # Get next ID
            ids = data_sh.col_values(1)
            next_id = f"E{len(ids):05d}"
            st.write(f"**Reference ID:** {next_id}")
            
            c_name = st.text_input("Candidate Name")
            c_phone = st.text_input("Contact Number")
            
            clients_df = pd.DataFrame(client_sh.get_all_records())
            sel_client = st.selectbox("Client Name", sorted(clients_df['Client Name'].unique()))
            
            pos_list = clients_df[clients_df['Client Name']==sel_client]['Position'].tolist()
            sel_pos = st.selectbox("Position", pos_list)
            
            int_date = st.date_input("Interview/Commitment Date")
            fb = st.text_area("Feedback")
            
            col_a, col_b = st.columns(2)
            if col_a.button("SUBMIT", use_container_width=True):
                data_sh.append_row([next_id, datetime.now().strftime("%d-%m-%Y"), c_name, c_phone, sel_client, sel_pos, int_date.strftime("%d-%m-%Y"), "Shortlisted", u['Username'], "", "", fb])
                st.success("Added!"); time.sleep(1); st.rerun()
            if col_b.button("CANCEL", use_container_width=True): st.rerun()

        if c2.button("+ New", use_container_width=True, type="primary"): add_new()
        st.markdown('</div>', unsafe_allow_html=True)

    # TABLE HEADER FREEZE (Point 22, 23)
    cols = [7, 12, 10, 12, 10, 10, 10, 10, 10, 5, 4]
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Int. Date", "Status", "Onboard", "SR Date", "HR Name", "Edit", "WA"]
    h_html = "".join([f'<div style="width:{w}%; text-align:center; border-right:1px solid white;">{l}</div>' for w, l in zip(cols, labels)])
    st.markdown(f'<div class="sticky-table-header">{h_html}</div>', unsafe_allow_html=True)

    # DATA AREA (Scrollable)
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Fetch and Filter Data
    df = pd.DataFrame(data_sh.get_all_records())
    if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
    elif u['Role'] == "TL":
        team = pd.DataFrame(user_sh.get_all_records())
        mems = team[team['Report_To'] == u['Username']]['Username'].tolist()
        df = df[df['HR Name'].isin(mems + [u['Username']])]
    
    if s_query:
        df = df[df.apply(lambda r: s_query.lower() in str(r).lower(), axis=1)]

    # Display Rows
    for idx, row in df.iterrows():
        # Auto-Delete Logic Visual
        s_dt = datetime.strptime(row['Shortlisted Date'], "%d-%m-%Y")
        if row['Status'] == "Shortlisted" and (datetime.now() - s_dt).days > 7: continue
        
        r_cols = st.columns(cols)
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        
        # EDIT DIALOG (Points 39-50)
        if r_cols[9].button("📝", key=f"edit_{idx}"):
            @st.dialog(f"Update: {row['Candidate Name']}")
            def update_row():
                new_st = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                new_date = st.date_input("Update Date (Interview/Joining)")
                new_fb = st.text_area("Feedback", value=row['Feedback'])
                
                if st.button("UPDATE", use_container_width=True):
                    sh_row = idx + 2
                    data_sh.update_cell(sh_row, 8, new_st)
                    data_sh.update_cell(sh_row, 12, new_fb)
                    if new_st == "Interviewed": data_sh.update_cell(sh_row, 7, new_date.strftime("%d-%m-%Y"))
                    if new_st == "Onboarded":
                        data_sh.update_cell(sh_row, 10, new_date.strftime("%d-%m-%Y"))
                        # SR Date Calculation
                        c_df = pd.DataFrame(client_sh.get_all_records())
                        days = int(c_df[c_df['Client Name'] == row['Client Name']]['SR Days'].values[0])
                        sr_dt = (new_date + timedelta(days=days)).strftime("%d-%m-%Y")
                        data_sh.update_cell(sh_row, 11, sr_dt)
                    st.success("Updated!"); time.sleep(1); st.rerun()
            update_row()

        # WHATSAPP (Points 51-53)
        if r_cols[10].button("📲", key=f"wa_{idx}"):
            c_df = pd.DataFrame(client_sh.get_all_records())
            c_info = c_df[c_df['Client Name'] == row['Client Name']].iloc[0]
            msg = f"Dear {row['Candidate Name']},\n\nDirect Interview Invite!\n\nPosition: {row['Job Title']}\nInterview Date: {row['Interview Date']}\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nRegards,\n{u['Username']}\nTakecare HR Team"
            wa_url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank">Click to Send WhatsApp</a>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
