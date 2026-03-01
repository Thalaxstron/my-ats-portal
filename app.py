import streamlit as st
import pandas as pd
from datetime import timedelta
# import gspread # Uncomment for actual GS integration

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Professional ATS")

# --- CUSTOM CSS (The "Secret Sauce") ---
st.markdown(f"""
    <style>
    /* 1. Gradient Background & Global Text */
    [.stApp] {{
        background: linear-gradient(135deg, #ff4b4b, #1c1c92);
        color: white;
    }}
    
    /* 2. Fixed Header (215px) */
    .fixed-header {{
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 215px;
        background: linear-gradient(90deg, #8E0E00, #1F1C18);
        z-index: 999;
        display: flex;
        justify-content: space-between;
        padding: 20px 50px;
        border-bottom: 2px solid white;
    }}
    
    /* 3. Left Side Text (4 Lines) */
    .header-left {{
        display: flex;
        flex-direction: column;
        line-height: 1.2;
    }}
    .co-name {{ font-size: 32px; font-weight: bold; }}
    .slogan {{ font-size: 18px; opacity: 0.8; }}
    .welcome {{ font-size: 20px; margin-top: 10px; }}
    .target {{ font-size: 16px; color: #00ffcc; }}

    /* 4. Table Logic */
    .table-container {{
        margin-top: 260px; /* Offset for header + table header */
    }}
    .sticky-table-header {{
        position: fixed;
        top: 215px;
        width: 100%;
        height: 45px;
        background-color: #002b5b;
        color: white;
        z-index: 998;
        display: grid;
        grid-template-columns: repeat(11, 1fr);
        align-items: center;
        text-align: center;
        font-weight: bold;
    }}
    
    /* Input Boxes Styling */
    input {{
        color: #002b5b !important;
    }}
    </style>
""", unsafe_allow_html=True)

# --- BACKEND LOGIC: SR DATE CALCULATION ---
def calculate_sr_date(joining_date, client_name, client_master_df):
    """
    Logic: Looks up SR Days from Client_Master and adds it to Joining Date.
    """
    sr_days = client_master_df.loc[client_master_df['Client'] == client_name, 'SR_Days'].values[0]
    return joining_date + timedelta(days=int(sr_days))

# --- UI LAYOUT ---

# 1. FIXED HEADER
st.markdown(f"""
    <div class="fixed-header">
        <div class="header-left">
            <div class="co-name">TALENT PRO ATS</div>
            <div class="slogan">Bridging Talent with Opportunity</div>
            <div class="welcome">Welcome back, Admin</div>
            <div class="target">Monthly Target: 15/20 Hires</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Right Side Buttons (Streamlit columns inside a container to align with fixed header)
header_right = st.container()
with header_right:
    # Using columns to position buttons on the top right
    c1, c2, c3, c4, c5 = st.columns([6, 1, 1, 1, 1.5])
    with c2: st.button("Logout")
    with c3: st.button("🔍 Search")
    with c4: st.button("Filter")
    with c5: st.button("+ New Shortlist")

# 2. FIXED TABLE HEADER
st.markdown("""
    <div class="sticky-table-header">
        <div>Ref ID</div><div>Name</div><div>Contact</div><div>Job Title</div>
        <div>Int. Date</div><div>Status</div><div>Joining</div><div>SR Date</div>
        <div>HR</div><div>Feedback</div><div>Action</div>
    </div>
""", unsafe_allow_html=True)

# 3. SCROLLABLE DATA AREA
st.markdown('<div class="table-container">', unsafe_allow_html=True)

# Mock Data for Display
data = {
    "Ref ID": ["REF001"], "Name": ["Arun Kumar"], "Contact": ["9876543210"],
    "Job Title": ["Python Dev"], "Interview Date": ["2026-03-10"], "Status": ["Onboarded"],
    "Joining Date": ["2026-04-01"], "SR Date": ["2026-05-01"], "HR": ["Priya"],
    "Feedback": ["Excellent"], "Action": ["📞 WhatsApp"]
}
df = pd.DataFrame(data)

# Displaying data in rows
for i in range(20): # Mocking 20 rows
    cols = st.columns(11)
    cols[0].write("REF001")
    cols[1].write("Arun Kumar")
    cols[2].write("9876543210")
    cols[3].write("Developer")
    cols[4].write("2026-03-10")
    cols[5].write("Onboarded")
    cols[6].write("2026-04-01")
    cols[7].write("2026-05-01")
    cols[8].write("Priya")
    cols[9].write("Strong")
    if cols[10].button("Edit", key=f"edit_{i}"):
        st.toast("Opening Dialog...")

st.markdown('</div>', unsafe_allow_html=True)
