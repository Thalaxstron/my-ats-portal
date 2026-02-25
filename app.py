import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Takecare ATS Portal", layout="wide")

# --- 2. DARK GRADIENT UI (Login & Global Style) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
        background-attachment: fixed;
    }
    .login-box {
        background: white;
        padding: 40px;
        border-radius: 10px;
        box-shadow: 0px 0px 15px rgba(0,0,0,0.5);
        width: 400px;
        margin: auto;
        text-align: center;
        color: #2c5364;
    }
    .stButton>button {
        background: #2c5364;
        color: white;
        border-radius: 5px;
        font-weight: bold;
        width: 100%;
    }
    /* White text for dashboard headers since background is dark */
    h1, h2, h3, p, .stMarkdown { color: white; }
    /* Keeping table areas readable */
    div[data-testid="stExpander"], .stTable { background-color: rgba(255,255,255,0.1); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
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

# --- 4. SESSION HANDLING ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- 5. APP FLOW ---

if not st.session_state.logged_in:
    # --- LOGIN PAGE ---
    st.write("#")
    st.write("#")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
            <div class="login-box">
                <h2 style="color: #2c5364;">Takecare Manpower Services Pvt Ltd</h2>
                <p style="color: #2c5364; font-weight: bold; font-size: 20px;">ATS LOGIN</p>
            </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            u_mail = st.text_input("Business Email")
            u_pass = st.text_input("Password", type="password")
            if st.button("LOGIN"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid Details")

else:
    # --- DASHBOARD STARTS HERE ---
    st.sidebar.markdown(f"### 👤 {st.session_state.user_full_name}")
    menu = st.sidebar.radio("Navigate", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()

    elif menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking Dashboard")
        
        raw_data = cand_sheet.get_all_records()
        if not raw_data:
            st.info("No records found.")
        else:
            df = pd.DataFrame(raw_data)
            
            # FILTERS
            f1, f2 = st.columns(2)
            with f1: search = st.text_input("🔍 Search Name/Contact")
            with f2: hr_filter = st.selectbox("Filter HR", ["All"] + sorted(df['HR Name'].unique().tolist()))

            if search:
                df = df[df['Candidate Name'].str.contains(search, case=False) | df['Contact Number'].astype(str).contains(search)]
            if hr_filter != "All":
                df = df[df['HR Name'] == hr_filter]

            # TABLE VIEW WITH ONBOARD DATE
            st.markdown("---")
            t_col = st.columns([1, 1.8, 1.2, 1.2, 1.2, 1.2, 0.5])
            headers = ["Ref ID", "Name", "Client", "Comm. Date", "Status", "Onboard Date", "Edit"]
            for col, head in zip(t_col, headers):
                col.markdown(f"**{head}**")

            for idx, row in df.iterrows():
                r_col = st.columns([1, 1.8, 1.2, 1.2, 1.2, 1.2, 0.5])
                r_col[0].write(row['Reference_ID'])
                r_col[1].write(row['Candidate Name'])
                r_col[2].write(row['Client Name'])
                r_col[3].write(row['Interview Date'])
                r_col[4].write(row['Status'])
                r_col[5].write(row['Joining Date'] if row['Joining Date'] else "-")
                
                if r_col[6].button("📝", key=f"ed_{idx}"):
                    st.session_state.edit_id = row['Reference_ID']
                    st.session_state.edit_idx = idx

            # EDIT LOGIC IN SIDEBAR
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"Update {st.session_state.edit_id}")
                    e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
                    
                    new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], 
                                         index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(e_row['Status']))
                    
                    new_feed = st.text_area("Feedback", value=e_row['Feedback'])
                    
                    # Onboard Logic
                    up_join = e_row['Joining Date']
                    up_sr = e_row['SR Date']

                    if new_st == "Onboarded":
                        j_date = st.date_input("Join Date")
                        up_join = j_date.strftime("%d-%m-%Y")
                        # SR Logic
                        c_df = pd.DataFrame(client_sheet.get_all_records())
                        c_row = c_df[c_df['Client Name'] == e_row['Client Name']]
                        days = int(c_row.iloc[0]['SR Days']) if not c_row.empty else 0
                        up_sr = (j_date + timedelta(days=days)).strftime("%d-%m-%Y")

                    if st.button("Save Changes"):
                        all_ids = cand_sheet.col_values(1)
                        row_num = all_ids.index(st.session_state.edit_id) + 1
                        cand_sheet.update_cell(row_num, 8, new_st)
                        cand_sheet.update_cell(row_num, 10, up_join)
                        cand_sheet.update_cell(row_num, 11, up_sr)
                        cand_sheet.update_cell(row_num, 12, new_feed)
                        st.success("Updated!")
                        del st.session_state.edit_id
                        st.rerun()

    elif menu == "New Entry":
        # ... (New Entry logic remains the same as previous stable version)
        st.header("📝 Candidate Entry")
        # [Existing form code here]
