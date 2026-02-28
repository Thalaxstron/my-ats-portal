import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta
import time

# --- 1. PAGE CONFIG & UI (Points 1, 2, 24, 70, 81) ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Gradient, Fixed Header, and White Input Boxes
st.markdown("""
    <style>
    /* Background Gradient (Point 2) */
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    
    /* Fixed Header Area (Point 24) */
    .fixed-header-container {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
        z-index: 1000;
        padding: 15px 40px;
        border-bottom: 2px solid rgba(255,255,255,0.3);
        height: 220px;
    }

    /* White Input Boxes with Dark Blue Text (Point 6, 7, 70) */
    div[data-baseweb="input"], div[data-baseweb="select"], .stTextArea textarea, input {
        background-color: white !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
        border-radius: 5px !important;
    }

    /* ATS Tracking Table - Excel Look (Point 25, 26) */
    .ats-scroll-container {
        background-color: white;
        margin-top: 230px; 
        padding: 0px;
        border: 1px solid #ccc;
    }

    /* Typography */
    .company-title { color: white; font-size: 28px; font-weight: bold; margin: 0; }
    .slogan-text { color: white; font-size: 16px; font-style: italic; margin: 0; }
    .welcome-msg { color: white; font-size: 20px; margin-top: 15px; }
    .target-box { 
        background-color: rgba(255,255,255,0.2); 
        color: white; 
        padding: 8px; 
        border-radius: 5px; 
        font-size: 15px; 
        margin-top: 10px;
        border-left: 5px solid white;
    }
    
    /* Button Styles */
    .stButton button {
        border-radius: 5px !important;
        font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GOOGLE SHEETS CONNECTION ---
@st.cache_resource
def init_connection():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    gc = init_connection()
    sh = gc.open("ATS_Cloud_Database")
    u_sheet = sh.worksheet("User_Master")
    c_sheet = sh.worksheet("Client_Master")
    d_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"Connection Error: Check st.secrets or Sheet Names. {e}")
    st.stop()

# --- 3. CORE LOGIC FUNCTIONS ---

def get_next_ref_id():
    # Point 35: Automatic Reference ID (E0001, E0002...)
    ids = d_sheet.col_values(1)
    if len(ids) <= 1: return "E0001"
    last_id = ids[-1]
    if last_id.startswith("E"):
        return f"E{int(last_id[1:]) + 1:04d}"
    return "E0001"

def clean_ats_view(df):
    # Points 62-64: Status-based Auto-Delete from View
    today = datetime.now()
    df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df['Interview Date'] = pd.to_datetime(df['Interview Date'], format="%d-%m-%Y", errors='coerce')
    
    # Logic 62: Shortlisted > 7 days
    mask1 = (df['Status'] == 'Shortlisted') & (df['Shortlisted Date'] < today - timedelta(days=7))
    # Logic 64: Left/Not Joined > 3 days
    mask2 = (df['Status'].isin(['Left', 'Not Joined'])) & (df['Shortlisted Date'] < today - timedelta(days=3))
    
    # Keep Onboarded & Project Success always (Point 65)
    return df[~(mask1 | mask2) | (df['Status'].isin(['Onboarded', 'Project Success']))]

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_info' not in st.session_state: st.session_state.user_info = {}

# --- 5. LOGIN PAGE (Points 3-12) ---
if not st.session_state.logged_in:
    st.markdown("<br><br><h1 style='text-align:center; color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, l_col, _ = st.columns([1, 1.2, 1])
    with l_col:
        with st.container(border=True):
            email = st.text_input("Email ID (Dark Blue Text)", placeholder="Enter registered email")
            upass = st.text_input("Password", type="password")
            st.checkbox("Remember me")
            if st.button("LOGIN", use_container_width=True, type="primary"):
                users = pd.DataFrame(u_sheet.get_all_records())
                match = users[(users['Mail_ID'] == email) & (users['Password'].astype(str) == upass)]
                if not match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_info = match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# --- 6. MAIN DASHBOARD ---
else:
    u = st.session_state.user_info
    
    # --- HEADER SECTION (Points 14-24, 81) ---
    # Left Side Info
    st.markdown(f"""
        <div class="fixed-header-container">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 60%;">
                    <p class="company-title">Takecare Manpower Services Pvt Ltd</p>
                    <p class="slogan-text">Successful HR Firm</p>
                    <p class="welcome-msg">Welcome back, {u['Username']}!</p>
                    <div class="target-box">
                        📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Right Side Buttons (Aligned with Left 4 lines)
    # Using streamlit columns inside the header area (positioning via spacer)
    with st.sidebar: st.write("Menu") # Using sidebar as extra space if needed

    # Absolute Positioning for Header Buttons
    h_col1, h_col2 = st.columns([3, 1])
    with h_col2:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        if st.button("Logout 🚪", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.rerun()
        
        search_val = st.text_input("Search", placeholder="Search in data sheet...", label_visibility="collapsed")
        
        if u['Role'] in ['ADMIN', 'TL']:
            if st.button("Filter Symbol ⚙️", use_container_width=True):
                # Filter Dialog logic (Point 71)
                pass
        
        # Point 29: New Shortlist Button
        if st.button("+ New Shortlist", type="primary", use_container_width=True):
            @st.dialog("➕ Add New Shortlist")
            def new_shortlist_dialog():
                clients = pd.DataFrame(c_sheet.get_all_records())
                ref_id = get_next_ref_id()
                
                c1, c2 = st.columns(2)
                c1.text_input("Reference ID", value=ref_id, disabled=True)
                c2.text_input("Shortlist Date", value=datetime.now().strftime("%d-%m-%Y"), disabled=True)
                
                c_name = c1.text_input("Candidate Name")
                c_phone = c2.text_input("Contact Number")
                
                client_choice = c1.selectbox("Client Name", options=clients['Client Name'].unique())
                pos_options = clients[clients['Client Name'] == client_choice]['Position'].tolist()
                pos_choice = c2.selectbox("Position", options=pos_options)
                
                comm_date = c1.date_input("Commitment Date")
                status = c2.selectbox("Status", ["Shortlisted"])
                feedback = st.text_area("Feedback")
                
                if st.button("SUBMIT"):
                    d_sheet.append_row([
                        ref_id, datetime.now().strftime("%d-%m-%Y"), c_name, c_phone, 
                        client_choice, pos_choice, comm_date.strftime("%d-%m-%Y"), 
                        status, u['Username'], "", "", feedback
                    ])
                    st.success("Data Saved!"); time.sleep(1); st.rerun()
            new_shortlist_dialog()

    # --- 7. DATA FETCH & FILTERING (Points 66-68) ---
    raw_df = pd.DataFrame(d_sheet.get_all_records())
    
    if u['Role'] == 'RECRUITER':
        # Show only their entries
        df = raw_df[raw_df['HR Name'] == u['Username']]
    elif u['Role'] == 'TL':
        # Show team entries
        users_list = pd.DataFrame(u_sheet.get_all_records())
        team = users_list[users_list['Report_To'] == u['Username']]['Username'].tolist()
        df = raw_df[raw_df['HR Name'].isin(team + [u['Username']])]
    else:
        df = raw_df

    # Apply Auto-Delete Filter
    df = clean_ats_view(df)
    
    # Search Logic (Points 79-80)
    if search_val:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_val, case=False)).any(axis=1)]

    # --- 8. ATS TRACKING TABLE (Points 25-27) ---
    st.markdown('<div class="ats-scroll-container">', unsafe_allow_html=True)
    
    # Table Headers
    cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
    headers = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboard", "SR Date", "HR", "Action", "WA"]
    for col, h in zip(cols, headers): col.write(f"**{h}**")
    
    st.divider()

    # Data Rows
    for idx, row in df.iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.5, 1.2, 1.2, 1.2, 1.2, 1, 0.8, 0.8])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Interview Date']) # This is the Commitment/Int Date column
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Joining Date'])
        r_cols[7].write(row['SR Date'])
        r_cols[8].write(row['HR Name'])
        
        # Point 47: Edit Pencil
        if r_cols[9].button("📝", key=f"edit_{row['Reference_ID']}"):
            @st.dialog(f"Update: {row['Candidate Name']}")
            def edit_candidate_dialog(r):
                st.write(f"Contact: {r['Contact Number']}")
                new_status = st.selectbox("Status", ["Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Project Success"])
                new_date = st.date_input("Update Date (Interview/Onboard)")
                new_fb = st.text_input("Feedback", max_chars=20)
                
                if st.button("SAVE CHANGES"):
                    sheet_row = raw_df[raw_df['Reference_ID'] == r['Reference_ID']].index[0] + 2
                    d_sheet.update_cell(sheet_row, 8, new_status)
                    d_sheet.update_cell(sheet_row, 12, new_fb)
                    
                    # Point 53-54: Interview Date overwrites Commitment Date
                    if new_status == "Interviewed":
                        d_sheet.update_cell(sheet_row, 7, new_date.strftime("%d-%m-%Y"))
                    
                    # Point 56 & 61: Onboarded & SR Date Calculation
                    if new_status == "Onboarded":
                        d_sheet.update_cell(sheet_row, 10, new_date.strftime("%d-%m-%Y"))
                        clients_db = pd.DataFrame(c_sheet.get_all_records())
                        sr_days = clients_db[clients_db['Client Name'] == r['Client Name']]['SR Days'].values[0]
                        sr_calc = (new_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                        d_sheet.update_cell(sheet_row, 11, sr_calc)
                    
                    st.success("Updated!"); time.sleep(1); st.rerun()
            edit_candidate_dialog(row)

        # Point 44-46: WhatsApp Invite Logic
        if r_cols[10].button("📲", key=f"wa_{row['Reference_ID']}"):
            c_db = pd.DataFrame(c_sheet.get_all_records())
            c_info = c_db[c_db['Client Name'] == row['Client Name']].iloc[0]
            
            # Point 46: Message Template
            msg = (
                f"Dear {row['Candidate Name']},\n\n"
                f"Congratulations, we invite you for a Direct Interview.\n\n"
                f"Reference: Takecare Manpower Services Pvt Ltd\n"
                f"Position: {row['Job Title']}\n"
                f"Interview Date: {row['Interview Date']}\n"
                f"Interview Time: 10.30 AM\n"
                f"Interview Venue: {c_info.get('Address', '')}\n"
                f"Map Link: {c_info.get('Map Link', '')}\n"
                f"Contact Person: {c_info.get('Contact Person', '')}\n\n"
                f"Please let me know when you arrive. All the best.\n\n"
                f"Regards,\n{u['Username']}\nTakecare HR Team"
            )
            
            encoded_msg = urllib.parse.quote(msg)
            wa_url = f"https://wa.me/91{row['Contact Number']}?text={encoded_msg}"
            # Open WhatsApp in new tab
            st.markdown(f'<meta http-equiv="refresh" content="0;URL=\'{wa_url}\'">', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
