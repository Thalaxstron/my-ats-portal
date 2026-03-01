import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare ATS", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(135deg,#d32f2f,#0d47a1); background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
.main-title { color: white; text-align: center; font-size: 40px; font-weight: bold; }
.sub-title { color: white; text-align: center; font-size: 25px; }
input, select, textarea { color:#0d47a1 !important; font-weight:bold !important; background-color: white !important; }
.target-bar { background:#1565c0; color:white; padding:10px; border-radius:8px; font-weight:bold; margin-bottom: 20px; }
/* Table Header Style */
.header-row { background-color: #0d47a1; color: white; font-weight: bold; padding: 10px; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def connect():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    gc = connect()
    sh = gc.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    data_sheet = sh.worksheet("ATS_Data")
    client_sheet = sh.worksheet("Client_Master")
except Exception as e:
    st.error(f"Database Error: Please share the Sheet with your Service Account Email. Details: {e}")
    st.stop()

# --- 3. LOGIC HELPERS ---
def get_next_ref():
    all_ids = data_sheet.col_values(1)
    if len(all_ids) <= 1: return "E00001"
    valid_ids = [int(x[1:]) for x in all_ids[1:] if x.startswith("E") and x[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. LOGIN SYSTEM ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)
    _, c, _ = st.columns([1,1.2,1])
    with c:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df["Mail_ID"] == u_mail) & (users_df["Password"].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user = user_row.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")
else:
    # --- 5. DASHBOARD (LOGGED IN) ---
    u = st.session_state.user
    
    # Header Info
    h_left, h_right = st.columns([3, 1])
    with h_left:
        st.markdown(f"### Takecare Manpower Service Pvt Ltd")
        st.markdown(f"*Successful HR Firm*")
        st.markdown(f"**Welcome back, {u['Username']}!**")
    with h_right:
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # --- 6. POPUP DIALOGS ---
    @st.dialog("➕ New Shortlist")
    def new_entry():
        ref = get_next_ref()
        st.write(f"Reference ID: **{ref}**")
        c1, c2 = st.columns(2)
        name = c1.text_input("Candidate Name")
        phone = c2.text_input("WhatsApp Number")
        
        c_df = pd.DataFrame(client_sheet.get_all_records())
        sel_client = st.selectbox("Client Name", sorted(c_df["Client Name"].unique()))
        
        pos_list = c_df[c_df["Client Name"] == sel_client]["Position"].tolist()
        sel_pos = st.selectbox("Position", pos_list)
        
        comm_date = st.date_input("Interview Date", datetime.now())
        fb = st.text_area("Feedback")
        
        if st.button("SUBMIT", use_container_width=True):
            data_sheet.append_row([
                ref, datetime.now().strftime("%d-%m-%Y"), name, phone,
                sel_client, sel_pos, comm_date.strftime("%d-%m-%Y"),
                "Shortlisted", u['Username'], "", "", fb
            ])
            st.success("Entry Saved!")
            st.rerun()

    # Dashboard Buttons
    btn_col1, btn_col2, btn_col3 = st.columns([1,2,1])
    with btn_col1:
        if st.button("+ New Shortlist", type="primary"): new_entry()
    with btn_col2:
        search_q = st.text_input("Search Anything...", placeholder="Type name, phone, or status")

    # --- 7. DATA LOADING & FILTERING ---
    df = pd.DataFrame(data_sheet.get_all_records())
    
    # Role Based Filter
    if u["Role"] == "RECRUITER":
        df = df[df["HR Name"] == u["Username"]]
    elif u["Role"] == "TL":
        team_users = pd.DataFrame(user_sheet.get_all_records())
        team = team_users[team_users["Report_To"] == u["Username"]]["Username"].tolist()
        df = df[df["HR Name"].isin(team + [u["Username"]])]

    # Auto-Delete Visual Logic
    now = datetime.now()
    df['Shortlisted Date DT'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')
    df = df[~((df['Status'] == "Shortlisted") & (df['Shortlisted Date DT'] < now - timedelta(days=7)))]

    if search_q:
        df = df[df.apply(lambda row: search_q.lower() in str(row).lower(), axis=1)]

    # --- 8. DATA DISPLAY ---
    st.dataframe(df.drop(columns=['Shortlisted Date DT']), use_container_width=True, hide_index=True)

    # --- 9. EDIT LOGIC (Simplified for performance) ---
    st.divider()
    with st.expander("📝 Update Candidate Status"):
        edit_id = st.selectbox("Select Ref ID to Update", [""] + df["Reference_ID"].tolist())
        if edit_id:
            row_data = df[df["Reference_ID"] == edit_id].iloc[0]
            new_st = st.selectbox("New Status", ["Shortlisted", "Interviewed", "Selected", "Onboarded", "Rejected", "Hold", "Left"])
            new_fb = st.text_area("Update Feedback", value=row_data["Feedback"])
            
            j_date = None
            if new_st == "Onboarded":
                j_date = st.date_input("Joining Date")
            
            if st.button("Update Sheet"):
                # Find exact row in sheet
                all_ids = data_sheet.col_values(1)
                row_idx = all_ids.index(edit_id) + 1
                data_sheet.update_cell(row_idx, 8, new_st)
                data_sheet.update_cell(row_idx, 12, new_fb)
                
                if new_st == "Onboarded" and j_date:
                    data_sheet.update_cell(row_idx, 10, j_date.strftime("%d-%m-%Y"))
                    # SR Date Logic
                    c_master = pd.DataFrame(client_sheet.get_all_records())
                    days = int(c_master[c_master["Client Name"] == row_data["Client Name"]]["SR Days"].values[0])
                    sr_date = (j_date + timedelta(days=days)).strftime("%d-%m-%Y")
                    data_sheet.update_cell(row_idx, 11, sr_date)
                
                st.success("Updated Successfully!")
                st.rerun()
