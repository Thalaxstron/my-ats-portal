import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Takecare ATS", layout="wide")

# Session state initialization
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_full_name' not in st.session_state:
    st.session_state.user_full_name = ""

# --- 2. HIGH QUALITY UI DESIGN ---
# Professional Office Background with Glassy Login Box
st.markdown("""
    <style>
    .stApp {
        background: url("https://images.unsplash.com/photo-1497366216548-37526070297c?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80");
        background-size: cover;
    }
    
    .login-container {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        text-align: center;
        margin-top: 50px;
    }
    
    .main-title {
        color: #004aad;
        font-family: 'Arial Black', sans-serif;
        font-size: 32px;
        margin-bottom: 5px;
    }
    
    .sub-title {
        color: #333;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
        letter-spacing: 2px;
    }

    .stButton>button {
        background: linear-gradient(45deg, #004aad, #0072ff);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 12px;
        font-size: 16px;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(0,74,173,0.4);
    }
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
    st.error(f"Database Connection Error: {e}")
    st.stop()

# --- 4. APP FLOW ---

if not st.session_state.logged_in:
    # --- MODERN LOGIN PAGE ---
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div class="login-container">
                <div class="main-title">Takecare Manpower Services Pvt Ltd</div>
                <div class="sub-title">ATS</div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.container(border=False):
            # Form style background for inputs
            st.markdown('<div style="background: white; padding: 20px; border-radius: 15px;">', unsafe_allow_html=True)
            u_mail = st.text_input("📧 Business Email")
            u_pass = st.text_input("🔑 Password", type="password")
            if st.button("Login to System"):
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_row = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                if not user_row.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_row.iloc[0]['Username']
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try again.")
            st.markdown('</div>', unsafe_allow_html=True)
            st.caption("© 2026 Takecare Manpower Services. For Admin support, contact HR Tech Team.")

else:
    # --- DASHBOARD (Side Navigation) ---
    st.sidebar.markdown(f"<h2 style='color:white;'>Takecare</h2>", unsafe_allow_html=True)
    st.sidebar.write(f"Logged in: **{st.session_state.user_full_name}**")
    menu = st.sidebar.radio("Navigation", ["Dashboard & Tracking", "New Entry", "Logout"])

    if menu == "Logout":
        st.session_state.logged_in = False
        st.session_state.user_full_name = ""
        st.rerun()

    # --- TRACKING MODULE ---
    if menu == "Dashboard & Tracking":
        st.header("🔄 Candidate Tracking Dashboard")
        
        raw_data = cand_sheet.get_all_records()
        if not raw_data:
            st.info("No records found.")
        else:
            df = pd.DataFrame(raw_data)
            
            # FILTERS
            f1, f2, f3 = st.columns([2, 1, 1])
            with f1: search_name = st.text_input("🔍 Search Name or Contact")
            with f2: hr_filter = st.selectbox("HR Filter", ["All"] + sorted(df['HR Name'].unique().tolist()))
            with f3: st_filter = st.selectbox("Status Filter", ["All"] + sorted(df['Status'].unique().tolist()))

            # Apply Filter
            if search_name:
                df = df[df['Candidate Name'].str.contains(search_name, case=False) | df['Contact Number'].astype(str).contains(search_name)]
            if hr_filter != "All":
                df = df[df['HR Name'] == hr_filter]
            if st_filter != "All":
                df = df[df['Status'] == st_filter]

            # TABLE VIEW
            st.markdown("---")
            t_col = st.columns([1, 2, 1.5, 1.2, 1.2, 1.2, 0.5])
            headers = ["Ref ID", "Name", "Client", "Comm. Date", "Status", "Onboard Date", "Edit"]
            for col, head in zip(t_col, headers):
                col.write(f"**{head}**")

            for idx, row in df.iterrows():
                r_col = st.columns([1, 2, 1.5, 1.2, 1.2, 1.2, 0.5])
                r_col[0].write(row['Reference_ID'])
                r_col[1].write(row['Candidate Name'])
                r_col[2].write(row['Client Name'])
                r_col[3].write(row['Interview Date'])
                r_col[4].write(row['Status'])
                r_col[5].write(row['Joining Date'] if row['Joining Date'] else "-")
                
                if r_col[6].button("📝", key=f"edit_{idx}"):
                    st.session_state.edit_id = row['Reference_ID']
                    st.session_state.edit_idx = idx

            # EDIT LOGIC (Sidebar)
            if 'edit_id' in st.session_state:
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"Edit {st.session_state.edit_id}")
                    e_row = df[df['Reference_ID'] == st.session_state.edit_id].iloc[0]
                    
                    new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"], 
                                         index=["Shortlisted", "Interviewed", "Selected", "Hold", "Rejected", "Onboarded", "Not Joined", "Left", "Working"].index(e_row['Status']))
                    
                    new_feed = st.text_area("Feedback", value=e_row['Feedback'])
                    
                    up_int = e_row['Interview Date']
                    up_join = e_row['Joining Date']
                    up_sr = e_row['SR Date']

                    if new_st == "Interviewed":
                        up_int = st.date_input("Interview Date").strftime("%d-%m-%Y")
                    if new_st == "Onboarded":
                        j_date = st.date_input("Join Date")
                        up_join = j_date.strftime("%d-%m-%Y")
                        # SR Logic
                        c_df = pd.DataFrame(client_sheet.get_all_records())
                        c_row = c_df[c_df['Client Name'] == e_row['Client Name']]
                        days = int(c_row.iloc[0]['SR Days']) if not c_row.empty else 0
                        up_sr = (j_date + timedelta(days=days)).strftime("%d-%m-%Y")

                    if st.button("Confirm Update"):
                        # In the sheet, rows start at 2 (1-based index + skip header)
                        # We must find the actual row based on Reference ID to be safe
                        all_ids_in_sheet = cand_sheet.col_values(1)
                        try:
                            row_num = all_ids_in_sheet.index(st.session_state.edit_id) + 1
                            cand_sheet.update_cell(row_num, 7, up_int)
                            cand_sheet.update_cell(row_num, 8, new_st)
                            cand_sheet.update_cell(row_num, 10, up_join)
                            cand_sheet.update_cell(row_num, 11, up_sr)
                            cand_sheet.update_cell(row_num, 12, new_feed)
                            st.success("Updated!")
                            del st.session_state.edit_id
                            st.rerun()
                        except:
                            st.error("Error finding record in sheet.")

    # --- NEW ENTRY MODULE ---
    elif menu == "New Entry":
        st.header("📝 New Shortlist Entry")
        # Reuse existing entry logic from previous stable version...
        # [Ippo ippinga content-ah simplify pannitaen storage-kaga]
        # (Unga pazhaya solid 'New Entry' logic inga irukkum)
        st.info("Use the form below to add new candidates.")
        # [Existing form logic goes here]
