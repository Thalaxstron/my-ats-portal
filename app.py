import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="Takecare ATS", layout="wide")

st.markdown("""
<style>
.stApp {
background: linear-gradient(135deg,#d32f2f,#0d47a1);
background-attachment: fixed;
}
input, select, textarea {
color:#0d47a1 !important;
font-weight:bold !important;
}
.big-title{
color:white;
text-align:center;
font-size:40px;
font-weight:bold;
}
.sub{
color:white;
text-align:center;
font-size:25px;
}
.white-box{
background:white;
padding:25px;
border-radius:12px;
}
.target{
background:#1565c0;
color:white;
padding:10px;
border-radius:8px;
font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ------------------ GOOGLE SHEET CONNECTION ------------------
def connect():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

gc = connect()
sh = gc.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
data_sheet = sh.worksheet("ATS_Data")
client_sheet = sh.worksheet("Client_Master")

# ------------------ HELPER ------------------
def next_ref():
    ids = data_sheet.col_values(1)
    valid = [int(x[1:]) for x in ids[1:] if x.startswith("E")]
    if not valid:
        return "E00001"
    return f"E{max(valid)+1:05d}"

# ------------------ SESSION ------------------
if "login" not in st.session_state:
    st.session_state.login = False

# =========================================================
# ====================== LOGIN PAGE =======================
# =========================================================
if not st.session_state.login:

    st.markdown("<div class='big-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub'>ATS LOGIN</div>", unsafe_allow_html=True)

    _,c,_ = st.columns([1,1.2,1])
    with c:
        with st.container(border=True):
            mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            remember = st.checkbox("Remember Me")
            if st.button("LOGIN", use_container_width=True):
                users = pd.DataFrame(user_sheet.get_all_records())
                row = users[(users["Mail_ID"]==mail) & (users["Password"]==pwd)]
                if not row.empty:
                    st.session_state.login = True
                    st.session_state.user = row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# =========================================================
# ===================== DASHBOARD =========================
# =========================================================
else:

    user = st.session_state.user
    role = user["Role"]
    username = user["Username"]

    # ------------ FROZEN HEADER ------------
    col1,col2,col3 = st.columns([4,2,1])
    with col1:
        st.markdown("<h3 style='color:white;'>Takecare Manpower Service Pvt Ltd</h3>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:white;'>Successful HR Firm</h5>", unsafe_allow_html=True)
        st.markdown(f"<h6 style='color:white;'>Welcome back, {username}!</h6>", unsafe_allow_html=True)
    with col3:
        if st.button("Logout"):
            st.session_state.login=False
            st.rerun()

    st.markdown("<div class='target'>Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    # ---------------- BUTTONS ----------------
    colA,colB,colC = st.columns([1,1,1])

    with colA:
        if st.button("New Shortlist"):
            st.session_state.add=True

    with colB:
        search = st.text_input("Search")

    with colC:
        if role in ["ADMIN","TL"]:
            if st.button("Filter"):
                st.session_state.filter=True

    # =========================================================
    # ================= NEW SHORTLIST POPUP ===================
    # =========================================================
    if "add" in st.session_state:

        with st.container(border=True):
            ref = next_ref()
            st.write("Reference ID:", ref)
            today = datetime.now().strftime("%d-%m-%Y")

            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")

            client_df = pd.DataFrame(client_sheet.get_all_records())
            client_list = sorted(client_df["Client Name"].unique())
            sel_client = st.selectbox("Client Name", client_list)

            positions = client_df[client_df["Client Name"]==sel_client]["Position"]
            sel_pos = st.selectbox("Position", positions)

            comm_date = st.date_input("Commitment Date")
            feedback = st.text_area("Feedback")

            colx,coly = st.columns(2)
            with colx:
                if st.button("Submit"):
                    data_sheet.append_row([
                        ref,today,name,phone,
                        sel_client,sel_pos,
                        comm_date.strftime("%d-%m-%Y"),
                        "Shortlisted",
                        username,"","",feedback
                    ])
                    st.success("Saved")
                    del st.session_state.add
                    st.rerun()
            with coly:
                if st.button("Cancel"):
                    del st.session_state.add
                    st.rerun()

    # =========================================================
    # ================= LOAD DATA =============================
    # =========================================================
    df = pd.DataFrame(data_sheet.get_all_records())

    # ROLE FILTER
    if role=="RECRUITER":
        df = df[df["HR Name"]==username]
    elif role=="TL":
        users = pd.DataFrame(user_sheet.get_all_records())
        team = users[users["Report_To"]==username]["Username"]
        df = df[df["HR Name"].isin(team.tolist()+[username])]

    # SEARCH
    if search:
        df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

    # AUTO DELETE VISUAL LOGIC
    now = datetime.now()
    df["Shortlisted Date"]=pd.to_datetime(df["Shortlisted Date"],errors="coerce",dayfirst=True)

    df = df[~((df["Status"]=="Shortlisted") &
              (df["Shortlisted Date"]<now-timedelta(days=7)))]

    # =========================================================
    # ================= DISPLAY TABLE =========================
    # =========================================================
    st.dataframe(df,use_container_width=True)

    # =========================================================
    # ================= EDIT STATUS ===========================
    # =========================================================
    edit_id = st.text_input("Enter Reference ID to Edit")

    if edit_id:
        row = df[df["Reference_ID"]==edit_id]
        if not row.empty:
            st.write("Editing:", edit_id)

            new_status = st.selectbox("Status",
            ["Interviewed","Selected","Hold","Rejected",
             "Onboarded","Left","Project Success"])

            new_feedback = st.text_area("Feedback",row.iloc[0]["Feedback"])

            join_date=None
            if new_status=="Onboarded":
                join_date = st.date_input("Onboarded Date")

            if st.button("Update"):
                sheet_row = df.index[df["Reference_ID"]==edit_id][0]+2
                data_sheet.update_cell(sheet_row,8,new_status)
                data_sheet.update_cell(sheet_row,12,new_feedback)

                if new_status=="Onboarded":
                    data_sheet.update_cell(sheet_row,10,join_date.strftime("%d-%m-%Y"))

                    c_master = pd.DataFrame(client_sheet.get_all_records())
                    sr_days = int(c_master[c_master["Client Name"]==
                              row.iloc[0]["Client Name"]]["SR Days"].values[0])

                    sr_date = join_date+timedelta(days=sr_days)
                    data_sheet.update_cell(sheet_row,11,
                                           sr_date.strftime("%d-%m-%Y"))

                st.success("Updated")
                st.rerun()

    # =========================================================
    # ================= WHATSAPP LINK =========================
    # =========================================================
    if not df.empty:
        last = df.iloc[0]
        if st.button("Send WhatsApp Invite (Top Row)"):
            c_master = pd.DataFrame(client_sheet.get_all_records())
            info = c_master[(c_master["Client Name"]==last["Client Name"]) &
                            (c_master["Position"]==last["Job Title"])].iloc[0]

            msg = f"""Dear {last['Candidate Name']},

Congratulations, Direct interview invite.

Position: {last['Job Title']}
Interview Date: {last['Interview Date']}
Interview Time: 10.30 AM
Interview Venue: {info['Address']}
Map Link: {info['Map Link']}
Contact Person: {info['Contact Person']}

Regards,
{username}
Takecare HR Team"""

            url = f"https://wa.me/91{last['Contact Number']}?text={urllib.parse.quote(msg)}"
            st.markdown(f"[Click to Open WhatsApp]({url})",unsafe_allow_html=True)
