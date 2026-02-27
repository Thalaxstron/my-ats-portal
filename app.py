import streamlit as st
import pandas as pd
import gspread
import urllib.parse
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(page_title="TAKECARE ATS", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#d32f2f,#0d47a1);
    background-attachment: fixed;
}
input, textarea, select {
    background-color:white !important;
    color:#0d47a1 !important;
    font-weight:bold !important;
}
.main-title{
    text-align:center;
    color:white;
    font-size:38px;
    font-weight:bold;
}
.sub-title{
    text-align:center;
    color:white;
    font-size:24px;
}
.target-bar{
    background:#1565c0;
    color:white;
    padding:8px;
    border-radius:6px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# GOOGLE CONNECTION
# =========================================================
def connect():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    return gspread.authorize(creds)

client = connect()
sh = client.open("ATS_Cloud_Database")

user_sheet = sh.worksheet("User_Master")
data_sheet = sh.worksheet("ATS_Data")
client_sheet = sh.worksheet("Client_Master")
log_sheet = sh.worksheet("Activity_Logs")

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def next_ref():
    ids = data_sheet.col_values(1)
    nums = [int(x[1:]) for x in ids[1:] if str(x).startswith("E")]
    return f"E{max(nums)+1:05d}" if nums else "E00001"

def add_log(user, action, cand, details):
    log_sheet.append_row([
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        user, action, cand, details
    ])

def load_data():
    df = pd.DataFrame(data_sheet.get_all_records())
    df.columns = df.columns.str.strip()
    return df

# =========================================================
# SESSION
# =========================================================
if "logged" not in st.session_state:
    st.session_state.logged = False

# =========================================================
# LOGIN PAGE
# =========================================================
if not st.session_state.logged:

    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1,1.2,1])
    with col:
        email = st.text_input("Email ID")
        show = st.checkbox("Show Password")
        password = st.text_input("Password", type="default" if show else "password")
        remember = st.checkbox("Remember Me")

        if st.button("LOGIN", use_container_width=True):
            users = pd.DataFrame(user_sheet.get_all_records())
            users.columns = users.columns.str.strip()
            row = users[(users["Mail_ID"]==email) &
                        (users["Password"].astype(str)==password)]
            if not row.empty:
                st.session_state.logged = True
                st.session_state.user = row.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Incorrect username or password")

        st.caption("Forgot password? Contact Admin")

# =========================================================
# DASHBOARD
# =========================================================
else:

    user = st.session_state.user
    df = load_data()

    # ---------------- HEADER ----------------
    left, search_col, filter_col, logout_col = st.columns([4,1.5,1,0.8])

    with left:
        st.markdown("## TAKECARE MANPOWER SERVICES PVT LTD")
        st.markdown("### Successful HR Firm")
        st.markdown(f"### Welcome back, {user['Username']}!")
        st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    with search_col:
        search = st.text_input("Search")

    with filter_col:
        open_filter = False
        if user["Role"] in ["ADMIN","TL"]:
            open_filter = st.button("Filter")

    with logout_col:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # =====================================================
    # ROLE FILTER
    # =====================================================
    if user["Role"]=="RECRUITER":
        df = df[df["HR Name"]==user["Username"]]

    if user["Role"]=="TL":
        users = pd.DataFrame(user_sheet.get_all_records())
        team = users[users["Report_To"]==user["Username"]]["Username"].tolist()
        df = df[df["HR Name"].isin(team+[user["Username"]])]

    # =====================================================
    # AUTO DELETE DISPLAY RULES
    # =====================================================
    now = datetime.now()
    df["Shortlisted Date"] = pd.to_datetime(df["Shortlisted Date"], errors="coerce", dayfirst=True)
    df["Interview Date"] = pd.to_datetime(df["Interview Date"], errors="coerce", dayfirst=True)

    df = df[~((df["Status"]=="Shortlisted") &
              (df["Shortlisted Date"] < now - timedelta(days=7)))]

    df = df[~((df["Status"].isin(["Interviewed","Selected","Rejected","Hold"])) &
              (df["Interview Date"] < now - timedelta(days=30)))]

    df = df[~((df["Status"].isin(["Left","Not Joined"])) &
              (df["Interview Date"] < now - timedelta(days=3)))]

    # =====================================================
    # SEARCH
    # =====================================================
    if search:
        df = df[df.astype(str).apply(lambda x: search.lower() in x.to_string().lower(), axis=1)]

    # =====================================================
    # DATA TABLE
    # =====================================================
    st.dataframe(df, use_container_width=True)

    # =====================================================
    # DOWNLOAD (ADMIN ONLY)
    # =====================================================
    if user["Role"]=="ADMIN":
        st.download_button("Download Report", df.to_csv(index=False), "ATS_Report.csv")

    # =====================================================
    # NEW SHORTLIST POPUP
    # =====================================================
    if st.button("+ New Shortlist"):

        with st.form("new_form"):

            ref = next_ref()
            today = datetime.now().strftime("%d-%m-%Y")

            st.write("Reference ID:", ref)
            st.write("Shortlisted Date:", today)

            c1,c2 = st.columns(2)

            with c1:
                name = st.text_input("Candidate Name")
                phone = st.text_input("Contact Number")
                client_list = list(set(client_sheet.col_values(1)[1:]))
                client_name = st.selectbox("Client Name", client_list)

            with c2:
                pos_df = pd.DataFrame(client_sheet.get_all_records())
                positions = pos_df[pos_df["Client Name"]==client_name]["Position"]
                position = st.selectbox("Position", positions)
                commit = st.date_input("Commitment Date")
                feedback = st.text_area("Feedback")
                send_wa = st.checkbox("WhatsApp Invite")

            submit = st.form_submit_button("Submit")
            cancel = st.form_submit_button("Cancel")

            if submit:

                data_sheet.append_row([
                    ref,today,name,phone,client_name,
                    position,commit.strftime("%d-%m-%Y"),
                    "Shortlisted",user["Username"],"", "",feedback
                ])

                add_log(user["Username"],"New Entry",name,"Shortlisted")

                if send_wa:
                    info = pos_df[(pos_df["Client Name"]==client_name)&
                                  (pos_df["Position"]==position)].iloc[0]

                    msg=f"""Dear {name},

Congratulations, upon reviewing your application, we would like to invite you for Direct interview and get to know you better.

Reference: Takecare Manpower Services Pvt Ltd
Position: {position}
Interview Date: {commit.strftime("%d-%m-%Y")}
Interview Time: 10.30 Am
Interview venue: {info['Address']}
Map Location: {info['Map Link']}
Contact Person: {info['Contact Person']}

Please Let me know when you arrive at the interview location. All the best....

Regards,
{user['Username']}
Takecare HR Team"""

                    wa=f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                    st.markdown(f"[Send WhatsApp]({wa})")

                st.success("Saved Successfully")
                st.rerun()

            if cancel:
                st.rerun()
