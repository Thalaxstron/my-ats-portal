import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# ---------------- ENTERPRISE CSS ----------------
st.markdown("""
<style>

.stApp {
    background:#f4f6f9;
}

/* ===== FIXED TOP PANEL ===== */
.fixed-top-panel {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: white;
    z-index: 999;
    padding: 15px 40px 10px 40px;
    box-shadow: 0px 3px 8px rgba(0,0,0,0.1);
}

/* ===== HEADER TEXT ===== */
.company {
    font-size:22px;
    font-weight:bold;
    color:#0d47a1;
}
.slogan {
    font-size:14px;
    color:#777;
}
.welcome {
    font-size:16px;
    margin-top:6px;
}
.target {
    background:#0d47a1;
    color:white;
    padding:6px 10px;
    border-radius:5px;
    font-size:13px;
    margin-top:6px;
}

/* ===== CONTROL PANEL ===== */
.control-panel {
    text-align:right;
}

/* ===== TABLE HEADER ===== */
.table-header {
    font-weight:bold;
    border-top:1px solid #eee;
    border-bottom:2px solid #ccc;
    padding:8px 0px;
    margin-top:15px;
}

/* ===== SCROLL AREA ===== */
.data-container {
    margin-top:320px;
    height:calc(100vh - 330px);
    overflow-y:auto;
    padding:0px 40px;
}

/* ===== DATA ROW ===== */
.data-row {
    background:white;
    padding:8px 0px;
    border-bottom:1px solid #eee;
}

/* ===== BUTTON ===== */
.stButton>button {
    background:#d32f2f !important;
    color:white !important;
    border-radius:6px;
    border:none;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
cand_sheet = sh.worksheet("ATS_Data")

def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1:
        return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:]
                 if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# ---------------- LOGIN (UNCHANGED) ----------------
if not st.session_state.logged_in:

    st.markdown("### TAKECARE MANPOWER SERVICES PVT LTD")
    st.markdown("##### ATS LOGIN")

    _, col, _ = st.columns([1,1.2,1])
    with col:
        u_mail = st.text_input("Email ID")
        u_pass = st.text_input("Password", type="password")

        if st.button("LOGIN", use_container_width=True):
            users_df = pd.DataFrame(user_sheet.get_all_records())
            users_df.columns = users_df.columns.str.strip()
            user_row = users_df[(users_df['Mail_ID']==u_mail) &
                                (users_df['Password'].astype(str)==u_pass)]
            if not user_row.empty:
                st.session_state.logged_in=True
                st.session_state.user_data=user_row.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Incorrect username or password")

# ---------------- DASHBOARD ----------------
else:

    u_data = st.session_state.user_data

    # ===== FIXED PANEL START =====
    st.markdown("<div class='fixed-top-panel'>", unsafe_allow_html=True)

    col1, col2 = st.columns([3,1])

    with col1:
        st.markdown("<div class='company'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
        st.markdown("<div class='slogan'>Successful HR Firm</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='welcome'>Welcome back, {u_data['Username']}!</div>", unsafe_allow_html=True)
        st.markdown("<div class='target'>📞 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    with col2:
        if st.button("Logout"):
            st.session_state.logged_in=False
            st.rerun()

        search_query = st.text_input("Search")

        if u_data['Role'] in ["TL","ADMIN"]:
            st.button("Filter")

        if st.button("+ New Shortlist"):
            st.session_state.open_popup=True

    # ===== TABLE HEADER =====
    header_cols = st.columns([1,1.5,1.5,1.6,1.4,1.2,1.3,1.3,1.2,1,1])
    headers = [
        "Ref ID","Candidate Name","Contact Number",
        "Position","Commitment / Interview Date",
        "Status","Onboarded Date","SR Date",
        "HR Name","Action","Whatsapp Invite"
    ]

    st.markdown("<div class='table-header'>", unsafe_allow_html=True)
    for col, head in zip(header_cols, headers):
        col.write(head)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
    # ===== FIXED PANEL END =====

    # ===== SCROLLABLE DATA AREA =====
    st.markdown("<div class='data-container'>", unsafe_allow_html=True)

    raw_data = cand_sheet.get_all_records()
    if raw_data:

        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()

        if u_data['Role']=="RECRUITER":
            df = df[df['HR Name']==u_data['Username']]

        now=datetime.now()
        df['Shortlisted Date']=pd.to_datetime(
            df['Shortlisted Date'],format="%d-%m-%Y",errors='coerce')

        df = df[~(
            (df['Status']=="Shortlisted") &
            (df['Shortlisted Date']<now-timedelta(days=7))
        )]

        for idx,row in df.iterrows():

            if search_query and search_query.lower() not in str(row).lower():
                continue

            r_cols = st.columns([1,1.5,1.5,1.6,1.4,1.2,1.3,1.3,1.2,1,1])

            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            r_cols[8].write(row['HR Name'])

            if r_cols[9].button("Edit", key=row['Reference_ID']):
                st.session_state.edit_id=row['Reference_ID']

            r_cols[10].write("📲")

    st.markdown("</div>", unsafe_allow_html=True)
