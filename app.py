import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    header[data-testid="stHeader"] { background: transparent !important; height: 0px; }
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { background-color: white !important; }
    input, textarea, div[role="listbox"] { color: #000033 !important; font-weight: bold !important; }
    label p { color: white !important; font-weight: bold !important; }
    .header-box { color: #00BFFF !important; font-size: 11px; font-weight: bold; text-align: center; border-bottom: 2px solid #555; }
    .row-text { color: white !important; font-size: 13px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
@st.cache_resource
def get_gsheet_client():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        return authorize(creds)
    except Exception as e:
        st.error(f"Database Error: {e}"); return None

client = get_gsheet_client()
if client:
    sh = client.open("ATS_Cloud_Database")
    user_sheet, client_sheet, cand_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

def get_next_ref_id():
    ids = cand_sheet.col_values(1)
    nums = [int(i[1:]) for i in ids[1:] if i.startswith("E") and i[1:].isdigit()]
    return f"E{max(nums)+1:05d}" if nums else "E00001"

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN & DASHBOARD ---
if not st.session_state.logged_in:
    with st.form("login"):
        u_mail, p_pass = st.text_input("Email ID"), st.text_input("Password", type="password")
        if st.form_submit_button("ATS LOGIN"):
            udf = pd.DataFrame(user_sheet.get_all_records())
            match = udf[(udf['Mail_ID'] == u_mail) & (udf['Password'].astype(str) == p_pass)]
            if not match.empty:
                st.session_state.logged_in, st.session_state.user_data = True, match.iloc[0].to_dict()
                st.rerun()
else:
    curr_user = st.session_state.user_data
    st.markdown(f"<h2 style='color: white;'>Takecare Manpower - Welcome {curr_user['Username']}</h2>", unsafe_allow_html=True)

    @st.dialog("📝 Update Status")
    def edit_candidate(row):
        new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Rejected", "Onboarded", "Left"])
        new_fb = st.text_input("Feedback", value=row.get('Feedback', ''))
        evt_dt = st.date_input("Date")
        if st.button("UPDATE"):
            idx = cand_sheet.find(row['Reference_ID']).row
            cand_sheet.update_cell(idx, 8, new_st)
            cand_sheet.update_cell(idx, 12, new_fb)
            st.rerun()

    b1, b2, b_search = st.columns([1, 1, 3])
    with b1: 
        if st.button("➕ New Shortlist"): st.info("Popup logic active") # Simplified for brevity
    with b_search: find = st.text_input("Search Candidate", placeholder="Name or ID...")

    # --- DATA TABLE ---
    st.markdown("---")
    cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1, 0.8, 1, 0.5, 0.5])
    titles = ["Ref ID", "Candidate", "Contact", "Client", "Position", "Int Date", "Status", "HR", "Edit", "WA"]
    for c, t in zip(cols, titles): c.markdown(f"<div class='header-box'>{t}</div>", unsafe_allow_html=True)
    
    data = pd.DataFrame(cand_sheet.get_all_records())
    data.columns = [c.strip() for c in data.columns]
    data = data.iloc[::-1]
    if find: data = data[data.astype(str).apply(lambda x: x.str.contains(find, case=False)).any(axis=1)]

    # Fetch Client Data Safely
    clients_df = pd.DataFrame(client_sheet.get_all_records())
    clients_df.columns = [c.strip() for c in clients_df.columns] # Remove hidden spaces

    for _, r in data.iterrows():
        r_cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1, 0.8, 1, 0.5, 0.5])
        r_cols[0].markdown(f"<p class='row-text'>{r.get('Reference_ID','')}</p>", unsafe_allow_html=True)
        r_cols[1].markdown(f"<p class='row-text'>{r.get('Candidate Name','')}</p>", unsafe_allow_html=True)
        r_cols[2].markdown(f"<p class='row-text'>{r.get('Contact Number','')}</p>", unsafe_allow_html=True)
        r_cols[3].markdown(f"<p class='row-text'>{r.get('Client Name','')}</p>", unsafe_allow_html=True)
        r_cols[4].markdown(f"<p class='row-text'>{r.get('Job Title','')}</p>", unsafe_allow_html=True)
        r_cols[5].markdown(f"<p class='row-text'>{r.get('Interview Date','')}</p>", unsafe_allow_html=True)
        r_cols[6].markdown(f"<p class='row-text'>{r.get('Status','')}</p>", unsafe_allow_html=True)
        r_cols[7].markdown(f"<p class='row-text'>{r.get('HR Name','')}</p>", unsafe_allow_html=True)
        
        if r_cols[8].button("📝", key=f"e_{r.get('Reference_ID')}"): edit_candidate(r)
        
        if r_cols[9].button("📲", key=f"w_{r.get('Reference_ID')}"):
            c_info = clients_df[clients_df['Client Name'] == r['Client Name']]
            # SAFE DATA EXTRACTION - Check if column exists before accessing
            c_addr = c_info.iloc[0].get('Address', 'Address Not Found') if not c_info.empty else "N/A"
            c_map = c_info.iloc[0].get('Map Link', '') if not c_info.empty else ""
            c_person = c_info.iloc[0].get('Contact Person', 'HR Department') if not c_info.empty else "N/A"

            msg = f"Dear {r.get('Candidate Name','')},\nDirect Interview Invite!\nClient: {r.get('Client Name','')}\nAddr: {c_addr}\nMap: {c_map}\nContact: {c_person}\nRegards, {curr_user['Username']}"
            wa_url = f"https://api.whatsapp.com/send?phone=91{r.get('Contact Number','')}&text={urllib.parse.quote(msg)}"
            st.markdown(f'<a href="{wa_url}" target="_blank"><button style="background:#25D366;color:white;border:none;padding:8px;border-radius:5px;width:100%;">SEND</button></a>', unsafe_allow_html=True)
