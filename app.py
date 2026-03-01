import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(page_title="Takecare ATS", layout="wide")

# ---------------------------------------------------
# ENTERPRISE UI CSS (Frozen Header + Red Blue Theme)
# ---------------------------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#c62828,#0d47a1);
    background-attachment: fixed;
}

/* LOGIN PAGE */
.login-title {
    text-align:center;
    color:white;
    font-size:40px;
    font-weight:bold;
}
.login-sub {
    text-align:center;
    color:white;
    font-size:26px;
    margin-bottom:20px;
}

/* INPUT STYLING */
input, textarea, select {
    background:white !important;
    color:#0d47a1 !important;
    font-weight:bold !important;
}

/* BUTTONS */
.stButton>button {
    border-radius:8px;
    font-weight:bold;
}

/* FROZEN HEADER */
.fixed-header {
    position:fixed;
    top:0;
    left:0;
    right:0;
    background:white;
    padding:15px 25px;
    z-index:999;
    border-bottom:3px solid #0d47a1;
}

/* SCROLL AREA */
.scroll-data {
    margin-top:320px;
    max-height:550px;
    overflow-y:auto;
    padding:10px;
}

/* COLUMN HEADER STYLE */
.col-head {
    font-weight:bold;
    color:#0d47a1;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# GOOGLE SHEET CONNECTION
# ---------------------------------------------------
def connect():
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    return authorize(creds)

client = connect()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
client_sheet = sh.worksheet("Client_Master")
data_sheet = sh.worksheet("ATS_Data")

# ---------------------------------------------------
# REFERENCE ID GENERATOR
# ---------------------------------------------------
def next_ref():
    ids = data_sheet.col_values(1)
    if len(ids) <= 1:
        return "E0001"
    nums = [int(x[1:]) for x in ids[1:] if x.startswith("E")]
    return f"E{max(nums)+1:04d}"

# ---------------------------------------------------
# SESSION
# ---------------------------------------------------
if "login" not in st.session_state:
    st.session_state.login = False

# ---------------------------------------------------
# LOGIN PAGE
# ---------------------------------------------------
if not st.session_state.login:

    st.markdown("<div class='login-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='login-sub'>ATS LOGIN</div>", unsafe_allow_html=True)

    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        with st.container(border=True):
            mail = st.text_input("Email ID")
            pwd = st.text_input("Password", type="password")
            st.checkbox("Remember Me")
            if st.button("LOGIN", use_container_width=True):
                df = pd.DataFrame(user_sheet.get_all_records())
                user = df[(df["Mail_ID"]==mail) & (df["Password"].astype(str)==pwd)]
                if not user.empty:
                    st.session_state.login=True
                    st.session_state.user=user.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Incorrect username or password")
            st.caption("Forgot password? Contact Admin")

# ---------------------------------------------------
# DASHBOARD
# ---------------------------------------------------
else:

    u = st.session_state.user

    # FROZEN HEADER SECTION
    st.markdown(f"""
    <div class="fixed-header">
        <div style="display:flex; justify-content:space-between;">
            <div>
                <div style="font-size:25px; font-weight:bold;">Takecare Manpower Services Pvt Ltd</div>
                <div style="font-size:20px;">Successful HR Firm</div>
                <div style="font-size:18px;">Welcome back, {u['Username']}!</div>
                <div style="font-size:18px; color:#0d47a1;">
                Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining
                </div>
            </div>
            <div>
    """, unsafe_allow_html=True)

    if st.button("Logout"):
        st.session_state.login=False
        st.rerun()

    search = st.text_input("Search")

    if u["Role"] in ["ADMIN","TL"]:
        filter_btn = st.button("Filter")

    new_btn = st.button("New Shortlist")

    st.markdown("</div></div></div>", unsafe_allow_html=True)

    # ---------------------------------------------------
    # NEW SHORTLIST POPUP
    # ---------------------------------------------------
    if new_btn:
        with st.dialog("New Shortlist Entry"):
            ref = next_ref()
            st.write("Reference ID:", ref)
            sdate = datetime.now().date()
            cname = st.text_input("Candidate Name")
            cphone = st.text_input("Contact Number")
            cdf = pd.DataFrame(client_sheet.get_all_records())
            client_name = st.selectbox("Client Name", cdf["Client Name"].unique())
            positions = cdf[cdf["Client Name"]==client_name]["Position"]
            pos = st.selectbox("Position", positions)
            commit = st.date_input("Commitment Date")
            status="Shortlisted"
            feedback = st.text_area("Feedback")
            col1,col2=st.columns(2)
            if col1.button("Submit"):
                data_sheet.append_row([
                    ref,str(sdate),cname,cphone,
                    client_name,pos,str(commit),
                    status,"","",u["Username"],feedback
                ])
                st.rerun()
            if col2.button("Cancel"):
                st.rerun()

    # ---------------------------------------------------
    # LOAD DATA
    # ---------------------------------------------------
    df = pd.DataFrame(data_sheet.get_all_records())

    # ROLE FILTER
    if u["Role"]=="RECRUITER":
        df = df[df["HR Name"]==u["Username"]]

    # SEARCH
    if search:
        df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]

    # AUTO EXPIRY LOGIC
    today=datetime.now()
    if not df.empty:
        df["Shortlisted Date"]=pd.to_datetime(df["Shortlisted Date"], errors='coerce')
        df=df[~((df["Status"]=="Shortlisted") &
                (df["Shortlisted Date"]<today-timedelta(days=7)))]

    # ---------------------------------------------------
    # SCROLLABLE DATA
    # ---------------------------------------------------
    st.markdown("<div class='scroll-data'>", unsafe_allow_html=True)

    cols = st.columns(11)
    headers=["Ref ID","Candidate","Contact","Client","Position",
             "Commitment Date","Status","Onboarded Date",
             "SR Date","Action","WhatsApp"]
    for col,h in zip(cols,headers):
        col.markdown(f"<div class='col-head'>{h}</div>", unsafe_allow_html=True)

    for i,row in df.iterrows():
        r=st.columns(11)
        r[0].write(row["Reference_ID"])
        r[1].write(row["Candidate Name"])
        r[2].write(row["Contact Number"])
        r[3].write(row["Client Name"])
        r[4].write(row["Position"])
        r[5].write(row["Commitment Date"])
        r[6].write(row["Status"])
        r[7].write(row.get("Onboarded Date",""))
        r[8].write(row.get("SR Date",""))

        if r[9].button("✏", key=i):
            with st.dialog("Update Status"):
                new_status=st.selectbox("Status",
                ["Interviewed","Selected","Hold","Rejected",
                 "Onboarded","Left","Project Success"])
                feedback=st.text_area("Feedback")
                if new_status=="Onboarded":
                    join=st.date_input("Onboarded Date")
                    cm=pd.DataFrame(client_sheet.get_all_records())
                    sr_days=int(cm[cm["Client Name"]==row["Client Name"]]["SR Days"].values[0])
                    sr=(join+timedelta(days=sr_days)).strftime("%Y-%m-%d")
                if st.button("Submit Update"):
                    idx=i+2
                    data_sheet.update_cell(idx,7,new_status)
                    data_sheet.update_cell(idx,12,feedback)
                    if new_status=="Onboarded":
                        data_sheet.update_cell(idx,8,str(join))
                        data_sheet.update_cell(idx,9,sr)
                    st.rerun()

        # WHATSAPP LINK
        msg=f"""
Dear {row['Candidate Name']},

Congratulations, upon reviewing your application, we would like to invite you for Direct interview.

Reference: Takecare Manpower Services Pvt Ltd
Position: {row['Position']}
Interview Date: {row['Commitment Date']}
Interview Time: 10.30 AM

Regards,
{u['Username']}
Takecare HR Team
"""
        link="https://wa.me/91"+str(row["Contact Number"])+"?text="+urllib.parse.quote(msg)
        r[10].markdown(f"[Send]({link})", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
