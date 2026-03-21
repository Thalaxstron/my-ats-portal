import streamlit as st
import pandas as pd
from gspread import authorize
from google.oauth2.service_account import Credentials
import urllib.parse
from datetime import datetime, timedelta

# --- 1. PAGE CONFIG & UI STYLING ---
st.set_page_config(page_title="Takecare Manpower ATS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    header[data-testid="stHeader"] { background: transparent !important; height: 0px; }
    .main .block-container { padding-top: 0.5rem !important; }
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e) !important; background-attachment: fixed; }
    [data-testid="stVerticalBlock"] > div:nth-child(5) { position: sticky; top: 0; z-index: 999; background: #1a1a2e; padding: 5px 0; }
    div[data-baseweb="select"] { background-color: white !important; border-radius: 5px !important; }
    div[data-testid="stSelectbox"] * { color: #000033 !important; font-weight: bold !important; }
    div[role="listbox"] ul li { color: #000033 !important; background-color: white !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: white !important; border-radius: 5px !important; }
    input, textarea { color: #000033 !important; font-weight: bold !important; }
    label p { color: white !important; font-size: 14px !important; font-weight: bold !important; }
    .stMarkdown p, .stWrite { color: white !important; }
    .stButton > button { background-color: #FF0000 !important; color: white !important; font-weight: bold !important; border-radius: 8px !important; border: 1px solid white !important; }
    .header-box { color: #00BFFF !important; font-size: 11px !important; font-weight: bold; text-align: center; border-bottom: 2px solid #555; padding: 5px 0; line-height: 1.2; }
    .row-text { color: white !important; font-size: 13px; text-align: center; padding: 5px 0; }
    .slogan { color: #FFD700 !important; font-size: 18px; font-weight: bold; margin-top: -10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE CONNECTION ---
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
    if len(ids) <= 1: return "E00001"
    nums = [int(i[1:]) for i in ids[1:] if i.startswith("E") and i[1:].isdigit()]
    return f"E{max(nums)+1:05d}" if nums else "E00001"

if 'logged_in' not in st.session_state: st.session_state.logged_in = False

# --- 3. LOGIN PAGE ---
if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align: center; color: white;'>TAKECARE MANPOWER SERVICES PVT LTD</h1>", unsafe_allow_html=True)
    _, col_m, _ = st.columns([1, 1.2, 1])
    with col_m:
        with st.form("login"):
            u_mail, p_pass = st.text_input("Email ID"), st.text_input("Password", type="password")
            if st.form_submit_button("ATS LOGIN", use_container_width=True):
                udf = pd.DataFrame(user_sheet.get_all_records())
                match = udf[(udf['Mail_ID'] == u_mail) & (udf['Password'].astype(str) == p_pass)]
                if not match.empty:
                    st.session_state.logged_in = True; st.session_state.user_data = match.iloc[0].to_dict(); st.rerun()
                else: st.error("Invalid Credentials")

# --- 4. MAIN DASHBOARD ---
else:
    curr_user = st.session_state.user_data
    h1, h2, h3 = st.columns([2, 1.5, 0.5])
    with h1:
        st.markdown("<h2 style='color: white; margin:0;'>Takecare Manpower Service Pvt Ltd</h2>", unsafe_allow_html=True)
        st.markdown("<p class='slogan'>Successful HR Firm</p>", unsafe_allow_html=True)
    with h2:
        st.markdown(f"<p style='color: white; font-size: 18px; margin-bottom:0;'>Welcome, <b>{curr_user['Username']}</b></p>", unsafe_allow_html=True)
    with h3:
        if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

    b1, b2, b3, b_search = st.columns([0.8, 0.8, 1.2, 2.5])
    
    @st.dialog("📝 Update Status")
    def edit_candidate(row):
        st_list = ["Shortlisted", "Interviewed", "Selected", "Rejected", "Onboarded", "Hold", "Left", "Project Success"]
        curr_st = str(row.get('Status', 'Shortlisted'))
        new_st = st.selectbox("Update Status", st_list, index=st_list.index(curr_st) if curr_st in st_list else 0)
        new_fb, evt_date = st.text_input("Feedback", value=row.get('Feedback', '')), st.date_input("Date")
        if st.button("UPDATE DATA", use_container_width=True):
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
        rid = get_next_ref_id()
        cm_df = pd.DataFrame(client_sheet.get_all_records())
        c1, c2 = st.columns(2)
        with c1:
            name, phone = st.text_input("Candidate Name"), st.text_input("Phone Number")
            cl_name = st.selectbox("Client", ["--Select--"] + sorted(cm_df['Client Name'].unique().tolist()))
        with c2:
            pos = st.selectbox("Position", cm_df[cm_df['Client Name'] == cl_name]['Position'].tolist() if cl_name != "--Select--" else [])
            c_date = st.date_input("Commitment Date")
        if st.button("SAVE CANDIDATE", use_container_width=True):
            cand_sheet.append_row([rid, datetime.now().strftime('%d-%m-%Y'), name, phone, cl_name, pos, c_date.strftime('%d-%m-%Y'), "Shortlisted", curr_user['Username'], "", "", st.text_area("Initial Feedback")]); st.rerun()

    with b3:
        if st.button("➕ New Shortlist"): add_shortlist()
    with b_search:
        find = st.text_input("Search", label_visibility="collapsed", placeholder="Search...")

    # --- 5. DATA TABLE & AUTO-HIDE LOGIC ---
    st.markdown("---")
    cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1.2, 0.8, 1, 1, 0.8, 0.5, 0.5])
    for c, t in zip(cols, ["Ref ID", "Candidate", "Contact", "Client", "Job", "Int Date", "Status", "Onboard", "SR Date", "HR Name", "Edit", "WA"]):
        c.markdown(f"<div class='header-box'>{t}</div>", unsafe_allow_html=True)
    
    data = pd.DataFrame(cand_sheet.get_all_records())
    data.columns = [str(c).strip() for c in data.columns]

    if not data.empty:
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        def apply_scenarios(row):
            st, ed, idt = str(row.get('Status', '')), str(row.get('Date', '')), str(row.get('Interview Date', ''))
            e_dt = pd.to_datetime(ed, format='%d-%m-%Y', errors='coerce')
            i_dt = pd.to_datetime(idt, format='%d-%m-%Y', errors='coerce')
            if st == "Shortlisted" and pd.notnull(e_dt) and (now - e_dt).days >= 7: return False
            if st in ["Selected", "Hold", "Interviewed"]:
                ref = i_dt if pd.notnull(i_dt) else e_dt
                if pd.notnull(ref) and (now - ref).days > 30: return False
            if st in ["Left", "Rejected"]: return False
            return True
        data = data[data.apply(apply_scenarios, axis=1)]

    data = data.iloc[::-1]
    if curr_user['Role'] == "RECRUITER": data = data[data['HR Name'] == curr_user['Username']]
    if find: data = data[data.astype(str).apply(lambda x: x.str.contains(find, case=False)).any(axis=1)]

    cl_df = pd.DataFrame(client_sheet.get_all_records())
    cl_df.columns = [str(c).strip() for c in cl_df.columns]

    for _, r in data.iterrows():
        r_cols = st.columns([0.8, 1.2, 1, 1, 1.2, 1.2, 0.8, 1, 1, 0.8, 0.5, 0.5])
        fields = ['Reference_ID', 'Candidate Name', 'Contact Number', 'Client Name', 'Job Title', 'Interview Date', 'Status', 'Joining Date', 'SR Date', 'HR Name']
        for idx, f in enumerate(fields): r_cols[idx].markdown(f"<div class='row-text'>{r.get(f,'')}</div>", unsafe_allow_html=True)
        if r_cols[10].button("📝", key=f"e_{r.get('Reference_ID','NA')}"): edit_candidate(r)
        if r_cols[11].button("📲", key=f"w_{r.get('Reference_ID','NA')}"):
            c_info = cl_df[cl_df['Client Name'] == r.get('Client Name')]
            c_addr = c_info.iloc[0].get('Address', 'N/A') if not c_info.empty else "N/A"
            c_map = c_info.iloc[0].get('Map Link', 'N/A') if not c_info.empty else "N/A"
            c_person = c_info.iloc[0].get('Contact Person', 'HR Dept') if not c_info.empty else "HR Dept"
            msg = f"Dear {r.get('Candidate Name')},\n\nInterview confirmed at {r.get('Client Name')}.\nAddress: {c_addr}\nMap: {c_map}\nContact: {c_person}\n\nRegards,\n{curr_user['Username']}"
            st.markdown(f'<a href="https://api.whatsapp.com/send?phone=91{r.get("Contact Number")}&text={urllib.parse.quote(msg)}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:5px; width:100%; font-weight:bold; cursor:pointer;">OPEN WA</button></a>', unsafe_allow_html=True)
