import streamlit as st
import pandas as pd

# --- 1. CSS FOR PERFECT CENTERING & HEADLINES ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0d47a1 10%, #d32f2f 100%);
        background-attachment: fixed;
    }
    
    /* Centering the entire Login block */
    [data-testid="stVerticalBlock"] > div:has(div.main-login-box) {
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .main-login-box {
        text-align: center;
        width: 100%;
        max-width: 400px;
    }

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 30px;
        margin-bottom: 0px;
        text-align: center;
    }

    .ats-title {
        color: white;
        font-weight: bold;
        font-size: 22px;
        margin-bottom: 30px;
        text-align: center; /* Center-la varum */
    }

    .field-label {
        color: white !important;
        font-weight: bold;
        text-align: left !important;
        margin-bottom: 5px;
        margin-top: 15px;
        font-size: 14px;
    }

    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* Blue Typing Font */
        font-weight: bold !important;
        height: 45px !important;
    }

    .stButton>button {
        background: #0d47a1;
        color: white;
        border-radius: 8px;
        height: 50px;
        font-weight: bold;
        width: 100%;
        margin-top: 25px;
        border: 2px solid white;
    }

    .stCheckbox label { color: white !important; }
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIN LOGIC ---
if not st.session_state.get('logged_in', False):
    
    # Intha columns dhaan ATS LOGIN-ai center-la veikkum
    _, col_m, _ = st.columns([1, 2, 1])
    
    with col_m:
        st.markdown('<div class="main-login-box">', unsafe_allow_html=True)
        st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
        st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)
        
        # HEADLINE: EMAIL ID
        st.markdown('<p class="field-label">EMAIL ID</p>', unsafe_allow_html=True)
        u_mail = st.text_input("email", placeholder="Enter Email", label_visibility="collapsed")
        
        # HEADLINE: PASSWORD
        st.markdown('<p class="field-label">PASSWORD</p>', unsafe_allow_html=True)
        u_pass = st.text_input("pass", placeholder="Enter Password", type="password", label_visibility="collapsed")
        
        col_a, col_b = st.columns(2)
        with col_a:
            remember = st.checkbox("Remember Me")
        with col_b:
            st.markdown('<p style="text-align:right; color:white; font-size:12px; margin-top:5px;">Forgot Password?<br><b>Contact Admin</b></p>', unsafe_allow_html=True)

        if st.button("LOGIN SUCCESSFUL"):
            try:
                # Actual Login Check
                users_df = pd.DataFrame(user_sheet.get_all_records())
                user_match = users_df[(users_df['Mail_ID'] == u_mail) & (users_df['Password'].astype(str) == u_pass)]
                
                if not user_match.empty:
                    st.session_state.logged_in = True
                    st.session_state.user_full_name = user_match.iloc[0]['Username']
                    st.rerun() # Ippo dhaan dashboard-ku pogum
                else:
                    st.error("❌ Invalid Email or Password")
            except Exception as e:
                st.error(f"Database Error: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- 3. DASHBOARD PAGE ---
    st.sidebar.write(f"👤 {st.session_state.user_full_name}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.title("📊 Real-time Candidate Tracking")
    # Inga unga dashboard tracking table code-ai vachikalam.
    st.write("Welcome to the Dashboard!")
