import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# ----------- UPDATED CSS (FREEZE HEADER ADDED ONLY) -----------
st.markdown("""
<style>

/* Background */
.stApp {
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
    background-attachment: fixed;
}

/* ----------- FREEZE HEADER (25%) ----------- */
.fixed-header {
    position: sticky;
    top: 0;
    background: white;
    z-index: 999;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 10px;
}

/* Scroll area */
.scroll-table {
    height: 65vh;
    overflow-y: auto;
}

/* Inputs white */
div[data-baseweb="input"] > div {
    background-color: white !important;
}

input, textarea {
    background-color: white !important;
    color: #0d47a1 !important;
    font-weight: bold !important;
}

.stButton > button {
    background-color: #d32f2f !important;
    color: white !important;
    border-radius: 8px;
    font-weight: bold;
    border: none;
}

.stButton > button:hover {
    background-color: #b71c1c !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

try:
    client = get_gsheet_client()
    sh = client.open("ATS_Cloud_Database")
    user_sheet = sh.worksheet("User_Master")
    client_sheet = sh.worksheet("Client_Master")
    cand_sheet = sh.worksheet("ATS_Data")
except Exception as e:
    st.error(f"Database Error: {e}")
    st.stop()

# --- 3. HELPER ---
def get_next_ref_id():
    all_ids = cand_sheet.col_values(1)
    if len(all_ids) <= 1:
        return "E00001"
    valid_ids = [int(val[1:]) for val in all_ids[1:]
                 if str(val).startswith("E") and str(val)[1:].isdigit()]
    return f"E{max(valid_ids)+1:05d}" if valid_ids else "E00001"

# --- 4. SESSION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. LOGIN ---
if not st.session_state.logged_in:

    st.markdown("<h1 style='text-align:center;color:white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;color:white;'>ATS LOGIN</h3>", unsafe_allow_html=True)

    _, col_m, _ = st.columns([1,1.2,1])
    with col_m:
        with st.container(border=True):
            u_mail = st.text_input("Email ID")
            u_pass = st.text_input("Password", type="password")

            if st.button("LOGIN", use_container_width=True):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                users_df.columns = users_df.columns.str.strip()

                user_row = users_df[
                    (users_df['Mail_ID'] == u_mail) &
                    (users_df['Password'].astype(str) == u_pass)
                ]

                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_data = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")

else:

    u_data = st.session_state.user_data

    # ================= FREEZE HEADER =================
    st.markdown("<div class='fixed-header'>", unsafe_allow_html=True)

    left, right = st.columns([3,1])

    # LEFT SIDE
    with left:
        st.markdown("## TAKECARE MANPOWER SERVICES PVT LTD")
        st.markdown("### Successful HR Firm")
        st.markdown(f"### Welcome back, {u_data['Username']}!")
        st.markdown("#### 📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining")

    # RIGHT SIDE
    with right:

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        search_query = st.text_input("Search")

        if u_data['Role'] in ["TL","ADMIN"]:
            st.button("Filter")

        if st.button("+ New Shortlist"):
            new_entry_popup()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")

    # ================= TABLE AREA (SCROLLABLE) =================
    st.markdown("<div class='scroll-table'>", unsafe_allow_html=True)

    raw_data = cand_sheet.get_all_records()
    if raw_data:
        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()

        if u_data['Role'] == "RECRUITER":
            df = df[df['HR Name'] == u_data['Username']]
        elif u_data['Role'] == "TL":
            users_df = pd.DataFrame(user_sheet.get_all_records())
            team = users_df[
                users_df['Report_To'] == u_data['Username']
            ]['Username'].tolist()
            df = df[df['HR Name'].isin(team + [u_data['Username']])]

        # -------- 11 COLUMN HEADER --------
        cols = st.columns([0.7,1.3,1.2,1.3,1.2,1.1,1.1,1.1,1,0.8,1])

        headers = [
            "Ref ID",
            "Candidate Name",
            "Contact Number",
            "Position / Job Title",
            "Commitment / Interview Date",
            "Status",
            "Onboarded Date",
            "SR Date",
            "HR Name",
            "Action",
            "Whatsapp Invite"
        ]

        for c,h in zip(cols,headers):
            c.markdown(f"**{h}**")

        # -------- DATA ROWS --------
        for idx,row in df.iterrows():

            row_cols = st.columns([0.7,1.3,1.2,1.3,1.2,1.1,1.1,1.1,1,0.8,1])

            row_cols[0].write(row.get('Reference_ID',""))
            row_cols[1].write(row.get('Candidate Name',""))
            row_cols[2].write(row.get('Contact Number',""))
            row_cols[3].write(row.get('Job Title',""))
            row_cols[4].write(row.get('Interview Date',""))
            row_cols[5].write(row.get('Status',""))
            row_cols[6].write(row.get('Joining Date',""))
            row_cols[7].write(row.get('SR Date',""))
            row_cols[8].write(row.get('HR Name',""))

            row_cols[9].button("📝", key=f"edit_{idx}")
            row_cols[10].write("📲")

    st.markdown("</div>", unsafe_allow_html=True)
