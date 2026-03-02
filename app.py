import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import urllib.parse

st.set_page_config(page_title="Takecare ATS", layout="wide")

# ===============================
# DATABASE CONNECTION
# ===============================
def get_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope
    )
    return authorize(creds)

client = get_client()
sh = client.open("ATS_Cloud_Database")
user_sheet = sh.worksheet("User_Master")
ats_sheet = sh.worksheet("ATS_Data")
client_sheet = sh.worksheet("Client_Master")

# ===============================
# SESSION
# ===============================
if "logged" not in st.session_state:
    st.session_state.logged = False

# ===============================
# LOGIN PAGE
# ===============================
def login_page():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
    }
    .loginbox {
        background:white;
        padding:40px;
        border-radius:15px;
    }
    </style>
    """, unsafe_allow_html=True)

    col1,col2,col3 = st.columns([1,1,1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>ATS LOGIN</h3>", unsafe_allow_html=True)

        email = st.text_input("Email ID")
        password = st.text_input("Password", type="password")
        remember = st.checkbox("Remember Me")

        if st.button("LOGIN"):
            users = pd.DataFrame(user_sheet.get_all_records())
            user = users[(users["Mail_ID"]==email) & (users["Password"]==password)]
            if not user.empty:
                st.session_state.logged = True
                st.session_state.username = user.iloc[0]["Username"]
                st.session_state.role = user.iloc[0]["Role"]
                st.session_state.report_to = user.iloc[0]["Report_To"]
                st.rerun()
            else:
                st.error("Incorrect username or password")

# ===============================
# REF ID
# ===============================
def next_ref():
    data = ats_sheet.col_values(1)
    ids = [int(x[1:]) for x in data[1:] if x.startswith("E")]
    if not ids:
        return "E00001"
    return f"E{max(ids)+1:05d}"

# ===============================
# SR DATE
# ===============================
def calculate_sr(onboard_date, client_name):
    client_df = pd.DataFrame(client_sheet.get_all_records())
    row = client_df[client_df["Client Name"]==client_name]
    if row.empty:
        return ""
    sr_days = int(row.iloc[0]["SR Days"])
    return (datetime.strptime(onboard_date,"%d-%m-%Y")+timedelta(days=sr_days)).strftime("%d-%m-%Y")

# ===============================
# WHATSAPP LINK
# ===============================
def whatsapp_link(row):
    client_df = pd.DataFrame(client_sheet.get_all_records())
    client_row = client_df[client_df["Client Name"]==row["Client Name"]].iloc[0]

    message = f"""
Dear {row['Candidate Name']},

Congratulations, upon reviewing your application, we would like to invite you for Direct interview and get to know you better.

Please write your resume:
Reference: Takecare Manpower Services Pvt Ltd

Position: {row['Job Title']}
Interview Date: {row['Interview Date']}
Interview Time: 10.30 Am

Interview venue: {client_row['Address']}
Map Link: {client_row['Map Link']}
Contact Person: {client_row['Contact Person']}

Regards,
{row['HR Name']}
Takecare HR Team
"""
    return f"https://wa.me/91{row['Contact Number']}?text={urllib.parse.quote(message)}"

# ===============================
# AUTO DELETE UI ONLY
# ===============================
def clean_data(df):
    today = datetime.now()

    def valid(row):
        status = row["Status"]
        short_date = datetime.strptime(row["Shortlisted Date"], "%d-%m-%Y")

        if status=="Shortlisted":
            return (today-short_date).days <= 7

        if status in ["Interviewed","Selected","Rejected","Hold"]:
            interview_date = datetime.strptime(row["Interview Date"], "%d-%m-%Y")
            return (today-interview_date).days <= 30

        if status in ["Left","Not Joined"]:
            onboard = datetime.strptime(row["Joining Date"], "%d-%m-%Y")
            return (today-onboard).days <= 3

        return True

    return df[df.apply(valid,axis=1)]

# ===============================
# DASHBOARD
# ===============================
def dashboard():

    st.markdown(f"""
    <h2 style='float:left;'>Takecare Manpower Service Pvt Ltd</h2>
    <h4 style='float:right;'>Welcome back, {st.session_state.username}!</h4>
    """, unsafe_allow_html=True)

    st.write("Successful HR Firm")
    st.write("Target for Today: 80+ Telescreening | 3-5 Interview | 1+ Joining")

    if st.button("Logout"):
        st.session_state.logged=False
        st.rerun()

    data = pd.DataFrame(ats_sheet.get_all_records())

    # ROLE FILTER
    if st.session_state.role=="RECRUITER":
        data = data[data["HR Name"]==st.session_state.username]

    if st.session_state.role=="TL":
        team = pd.DataFrame(user_sheet.get_all_records())
        recruiters = team[team["Report_To"]==st.session_state.username]["Username"].tolist()
        data = data[data["HR Name"].isin(recruiters+[st.session_state.username])]

    data = clean_data(data)

    # SEARCH
    search = st.text_input("Search")
    if search:
        data = data[data.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

    # NEW SHORTLIST
    if st.button("New Shortlist"):
        with st.form("new"):
            ref = next_ref()
            name = st.text_input("Candidate Name")
            phone = st.text_input("Contact Number")
            clients = sorted(pd.DataFrame(client_sheet.get_all_records())["Client Name"].unique())
            client_name = st.selectbox("Client", clients)

            positions = pd.DataFrame(client_sheet.get_all_records())
            pos_list = positions[positions["Client Name"]==client_name]["Position"].tolist()
            job = st.selectbox("Position", pos_list)

            cdate = st.date_input("Interview Date")
            feedback = st.text_area("Feedback")

            submit = st.form_submit_button("Submit")
            cancel = st.form_submit_button("Cancel")

            if submit:
                ats_sheet.append_row([
                    ref,
                    datetime.now().strftime("%d-%m-%Y"),
                    name,
                    phone,
                    client_name,
                    job,
                    cdate.strftime("%d-%m-%Y"),
                    "Shortlisted",
                    st.session_state.username,
                    "",
                    "",
                    feedback
                ])
                st.rerun()

    st.dataframe(data, use_container_width=True)

# ===============================
# MAIN
# ===============================
if not st.session_state.logged:
    login_page()
else:
    dashboard()
