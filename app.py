import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & STABLE GRADIENT UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

st.markdown("""
    <style>
    /* Stable Professional Gradient Background (Point 69) */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important;
        background-attachment: fixed;
    }
    /* Input Boxes: White background with Dark Blue Text (Point 7 & 8) */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, div[data-baseweb="textarea"] > div {
        background-color: white !important;
        border-radius: 8px !important;
    }
    input, select, textarea {
        color: #00008b !important;
        font-weight: bold !important;
    }
    label { color: white !important; font-weight: 500 !important; }
    
    /* Login Button RED (Point 10) */
    .stButton > button {
        background-color: #FF0000 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    /* Success HR Firm Slogan (Point 16) */
    .slogan { color: #FFD700 !important; font-size: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"GCP Connection Error: {e}"); return None

client = get_gsheet_client()
if client:
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")

# --- 3. HELPER FUNCTIONS ---
def get_next_ref_id():
    # Point 30: Auto Ref ID generation
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E0001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:04d}" if valid_ids else "E0001"

# --- 4. SESSION MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 5. LOGIN PAGE (Points 2-13) ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: white; border-bottom: 2px solid red; padding-bottom: 10px;'>ATS LOGIN</h3>", unsafe_allow_html=True)
    
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container():
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_match.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password") # Point 12
            st.caption("Forgot password? Contact Admin") # Point 11

# --- 6. DASHBOARD (LOGGED IN) ---
else:
    u_data = st.session_state.user_data
    
    # Header Section (Points 15, 16, 20, 21, 22)
    h_col1, h_col2, h_col3 = st.columns([2, 1.5, 0.5])
    with h_col1:
        st.markdown("<h1 style='font-size: 25px; color: white;'>Takecare Manpower Service Pvt Ltd</h1>", unsafe_allow_html=True)
        st.markdown("<p class='slogan'>Successful HR Firm</p>", unsafe_allow_html=True)
    with h_col2:
        st.markdown(f"<p style='color: white; font-size: 18px;'>Welcome back, {u_data['Username']}!</p>", unsafe_allow_html=True)
        st.markdown("<p style='color: #00FF00;'>Target: 80+ Calls / 3-5 Interview / 1+ Joining</p>", unsafe_allow_html=True)
    with h_col3:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # Action Row (Points 17, 18, 19, 65, 66)
    c_btn1, c_btn2, c_btn3, c_search = st.columns([1, 1, 1.2, 2])
    
    # Point 24-38: NEW SHORTLIST DIALOG
    @st.dialog("New Candidate Shortlist")
    def new_shortlist_dialog():
        ref_id = get_next_ref_id() # Point 30
        st.write(f"**Reference ID:** {ref_id}")
        st.write(f"**Date:** {datetime.now().strftime('%d-%m-%Y')}")
        
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            # Point 34: Client Name dropdown
            c_master = pd.DataFrame(client_sheet.get_all_records())
            client_list = sorted(c_master['Client Name'].unique().tolist())
            sel_client = st.selectbox("Client Name", ["--Select--"] + client_list)
        with col2:
            # Point 35: Position base on client
            pos_list = c_master[c_master['Client Name'] == sel_client]['Position'].tolist() if sel_client != "--Select--" else []
            sel_pos = st.selectbox("Position", pos_list)
            comm_date = st.date_input("Commitment Date")
            status = st.selectbox("Status", ["Shortlisted"])
            
        feedback = st.text_area("Feedback")
        
        if st.button("SUBMIT"): # Point 27
            if name and phone and sel_client != "--Select--":
                new_row = [ref_id, datetime.now().strftime('%d-%m-%Y'), name, phone, sel_client, sel_pos, comm_date.strftime('%d-%m-%Y'), status, u_data['Username'], "", "", feedback]
                cand_sheet.append_row(new_row)
                st.success("Data Saved!")
                st.rerun()
        if st.button("CANCEL"): st.rerun()

    with c_btn1: 
        if st.button("🔍 Search"): pass # Focus to search text_input
    with c_btn2:
        if u_data['Role'] in ['ADMIN', 'TL']:
            if st.button("⚡ Filter"): st.toast("Filter Clicked")
    with c_btn3:
        if st.button("➕ New Shortlist"): new_shortlist_dialog()
    with c_search:
        search_query = st.text_input("Search (Type anything to filter rows)", label_visibility="collapsed")

    # --- 7. DATA TABLE (Points 23, 24, 54-58) ---
    st.markdown("---")
    # Headers
    h_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1, 1, 1, 0.5, 0.5])
    labels = ["Ref ID", "Candidate", "Number", "Job Title", "Int/Comm Date", "Status", "Onboard", "SR Date", "Edit", "WA"]
    for col, l in zip(h_cols, labels): col.markdown(f"<div style='color: #00BFFF; font-weight: bold;'>{l}</div>", unsafe_allow_html=True)
    
    # Data Rows Logic
    raw_data = cand_sheet.get_all_records()
    df = pd.DataFrame(raw_data)
    
    # Filter by Role (Points 59-61)
    if u_data['Role'] == "RECRUITER":
        df = df[df['HR Name'] == u_data['Username']]
    elif u_data['Role'] == "TL":
        # TL access logic for team entries
        pass

    # Search Logic (Point 67-68)
    if search_query:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]

    # Display Rows (Scrollable logic handled by Streamlit naturally)
    for _, row in df.iterrows():
        r_cols = st.columns([0.8, 1.5, 1.2, 1.2, 1.2, 1, 1, 1, 0.5, 0.5])
        r_cols[0].write(row['Reference_ID'])
        r_cols[1].write(row['Candidate Name'])
        r_cols[2].write(row['Contact Number'])
        r_cols[3].write(row['Job Title'])
        r_cols[4].write(row['Commitment Date'])
        r_cols[5].write(row['Status'])
        r_cols[6].write(row['Onboarded Date'])
        r_cols[7].write(row['SR Date'])
        
        # Edit Pencil (Point 39-49)
        if r_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
            st.toast(f"Edit {row['Reference_ID']}")
            
        # WhatsApp Invite (Point 51-53)
        if r_cols[9].button("📲", key=f"wa_{row['Reference_ID']}"):
            msg = f"Dear {row['Candidate Name']}, Congratulations! Invite for Direct Interview..." # Simplified template
            url = f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)
