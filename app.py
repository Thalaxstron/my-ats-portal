import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
from gspread import authorize
from google.oauth2.service_account import Credentials

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="TAKECARE ATS", layout="wide")

# =====================================================
# RED BLUE ENTERPRISE THEME
# =====================================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #c62828 0%, #0d47a1 100%);
    color: white;
}
.block-container {padding-top:2rem;}
input, textarea {
    color: black !important;
}
.stButton>button {
    background-color:#c62828;
    color:white;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# GOOGLE SHEET CONNECTION
# =====================================================
@st.cache_resource
def connect():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    return authorize(creds)

client = connect()
sheet = client.open("ATS_Cloud_Database")
user_ws = sheet.worksheet("User_Master")
ats_ws = sheet.worksheet("ATS_Data")
client_ws = sheet.worksheet("Client_Master")
log_ws = sheet.worksheet("Activity_Logs")

# =====================================================
# SESSION STATE
# =====================================================
if "login" not in st.session_state:
    st.session_state.login = False

# =====================================================
# REF ID GENERATOR
# =====================================================
def generate_ref():
    data = ats_ws.col_values(1)
    ids = [int(x[1:]) for x in data[1:] if x.startswith("E")]
    if not ids:
        return "E00001"
    return f"E{max(ids)+1:05d}"

# =====================================================
# SR DATE CALCULATION
# =====================================================
def calculate_sr(client_name, joining_date):
    df = pd.DataFrame(client_ws.get_all_records())
    row = df[df["Client Name"]==client_name]
    if row.empty or not joining_date:
        return ""
    sr_days = int(row.iloc[0]["SR Days"])
    return (datetime.strptime(joining_date,"%d-%m-%Y")+timedelta(days=sr_days)).strftime("%d-%m-%Y")

# =====================================================
# STATUS CHANGE LOG
# =====================================================
def log_status(user, candidate, old_status, new_status):
    log_ws.append_row([
        datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        user,
        "Status Changed",
        candidate,
        f"{old_status} → {new_status}"
    ])

# =====================================================
# AUTO UI CLEANUP
# =====================================================
def cleanup(df):
    today = datetime.now()
    def valid(row):
        status = row["Status"]
        short = datetime.strptime(row["Shortlisted Date"], "%d-%m-%Y")
        if status=="Shortlisted":
            return (today-short).days <=7
        if status in ["Interviewed","Selected","Rejected","Hold"]:
            interview = datetime.strptime(row["Interview Date"], "%d-%m-%Y")
            return (today-interview).days <=30
        if status in ["Left","Not Joined"]:
            join = datetime.strptime(row["Joining Date"], "%d-%m-%Y")
            return (today-join).days <=3
        return True
    return df[df.apply(valid, axis=1)]

# =====================================================
# WHATSAPP MESSAGE
# =====================================================
def create_whatsapp(row):
    client_df = pd.DataFrame(client_ws.get_all_records())
    client_row = client_df[client_df["Client Name"]==row["Client Name"]].iloc[0]

    message = f"""
Dear {row['Candidate Name']},

Congratulations, upon reviewing your application, we would like to invite you for Direct interview.

Reference: Takecare Manpower Services Pvt Ltd

Position: {row['Job Title']}
Interview Date: {row['Interview Date']}
Interview Time: 10.30 AM

Interview Venue:
{client_row['Address']}

Map Link: {client_row['Map Link']}
Contact Person: {client_row['Contact Person']}

Regards,
{row['HR Name']}
Takecare HR Team
"""
    return f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(message)}"

# =====================================================
# LOGIN PAGE
# =====================================================
def login_page():
    col1,col2,col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>ATS LOGIN</h3>", unsafe_allow_html=True)
        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        if st.button("LOGIN"):
            df = pd.DataFrame(user_ws.get_all_records())
            user = df[(df["Mail_ID"]==email) & (df["Password"]==password)]
            if not user.empty:
                st.session_state.login=True
                st.session_state.username=user.iloc[0]["Username"]
                st.session_state.role=user.iloc[0]["Role"]
                st.session_state.report_to=user.iloc[0]["Report_To"]
                st.rerun()
            else:
                st.error("Incorrect username or password")

# =====================================================
# DASHBOARD
# =====================================================
def dashboard():
    st.markdown(f"### Welcome back, {st.session_state.username}!")
    st.markdown("Target for Today: 80+ Calls | 3-5 Interviews | 1+ Joining")
    if st.button("Logout"):
        st.session_state.login=False
        st.rerun()

    df = pd.DataFrame(ats_ws.get_all_records())

    # ROLE FILTER
    if st.session_state.role=="RECRUITER":
        df=df[df["HR Name"]==st.session_state.username]

    if st.session_state.role=="TL":
        users=pd.DataFrame(user_ws.get_all_records())
        team=users[users["Report_To"]==st.session_state.username]["Username"].tolist()
        df=df[df["HR Name"].isin(team+[st.session_state.username])]

    df=cleanup(df)

    search=st.text_input("Search")
    if search:
        df=df[df.apply(lambda r: search.lower() in str(r).lower(),axis=1)]

    # NEW SHORTLIST
    with st.expander("New Shortlist"):
        with st.form("new_form"):
            ref=generate_ref()
            name=st.text_input("Candidate Name")
            phone=st.text_input("Contact Number")
            clients=sorted(pd.DataFrame(client_ws.get_all_records())["Client Name"].unique())
            client_name=st.selectbox("Client",clients)
            pos_df=pd.DataFrame(client_ws.get_all_records())
            positions=pos_df[pos_df["Client Name"]==client_name]["Position"].tolist()
            job=st.selectbox("Position",positions)
            interview=st.date_input("Interview Date")
            submit=st.form_submit_button("Submit")
            if submit:
                ats_ws.append_row([
                    ref,
                    datetime.now().strftime("%d-%m-%Y"),
                    name,
                    phone,
                    client_name,
                    job,
                    interview.strftime("%d-%m-%Y"),
                    "Shortlisted",
                    st.session_state.username,
                    "",
                    "",
                    ""
                ])
                st.success("Saved Successfully")
                st.rerun()

    # TABLE
    for i,row in df.iterrows():
        cols=st.columns([1,1,1,1,1,1,1,1])
        cols[0].write(row["Reference_ID"])
        cols[1].write(row["Candidate Name"])
        cols[2].write(row["Contact Number"])
        cols[3].write(row["Job Title"])
        cols[4].write(row["Interview Date"])
        cols[5].write(row["Status"])
        cols[6].write(row["Joining Date"])
        if cols[7].button("Edit",key=i):
            with st.form(f"edit{i}"):
                new_status=st.selectbox("Status",
                ["Interviewed","Selected","Hold","Rejected","Onboarded","Left","Project Success"])
                feedback=st.text_area("Feedback")
                submit2=st.form_submit_button("Update")
                if submit2:
                    old_status=row["Status"]
                    index=df.index.get_loc(i)+2
                    ats_ws.update(f"H{index}",new_status)
                    ats_ws.update(f"L{index}",feedback)
                    log_status(st.session_state.username,row["Candidate Name"],old_status,new_status)
                    st.success("Updated")
                    st.rerun()

        wa=create_whatsapp(row)
        st.markdown(f"[WhatsApp Invite]({wa})")

# =====================================================
# MAIN
# =====================================================
if not st.session_state.login:
    login_page()
else:
    dashboard()
