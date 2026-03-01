import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & MOBILE RESPONSIVE UI (Points 1, 2) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS (Points 2, 6, 7, 8, 9, 23, 70) ---
st.markdown("""
<style>
    /* Gradient Background (Point 2) */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }

    /* Fixed Header Container (Point 23) */
    .fixed-header {
        position: fixed; top: 0; left: 0; width: 100%; height: 215px;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000; padding: 15px 40px; border-bottom: 2px solid white;
        display: flex; justify-content: space-between; align-items: flex-start;
    }

    /* Table Column Header Freeze (Point 23) */
    .table-header-freeze {
        position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
        background-color: #0d47a1; z-index: 999; display: flex; align-items: center;
        border-bottom: 1px solid white;
    }

    .h-cell {
        color: white; font-weight: bold; text-align: center; font-size: 13px;
        border-right: 1px solid rgba(255,255,255,0.3); display: flex; 
        align-items: center; justify-content: center; height: 100%;
    }

    /* Input Styling (Points 6, 7, 32, 33) */
    div[data-baseweb="input"] > div, input, textarea {
        background-color: white !important; color: #0d47a1 !important; 
        font-weight: bold !important; border-radius: 5px !important;
    }
    
    /* Login & Buttons (Point 9) */
    .stButton > button {
        background-color: #d32f2f !important; color: white !important;
        border-radius: 8px; font-weight: bold; border: none;
    }

    /* Main Content Area */
    .data-container { margin-top: 270px; background-color: white; min-height: 100vh; padding: 5px; }
    
    .center-text { text-align: center; color: white; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_db():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    gc = get_db()
    sh = gc.open("ATS_Cloud_Database")
    user_sh = sh.worksheet("User_Master")
    client_sh = sh.worksheet("Client_Master")
    data_sh = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"DB Error: {e}"); st.stop()

# --- 3. LOGIC FUNCTIONS (Points 30, 54, 55-58) ---
def get_next_ref():
    vals = data_sh.col_values(1)
    if len(vals) <= 1: return "E0001"
    ids = [int(v[1:]) for v in vals[1:] if v.startswith("E") and v[1:].isdigit()]
    return f"E{max(ids)+1:04d}" if ids else "E0001"

# --- 4. LOGIN SESSION (Points 3-12) ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br><h1 class='center-text'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='center-text'>ATS LOGIN</h3>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        with st.container(border=True):
            mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password") # Sidebar toggle is default in Streamlit
            rem = st.checkbox("Remember me")
            if st.button("LOGIN", use_container_width=True):
                users = pd.DataFrame(user_sh.get_all_records())
                match = users[(users['Mail_ID']==mail) & (users['Password'].astype(str)==pwd)]
                if not match.empty:
                    st.session_state.auth = True
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.info("Forgot password? Contact Admin")
else:
    # --- 5. DASHBOARD LAYOUT (Points 13-23) ---
    u = st.session_state.user
    
    # Left Header Info (Points 14-17)
    st.markdown(f"""
        <div class="fixed-header">
            <div style="color: white;">
                <h2 style="margin:0; font-size:25px;">Takecare Manpower Service Pvt Ltd</h2>
                <p style="margin:0; font-size:20px; font-style:italic;">Successful HR Firm</p>
                <p style="margin:8px 0 0 0; font-size:18px;">Welcome back, {u['Username']}!</p>
                <div style="background:white; color:#0d47a1; padding:5px 10px; border-radius:4px; font-weight:bold; margin-top:5px; font-size:18px;">
                    📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Right Header Controls (Points 18-21)
    _, r_col = st.columns([3, 1])
    with r_col:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True):
            st.session_state.auth = False
            st.rerun()
        search_q = st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed")
        
        c1, c2 = st.columns(2)
        if u['Role'] in ['ADMIN', 'TL']:
            if c1.button("Filter ⚙️", use_container_width=True): st.session_state.show_filter = True
        
        # --- NEW SHORTLIST POPUP (Points 24-38) ---
        @st.dialog("➕ Add New Candidate Shortlist")
        def add_popup():
            ref = get_next_ref()
            st.write(f"**Reference ID:** {ref}")
            c_name = st.text_input("Candidate Name")
            c_phone = st.text_input("Contact Number (WhatsApp)")
            
            clients = pd.DataFrame(client_sh.get_all_records())
            sel_client = st.selectbox("Client Name", ["-- Select --"] + sorted(clients['Client Name'].unique().tolist()))
            
            positions = clients[clients['Client Name']==sel_client]['Position'].tolist() if sel_client != "-- Select --" else []
            sel_pos = st.selectbox("Position", positions if positions else ["Select Client First"])
            
            comm_date = st.date_input("Commitment / Interview Date", datetime.now())
            status = st.selectbox("Status", ["Shortlisted"])
            fb = st.text_area("Feedback (Optional)")
            
            col_a, col_b = st.columns(2)
            if col_a.button("SUBMIT", use_container_width=True):
                if c_name and c_phone and sel_client != "-- Select --":
                    data_sh.append_row([ref, datetime.now().strftime("%d-%m-%Y"), c_name, c_phone, sel_client, sel_pos, comm_date.strftime("%d-%m-%Y"), status, u['Username'], "", "", fb])
                    st.success("Data Saved!"); st.rerun()
            if col_b.button("CANCEL", use_container_width=True): st.rerun()

        if c2.button("+ New", type="primary", use_container_width=True): add_popup()

    # --- 6. TABLE HEADERS (Point 22) ---
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Date", "Status", "Onboard", "SR Date", "HR", "Action", "WA"]
    widths = [7, 12, 10, 15, 10, 10, 10, 8, 10, 4, 4]
    h_html = "".join([f'<div style="width:{w}%;" class="h-cell">{l}</div>' for l, w in zip(labels, widths)])
    st.markdown(f'<div class="table-header-freeze">{h_html}</div>', unsafe_allow_html=True)

    # --- 7. DATA DISPLAY & LOGIC (Points 39-68) ---
    st.markdown('<div class="data-container">', unsafe_allow_html=True)
    
    raw = data_sh.get_all_records()
    if raw:
        df = pd.DataFrame(raw)
        # Role Filters (Points 59-61)
        if u['Role'] == "RECRUITER": df = df[df['HR Name'] == u['Username']]
        elif u['Role'] == "TL":
            team = pd.DataFrame(user_sh.get_all_records())
            members = team[team['Report_To'] == u['Username']]['Username'].tolist()
            df = df[df['HR Name'].isin(members + [u['Username']])]
            
        # Search (Point 66-68)
        if search_q:
            df = df[df.apply(lambda row: search_q.lower() in row.astype(str).str.lower().values, axis=1)]

        for idx, row in df.iterrows():
            # Auto-Delete Visual Logic (Points 55-57)
            s_date = datetime.strptime(row['Shortlisted Date'], "%d-%m-%Y")
            if row['Status'] == "Shortlisted" and (datetime.now() - s_date).days > 7: continue
            
            r_cols = st.columns(widths)
            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            r_cols[8].write(row['HR Name'])
            
            # EDIT ACTION (Points 39-50)
            if r_cols[9].button("📝", key=f"ed_{idx}"):
                @st.dialog(f"Update: {row['Candidate Name']}")
                def edit_pop():
                    new_st = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                    new_date = st.date_input("Update Date (Interview/Onboard)")
                    new_fb = st.text_area("Feedback", value=row['Feedback'])
                    
                    if st.button("UPDATE"):
                        row_idx = idx + 2
                        data_sh.update_cell(row_idx, 8, new_st)
                        data_sh.update_cell(row_idx, 12, new_fb)
                        
                        if new_st == "Interviewed": data_sh.update_cell(row_idx, 7, new_date.strftime("%d-%m-%Y"))
                        if new_st == "Onboarded":
                            data_sh.update_cell(row_idx, 10, new_date.strftime("%d-%m-%Y"))
                            # SR Date Calculation (Point 54)
                            c_info = pd.DataFrame(client_sh.get_all_records())
                            days = c_info[c_info['Client Name'] == row['Client Name']]['SR Days'].values[0]
                            sr_dt = (new_date + timedelta(days=int(days))).strftime("%d-%m-%Y")
                            data_sh.update_cell(row_idx, 11, sr_dt)
                        st.rerun()
                edit_pop()

            # WHATSAPP (Points 51-53)
            if r_cols[10].button("📲", key=f"wa_{idx}"):
                c_master = pd.DataFrame(client_sh.get_all_records())
                c_dtl = c_master[c_master['Client Name'] == row['Client Name']].iloc[0]
                msg = f"Dear {row['Candidate Name']},\n\nCongratulations! Invite for Direct Interview.\n\nPosition: {row['Job Title']}\nInterview Date: {row['Interview Date']}\nVenue: {c_dtl['Address']}\nMap: {c_dtl['Map Link']}\nContact: {c_dtl['Contact Person']}\n\nRegards,\n{u['Username']}\nTakecare HR Team"
                wa_url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={wa_url}">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
