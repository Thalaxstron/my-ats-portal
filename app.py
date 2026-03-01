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
[data-testid="stHeader"] { background: transparent; }
.main-title { color: white; text-align: center; font-size: 40px; font-weight: bold; margin-bottom: 0px; }
.sub-title { color: white; text-align: center; font-size: 25px; margin-bottom: 20px; }
.target-bar { background-color: #1565c0; color: white; padding: 10px; border-radius: 5px; font-weight: bold; margin-bottom: 10px; }
div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
div[data-baseweb="input"] > div { background-color: white !important; }
input, textarea { background-color: white !important; color: #0d47a1 !important; font-weight: bold !important; }
[data-testid="stTextInput"] svg { color: black !important; }
div[data-baseweb="checkbox"] { background-color: white !important; padding: 6px; border-radius: 6px; }
.stButton > button { background-color: #d32f2f !important; color: white !important; border-radius: 8px; font-weight: bold; border: none; }
.stButton > button:hover { background-color: #b71c1c !important; }
</style>
""", unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
cand_sheet = sh.worksheet("ATS_Data")

# --- HELPER ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1:
        return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:] if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:

    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)

    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")
            st.checkbox("Remember Me")

            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()
                user_row = users_df[(users_df['Mail_ID'] == u_mail) &
                                    (users_df['Password'].astype(str) == u_pass)]

                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")

            st.caption("Forgot password? Contact Admin")

# ---------------- DASHBOARD ----------------
else:

    u_data = st.session_state.user_data

    h_col1, h_col2, h_col3, h_col4 = st.columns([1, 2, 1.5, 0.5])
    with h_col1:
        st.subheader("TAKECARE")
    with h_col2:
        st.markdown(f"### Welcome back, {u_data['Username']}!")
    with h_col4:
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.rerun()

    st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # -------- BUTTON + SEARCH --------
    col_btn, col_search = st.columns([6, 1])
    with col_btn:
        if st.button("+ New Shortlist"):
            st.session_state.show_popup = True
    with col_search:
        search_query = st.text_input("🔍 Search")

    raw_data = cand_sheet.get_all_records()

    if raw_data:
        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()

        now = datetime.now()
        df['Shortlisted Date'] = pd.to_datetime(df['Shortlisted Date'], format="%d-%m-%Y", errors='coerce')

        df = df[~(
            (df['Status'] == "Shortlisted") &
            (df['Shortlisted Date'] < now - timedelta(days=7))
        )]

        st.markdown("---")

        # ✅ ALIGNMENT FIXED HERE
        column_widths = [1, 2, 1.5, 1.8, 1.3, 1.3, 1.2, 1.2, 0.6]

        headers = ["Ref ID", "Candidate", "Contact", "Job Title",
                   "Int. Date", "Status", "Onboard", "SR Date", "Edit"]

        header_cols = st.columns(column_widths)
        for col, h in zip(header_cols, headers):
            col.markdown(f"**{h}**")

        for idx, row in df.iterrows():

            if search_query and search_query.lower() not in str(row).lower():
                continue

            row_cols = st.columns(column_widths)

            row_cols[0].write(row['Reference_ID'])
            row_cols[1].write(row['Candidate Name'])
            row_cols[2].write(row['Contact Number'])
            row_cols[3].write(row['Job Title'])
            row_cols[4].write(row['Interview Date'])
            row_cols[5].write(row['Status'])
            row_cols[6].write(row['Joining Date'])
            row_cols[7].write(row['SR Date'])

            if row_cols[8].button("📝", key=f"edit_{row['Reference_ID']}"):
                st.session_state.edit_id = row['Reference_ID']

        # -------- EDIT SIDEBAR --------
        if 'edit_id' in st.session_state:
            with st.sidebar:
                st.header(f"Update: {st.session_state.edit_id}")
                current_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]

                new_status = st.selectbox(
                    "Status",
                    ["Shortlisted", "Interviewed", "Selected", "Hold",
                     "Rejected", "Onboarded", "Left", "Not Joined"]
                )

                new_feedback = st.text_area("Feedback", value=current_row['Feedback'])

                if new_status == "Onboarded":
                    join_date = st.date_input("Joining Date")
                    c_master = pd.DataFrame(client_sheet.get_all_records())
                    sr_days = c_master[c_master['Client Name'] == current_row['Client Name']]['SR Days'].values[0]
                    sr_date = (join_date + timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                    st.info(f"Calculated SR Date: {sr_date}")

                if st.button("Update Sheet"):
                    gsheet_row_idx = df.index[df['Reference_ID'] == st.session_state.edit_id][0] + 2
                    cand_sheet.update_cell(gsheet_row_idx, 8, new_status)
                    cand_sheet.update_cell(gsheet_row_idx, 12, new_feedback)

                    if new_status == "Onboarded":
                        cand_sheet.update_cell(gsheet_row_idx, 10, join_date.strftime("%d-%m-%Y"))
                        cand_sheet.update_cell(gsheet_row_idx, 11, sr_date)

                    st.success("Updated!")
                    del st.session_state.edit_id
                    st.rerun()
