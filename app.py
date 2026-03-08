import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. UI STYLING ---
st.set_page_config(page_title="Takecare ATS", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
    header[data-testid="stHeader"] { background: transparent !important; height: 0px; }
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); background-attachment: fixed; }
    div[data-baseweb="select"], div[data-baseweb="input"] > div { background-color: white !important; border-radius: 5px !important; }
    input, textarea, div[data-testid="stSelectbox"] * { color: #000033 !important; font-weight: bold !important; }
    label p { color: white !important; font-weight: bold !important; }
    .stButton > button { background-color: #FF0000 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; }
    .header-box { color: #00BFFF !important; font-size: 11px !important; font-weight: bold; text-align: center; border-bottom: 2px solid #555; }
    .row-text { color: white !important; font-size: 13px; text-align: center; padding: 5px 0; }
</style>""", unsafe_allow_html=True)

# --- 2. DB CONNECTION ---
@st.cache_resource
def get_gsheet_client():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return authorize(creds)

client = get_gsheet_client()
sh = client.open("ATS_Cloud_Database")
user_sheet, client_sheet, cand_sheet = sh.worksheet("User_Master"), sh.worksheet("Client_Master"), sh.worksheet("ATS_Data")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN & DASHBOARD LOGIC ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE ATS LOGIN</h1>", unsafe_allow_html=True)
    with st.form("login"):
        u, p = st.text_input("Email"), st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN"):
            udf = pd.DataFrame(user_sheet.get_all_records())
            match = udf[(udf['Mail_ID'] == u) & (udf['Password'].astype(str) == p)]
            if not match.empty: st.session_state.logged_in = True; st.session_state.user_data = match.iloc[0].to_dict(); st.rerun()
else:
    curr_user = st.session_state.user_data
    st.markdown(f"<h3 style='color: white;'>Welcome, {curr_user['Username']}</h3>", unsafe_allow_html=True)
    
    @st.dialog("📝 Update Status")
    def edit_candidate(row):
        new_st = st.selectbox("Status", ["Shortlisted", "Interviewed", "Selected", "Rejected", "Onboarded", "Hold", "Left", "Project Success"], index=0)
        new_fb = st.text_input("Feedback", value=row.get('Feedback', ''))
        evt_date = st.date_input("Event Date")
        if st.button("UPDATE"):
            idx = cand_sheet.find(row['Reference_ID']).row
            cand_sheet.update_cell(idx, 8, new_st); cand_sheet.update_cell(idx, 12, new_fb)
            if new_st == "Interviewed": cand_sheet.update_cell(idx, 7, evt_date.strftime('%d-%m-%Y'))
            if new_st == "Onboarded":
                cand_sheet.update_cell(idx, 10, evt_date.strftime('%d-%m-%Y'))
                cm = pd.DataFrame(client_sheet.get_all_records())
                days = int(cm[cm['Client Name'] == row['Client Name']]['SR Days'].values[0])
                cand_sheet.update_cell(idx, 11, (evt_date + timedelta(days=days)).strftime('%d-%m-%Y'))
            st.rerun()

    @st.dialog("➕ New Shortlist")
    def add_shortlist():
        cm = pd.DataFrame(client_sheet.get_all_records())
        name, ph = st.text_input("Name"), st.text_input("Phone")
        cl = st.selectbox("Client", cm['Client Name'].unique())
        pos = st.selectbox("Position", cm[cm['Client Name'] == cl]['Position'])
        c_date = st.date_input("Commitment Date")
        if st.button("SAVE"):
            rid = f"E{len(cand_sheet.col_values(1)):05d}"
            cand_sheet.append_row([rid, datetime.now().strftime('%d-%m-%Y'), name, ph, cl, pos, c_date.strftime('%d-%m-%Y'), "Shortlisted", curr_user['Username'], "", "", ""])
            st.rerun()

    c1, c2, c3 = st.columns([1, 1, 3])
    with c1: 
        if st.button("➕ New Shortlist"): add_shortlist()
    with c2: 
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()
    find = c3.text_input("Search Candidate...")

    # --- 4. DATA DISPLAY & AUTO-HIDE LOGIC ---
    data = pd.DataFrame(cand_sheet.get_all_records())
    data.columns = [str(c).strip() for c in data.columns]
    
    if not data.empty:
        now = datetime.now()
        def filter_rows(r):
            st, ed, idt = str(r.get('Status','')), str(r.get('Date','')), str(r.get('Interview Date',''))
            e_dt = pd.to_datetime(ed, format='%d-%m-%Y', errors='coerce')
            i_dt = pd.to_datetime(idt, format='%d-%m-%Y', errors='coerce')
            if st == "Shortlisted" and pd.notnull(e_dt) and (now - e_dt).days > 7: return False
            if st in ["Selected", "Hold", "Interviewed"]:
                ref = i_dt if pd.notnull(i_dt) else e_dt
                if pd.notnull(ref) and (now - ref).days > 30: return False
            if st in ["Left", "Rejected"]: return False
            return True
        data = data[data.apply(filter_rows, axis=1)]

    if find: data = data[data.astype(str).apply(lambda x: x.str.contains(find, case=False)).any(axis=1)]
    
    st.markdown("---")
    t_cols = st.columns([1, 1.5, 1.2, 1.2, 1.2, 1, 0.5, 0.5])
    for c, t in zip(t_cols, ["Ref ID", "Candidate", "Client", "Status", "Int Date", "HR", "Edit", "WA"]):
        c.markdown(f"<div class='header-box'>{t}</div>", unsafe_allow_html=True)

    for _, r in data.iloc[::-1].iterrows():
        r_cols = st.columns([1, 1.5, 1.2, 1.2, 1.2, 1, 0.5, 0.5])
        for idx, f in enumerate(['Reference_ID', 'Candidate Name', 'Client Name', 'Status', 'Interview Date', 'HR Name']):
            r_cols[idx].markdown(f"<div class='row-text'>{r.get(f,'')}</div>", unsafe_allow_html=True)
        if r_cols[6].button("📝", key=f"e_{r['Reference_ID']}"): edit_candidate(r)
        if r_cols[7].button("📲", key=f"w_{r['Reference_ID']}"):
            msg = urllib.parse.quote(f"Hi {r['Candidate Name']}, Interview confirmed at {r['Client Name']} on {r['Interview Date']}.")
            st.markdown(f'<a href="https://api.whatsapp.com/send?phone=91{r["Contact Number"]}&text={msg}" target="_blank">WA</a>', unsafe_allow_html=True)
