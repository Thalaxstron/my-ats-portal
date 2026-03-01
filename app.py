import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

st.set_page_config(page_title="Takecare Manpower ATS", layout="wide")

# ---------------- CSS ----------------
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%) !important;
    background-attachment: fixed;
}

.main-title {color:white;font-size:28px;font-weight:bold;margin-bottom:0px;}
.sub-slogan {color:white;font-size:16px;margin-bottom:5px;}
.welcome {color:white;font-size:20px;margin-bottom:5px;}
.target-bar {background:#1565c0;color:white;padding:8px;border-radius:5px;font-weight:bold;margin-bottom:10px;}

.header-row {
    position: sticky;
    top: 0;
    background: white;
    z-index: 999;
    font-weight: bold;
    border-bottom: 2px solid #ccc;
    padding:5px 0px;
}

.data-row {
    background:white;
    padding:5px 0px;
}

.stButton>button {
    background:#d32f2f !important;
    color:white !important;
    border-radius:6px;
    border:none;
}

</style>
""", unsafe_allow_html=True)

# ---------------- DB ----------------
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

# ---------------- LOGIN ----------------
if not st.session_state.logged_in:

    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-slogan'>Successful HR Firm</div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1,1.2,1])
    with col:
        u_mail = st.text_input("Email")
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
                st.error("Invalid Credentials")

# ---------------- DASHBOARD ----------------
else:

    u_data = st.session_state.user_data

    # ----------- HEADER LAYOUT -----------
    left, right = st.columns([4,1])

    with left:
        st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-slogan'>Successful HR Firm</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='welcome'>Welcome back, {u_data['Username']}!</div>", unsafe_allow_html=True)
        st.markdown("<div class='target-bar'>Target for Today: 📞 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    with right:
        if st.button("Logout"):
            st.session_state.logged_in=False
            st.rerun()

        search_query = st.text_input("Search")

        if u_data['Role'] in ["TL","ADMIN"]:
            st.button("Filter")

        if st.button("+ New Shortlist"):
            st.session_state.open_popup=True

    # ---------------- POPUP ----------------
    @st.dialog("Add New Candidate")
    def new_entry_popup():
        ref_id = get_next_ref_id()
        st.write(f"Ref ID: {ref_id}")
        c_name = st.text_input("Candidate Name")
        c_phone = st.text_input("Contact")
        c_master = pd.DataFrame(client_sheet.get_all_records())
        sel_client = st.selectbox("Client Name",
                                  ["-- Select --"] +
                                  sorted(c_master['Client Name'].unique()))
        pos_options=[]
        if sel_client!="-- Select --":
            pos_options = c_master[c_master['Client Name']==sel_client]['Position']
        sel_pos = st.selectbox("Position", pos_options)
        comm_date = st.date_input("Commitment Date")
        feedback = st.text_area("Feedback")

        if st.button("Submit"):
            today=datetime.now().strftime("%d-%m-%Y")
            cand_sheet.append_row([
                ref_id,today,c_name,c_phone,sel_client,
                sel_pos,comm_date.strftime("%d-%m-%Y"),
                "Shortlisted",u_data['Username'],"","",feedback
            ])
            st.success("Saved")
            st.rerun()

    if 'open_popup' in st.session_state:
        new_entry_popup()
        del st.session_state.open_popup

    # ---------------- TABLE ----------------
    raw_data = cand_sheet.get_all_records()
    if raw_data:

        df = pd.DataFrame(raw_data)
        df.columns = df.columns.str.strip()

        now=datetime.now()
        df['Shortlisted Date']=pd.to_datetime(
            df['Shortlisted Date'],format="%d-%m-%Y",errors='coerce')

        df = df[~(
            (df['Status']=="Shortlisted") &
            (df['Shortlisted Date']<now-timedelta(days=7))
        )]

        column_widths=[1,1.8,1.5,1.6,1.4,1.2,1.3,1.3,1.2,1,1]

        headers=[
            "Ref ID","Candidate Name","Contact Number",
            "Position / Job Title","Commitment Date",
            "Status","Onboarded Date","SR Date",
            "HR Name","Action","Whatsapp Invite"
        ]

        st.markdown("<div class='header-row'>",unsafe_allow_html=True)
        cols=st.columns(column_widths)
        for c,h in zip(cols,headers):
            c.write(h)
        st.markdown("</div>",unsafe_allow_html=True)

        for idx,row in df.iterrows():

            if search_query and search_query.lower() not in str(row).lower():
                continue

            st.markdown("<div class='data-row'>",unsafe_allow_html=True)
            r_cols=st.columns(column_widths)

            r_cols[0].write(row['Reference_ID'])
            r_cols[1].write(row['Candidate Name'])
            r_cols[2].write(row['Contact Number'])
            r_cols[3].write(row['Job Title'])
            r_cols[4].write(row['Interview Date'])
            r_cols[5].write(row['Status'])
            r_cols[6].write(row['Joining Date'])
            r_cols[7].write(row['SR Date'])
            r_cols[8].write(row['HR Name'])

            if r_cols[9].button("Edit",key=row['Reference_ID']):
                st.session_state.edit_id=row['Reference_ID']

            r_cols[10].write("📲")

            st.markdown("</div>",unsafe_allow_html=True)

    # ------------- EDIT SIDEBAR (UNCHANGED LOGIC) -------------
    if 'edit_id' in st.session_state:
        with st.sidebar:
            current_row=df[df['Reference_ID']==st.session_state.edit_id].iloc[0]
            new_status=st.selectbox("Status",
            ["Shortlisted","Interviewed","Selected","Hold",
             "Rejected","Onboarded","Left","Not Joined"])

            new_feedback=st.text_area("Feedback",
                                      value=current_row['Feedback'])

            if new_status=="Onboarded":
                join_date=st.date_input("Joining Date")
                c_master=pd.DataFrame(client_sheet.get_all_records())
                sr_days=c_master[
                    c_master['Client Name']==current_row['Client Name']
                ]['SR Days'].values[0]
                sr_date=(join_date+timedelta(days=int(sr_days))).strftime("%d-%m-%Y")
                st.info(f"SR Date: {sr_date}")

            if st.button("Update Sheet"):
                gsheet_row_idx=df.index[
                    df['Reference_ID']==st.session_state.edit_id
                ][0]+2

                cand_sheet.update_cell(gsheet_row_idx,8,new_status)
                cand_sheet.update_cell(gsheet_row_idx,12,new_feedback)

                if new_status=="Onboarded":
                    cand_sheet.update_cell(gsheet_row_idx,10,
                                           join_date.strftime("%d-%m-%Y"))
                    cand_sheet.update_cell(gsheet_row_idx,11,sr_date)

                st.success("Updated")
                del st.session_state.edit_id
                st.rerun()
