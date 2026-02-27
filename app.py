import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
        background-attachment: fixed;
    }
    .main-title { color: white; text-align: center; font-size: 35px; font-weight: bold; padding: 10px; }
    .target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    /* White Input Boxes for better readability */
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        background-color: white !important;
        color: #0d47a1 !important;
    }
    .status-card { background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; border: 1px solid white; }
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
    st.error("Database Connection Failed. Check Secrets."); st.stop()

# --- 3. CORE LOGIC FUNCTIONS ---

def get_next_ref_id():
    """Generates unique Ref ID: E00001, E00002..."""
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

def calculate_sr_date(join_date_str, client_name):
    """Calculates SR Date based on Client Master SR Days"""
    c_df = pd.DataFrame(client_sheet.get_all_records())
    try:
        days = int(c_df[c_df['Client Name'] == client_name]['SR Days'].values[0])
        join_dt = datetime.strptime(join_date_str, "%d-%m-%Y")
        return (join_dt + timedelta(days=days)).strftime("%d-%m-%Y")
    except: return ""

# --- 4. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            st.markdown("<h3 style='text-align:center; color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                u_df = pd.DataFrame(user_sheet.get_all_records())
                u_df.columns = u_df.columns.str.strip()
                user = u_df[(u_df['Mail_ID'] == u_mail) & (u_df['Password'].astype(str) == u_pass)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")
else:
    # --- 5. DASHBOARD ---
    u = st.session_state.user_data
    
    # Header
    h1, h2, h3 = st.columns([2, 3, 1])
    h1.write(f"### Takecare Manpower")
    h2.write(f"### Welcome back, {u['Username']}!")
    if h3.button("Log out"): 
        st.session_state.logged_in = False
        st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # --- NEW SHORTLIST POPUP ---
    @st.dialog("➕ New Candidate Shortlist")
    def add_shortlist():
        new_id = get_next_ref_id()
        st.info(f"Ref ID: {new_id}")
        
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            cl_df = pd.DataFrame(client_sheet.get_all_records())
            client_name = st.selectbox("Client Name", cl_df['Client Name'].unique())
        with c2:
            positions = cl_df[cl_df['Client Name'] == client_name]['Position'].tolist()
            job = st.selectbox("Position", positions)
            comm_date = st.date_input("Commitment Date")
            status = st.selectbox("Status", ["Shortlisted"])
        
        feedback = st.text_area("Feedback")
        send_wa = st.checkbox("Send WhatsApp Invite Link", value=True)

        if st.button("SUBMIT"):
            if name and phone:
                today = datetime.now().strftime("%d-%m-%Y")
                c_dt = comm_date.strftime("%d-%m-%Y")
                
                # Append to Sheet
                cand_sheet.append_row([new_id, today, name, phone, client_name, job, c_dt, status, u['Username'], "", "", feedback])
                
                if send_wa:
                    # WhatsApp Logic
                    c_info = cl_df[(cl_df['Client Name'] == client_name) & (cl_df['Position'] == job)].iloc[0]
                    wa_msg = f"Dear {name},\n\nCongratulations! Invite for Interview.\n\nPosition: {job}\nDate: {c_dt}\nTime: 10.30 AM\nVenue: {c_info['Address']}\nMap: {c_info['Map Link']}\nContact: {c_info['Contact Person']}\n\nAll the best!\nRegards,\n{u['Username']}\nTakecare HR Team"
                    wa_url = f"https://wa.me/91{phone}?text={urllib.parse.quote(wa_msg)}"
                    st.markdown(f'<a href="{wa_url}" target="_blank">📲 Click here to Send WhatsApp</a>', unsafe_allow_html=True)
                
                st.success("Shortlist Saved!")
                st.rerun()

    # Dashboard Actions
    col_a, col_b = st.columns([4, 1])
    if col_a.button("+ New Shortlist"): add_shortlist()
    search = col_b.text_input("🔍 Search Anything")

    # --- 6. DATA DISPLAY & AUTO-DELETE LOGIC ---
    df = pd.DataFrame(cand_sheet.get_all_records())
    if not df.empty:
        df.columns = df.columns.str.strip()
        
        # Permissions
        if u['Role'] == "RECRUITER":
            df = df[df['HR Name'] == u['Username']]
        elif u['Role'] == "TL":
            users = pd.DataFrame(user_sheet.get_all_records())
            team = users[users['Report_To'] == u['Username']]['Username'].tolist()
            df = df[df['HR Name'].isin(team + [u['Username']])]

        # Auto-Delete logic (Filtering from View)
        today_dt = datetime.now()
        df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
        
        # 1. Shortlisted > 7 days -> Hide
        df = df[~((df['Status'] == 'Shortlisted') & (df['Shortlisted Date DT'] < today_dt - timedelta(days=7)))]
        
        # Search filter
        if search:
            df = df[df.apply(lambda row: search.lower() in row.astype(str).str.lower().values, axis=1)]

        # Display Table Headers
        t_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 0.5])
        headers = ["Ref ID", "Candidate", "Contact", "Position", "Commitment", "Status", "Onboard", "SR Date", "Action"]
        for col, h in zip(t_cols, headers): col.markdown(f"**{h}**")

        for i, row in df.iterrows():
            r_cols = st.columns([0.8, 1.2, 1, 1.2, 1, 1, 1, 1, 0.5])
            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            
            if r_cols[8].button("📝", key=f"ed_{row['Reference_ID']}"):
                st.session_state.edit_ref = row['Reference_ID']

    # --- 7. EDIT MODAL (SIDEBAR) ---
    if 'edit_ref' in st.session_state:
        with st.sidebar:
            st.header(f"Edit: {st.session_state.edit_ref}")
            curr = df[df['Reference_ID'] == st.session_state.edit_ref].iloc[0]
            
            new_status = st.selectbox("Change Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Left", "Not Joined"], index=0)
            new_feed = st.text_area("Update Feedback", value=curr['Feedback'])
            
            up_data = {"Status": new_status, "Feedback": new_feed}

            if new_status == "Interviewed":
                up_data["Interview Date"] = st.date_input("Interview Date").strftime("%d-%m-%Y")
            
            if new_status == "Onboarded":
                join_dt = st.date_input("Joining Date")
                up_data["Joining Date"] = join_dt.strftime("%d-%m-%Y")
                up_data["SR Date"] = calculate_sr_date(up_data["Joining Date"], curr['Client Name'])

            if st.button("SAVE UPDATES"):
                # Find exact row in Sheet
                all_records = cand_sheet.get_all_records()
                row_idx = next(i for i, r in enumerate(all_records) if r['Reference_ID'] == st.session_state.edit_ref) + 2
                
                # Update cells
                cand_sheet.update_cell(row_idx, 8, up_data["Status"])
                cand_sheet.update_cell(row_idx, 12, up_data["Feedback"])
                if "Interview Date" in up_data: cand_sheet.update_cell(row_idx, 7, up_data["Interview Date"])
                if "Joining Date" in up_data:
                    cand_sheet.update_cell(row_idx, 10, up_data["Joining Date"])
                    cand_sheet.update_cell(row_idx, 11, up_data["SR Date"])
                
                st.success("Updated Successfully!")
                del st.session_state.edit_ref
                st.rerun()
