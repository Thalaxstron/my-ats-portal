import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Takecare ATS", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
}
.main-title {color:white;text-align:center;font-size:38px;font-weight:bold;}
.sub-title {color:white;text-align:center;font-size:22px;}
.target-bar {
    background:#1565c0;
    color:white;
    padding:8px;
    border-radius:5px;
    font-weight:bold;
}
input, select, textarea {
    color:#0d47a1 !important;
    font-weight:bold !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# GOOGLE SHEET CONNECTION
# -------------------------------------------------
def connect_gsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    return client.open("ATS_Cloud_Database")

sh = connect_gsheet()
user_sheet = sh.worksheet("User_Master")
data_sheet = sh.worksheet("ATS_Data")
client_sheet = sh.worksheet("Client_Master")

# -------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------
def get_next_ref():
    ids = data_sheet.col_values(1)
    if len(ids) <= 1:
        return "E00001"
    nums = [int(x[1:]) for x in ids[1:] if x.startswith("E")]
    return f"E{max(nums)+1:05d}"

def calculate_sr_date(client, position, joining_date):
    cm = pd.DataFrame(client_sheet.get_all_records())
    row = cm[(cm["Client Name"] == client) &
             (cm["Position"] == position)]
    if not row.empty:
        sr_days = int(row["SR Days"].values[0])
        return joining_date + timedelta(days=sr_days)
    return None

# -------------------------------------------------
# SESSION
# -------------------------------------------------
if "logged" not in st.session_state:
    st.session_state.logged = False

# -------------------------------------------------
# LOGIN PAGE
# -------------------------------------------------
if not st.session_state.logged:

    st.markdown("<div class='main-title'>TAKECARE MANPOWER SERVICES PVT LTD</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>ATS LOGIN</div>", unsafe_allow_html=True)

    _, c, _ = st.columns([1,1.2,1])
    with c:
        st.markdown("###")
        email = st.text_input("Email ID")
        show_pass = st.checkbox("Show Password")
        password = st.text_input("Password", type="default" if show_pass else "password")
        remember = st.checkbox("Remember Me")

        if st.button("LOGIN", use_container_width=True):
            users = pd.DataFrame(user_sheet.get_all_records())
            row = users[(users["Mail_ID"] == email) &
                        (users["Password"] == password)]
            if not row.empty:
                st.session_state.logged = True
                st.session_state.user = row.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Incorrect username or password")

        st.caption("Forgot password? Contact Admin")

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
else:

    user = st.session_state.user

    # HEADER
    left, s_col, f_col, r_col = st.columns([4,1,1,1])

    with left:
        st.markdown("## TAKECARE MANPOWER SERVICES PVT LTD")
        st.markdown("### Successful HR Firm")
        st.markdown(f"### Welcome back, {user['Username']}!")
        st.markdown("<div class='target-bar'>📞 Target for Today: 80+ Telescreening Calls / 3-5 Interview / 1+ Joining</div>", unsafe_allow_html=True)

    with s_col:
        search = st.text_input("🔍 Search")

    with f_col:
        if user["Role"] != "RECRUITER":
            filter_type = st.selectbox("Filter",
                ["All","Client Wise","Recruiter Wise","Date Wise"])

    with r_col:
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

    # NEW SHORTLIST BUTTON
    col_space, col_btn = st.columns([5,1])
    with col_btn:
        open_form = st.button("+ New Shortlist")

    # LOAD DATA
    df = pd.DataFrame(data_sheet.get_all_records())

    if not df.empty:

        # ROLE FILTER
        if user["Role"] == "RECRUITER":
            df = df[df["HR Name"] == user["Username"]]

        if user["Role"] == "TL":
            users = pd.DataFrame(user_sheet.get_all_records())
            team = users[users["Report_To"] == user["Username"]]["Username"].tolist()
            df = df[df["HR Name"].isin(team + [user["Username"]])]

        # SEARCH
        if search:
            df = df[df.astype(str).apply(lambda x: search.lower() in x.to_string().lower(), axis=1)]

        # FILTER LOGIC
        if user["Role"] != "RECRUITER":
            if filter_type == "Client Wise":
                client_sel = st.selectbox("Select Client", df["Client Name"].unique())
                df = df[df["Client Name"] == client_sel]

            if filter_type == "Recruiter Wise":
                rec_sel = st.selectbox("Select Recruiter", df["HR Name"].unique())
                df = df[df["HR Name"] == rec_sel]

            if filter_type == "Date Wise":
                from_d = st.date_input("From")
                to_d = st.date_input("To")
                df["Shortlisted Date"] = pd.to_datetime(df["Shortlisted Date"], errors='coerce')
                df = df[(df["Shortlisted Date"] >= pd.to_datetime(from_d)) &
                        (df["Shortlisted Date"] <= pd.to_datetime(to_d))]

        # AUTO HIDE RULES
        now = datetime.now()
        df["Shortlisted Date"] = pd.to_datetime(df["Shortlisted Date"], errors='coerce')
        df["Interview Date"] = pd.to_datetime(df["Interview Date"], errors='coerce')

        df = df[~((df["Status"]=="Shortlisted") &
                  (df["Shortlisted Date"] < now - timedelta(days=7)))]

        df = df[~((df["Status"].isin(["Selected","Rejected","Hold"])) &
                  (df["Interview Date"] < now - timedelta(days=30)))]

        df = df[~((df["Status"].isin(["Left","Not Joined"])) &
                  (df["Shortlisted Date"] < now - timedelta(days=7)))]

        st.dataframe(df, use_container_width=True)

    # -------------------------------------------------
    # NEW SHORTLIST FORM
    # -------------------------------------------------
    if open_form:
        with st.form("new_entry"):
            ref = get_next_ref()
            st.write("Reference ID:", ref)
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            cm = pd.DataFrame(client_sheet.get_all_records())
            client_sel = st.selectbox("Client Name", cm["Client Name"].unique())
            pos = st.selectbox("Position",
                cm[cm["Client Name"]==client_sel]["Position"])
            commit_date = st.date_input("Commitment Date")
            feedback = st.text_area("Feedback")
            send_wa = st.checkbox("Send WhatsApp Invite")

            submit = st.form_submit_button("Submit")

            if submit:
                today = datetime.now().strftime("%d-%m-%Y")
                data_sheet.append_row([
                    ref, today, name, phone, client_sel,
                    pos, commit_date.strftime("%d-%m-%Y"),
                    "Shortlisted", user["Username"], "", "", feedback
                ])

                if send_wa:
                    row = cm[(cm["Client Name"]==client_sel) &
                             (cm["Position"]==pos)].iloc[0]

                    msg = f"""
Dear {name},

Congratulations, upon reviewing your application, we would like to invite you for Direct interview and get to know you better.

Reference: Takecare Manpower Services Pvt Ltd
Position: {pos}
Interview Date: {commit_date.strftime("%d-%m-%Y")}
Interview Time: 10.30 AM
Interview venue: {row['Address']}
Map Location: {row['Map Link']}
Contact Person: {row['Contact Person']}

Please Let me know when you arrive at the interview location.

Regards,
{user['Username']}
Takecare HR Team
"""
                    url = f"https://wa.me/91{phone}?text={urllib.parse.quote(msg)}"
                    st.markdown(f"[Click here to Send WhatsApp Invite]({url})")

                st.success("Shortlisted Successfully")
                st.rerun()

    # -------------------------------------------------
    # CLIENT MASTER (ADMIN ONLY)
    # -------------------------------------------------
    if user["Role"] == "ADMIN":
        with st.expander("Client Master Management"):
            with st.form("add_client"):
                cname = st.text_input("Client Name")
                pos = st.text_input("Position")
                addr = st.text_area("Address")
                mapl = st.text_input("Map Link")
                cp = st.text_input("Contact Person")
                srd = st.number_input("SR Days", min_value=1)
                add = st.form_submit_button("Add Client")

                if add:
                    client_sheet.append_row(
                        [cname,pos,addr,mapl,cp,srd])
                    st.success("Client Added")
