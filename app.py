import streamlit as st

# --- CSS (Everything Centered + Headings + Blue Font) ---
st.markdown("""
    <style>
    /* Background */
    .stApp {
        background: linear-gradient(135deg, #0d47a1 10%, #d32f2f 100%);
        background-attachment: fixed;
    }
    
    /* Centering the main content */
    .main-login-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding-top: 60px;
    }

    .company-header {
        color: white;
        font-family: 'Arial Black', sans-serif;
        font-size: 34px;
        margin-bottom: 5px;
    }

    .ats-title {
        color: white;
        font-weight: bold;
        font-size: 24px;
        margin-bottom: 30px;
        letter-spacing: 2px;
    }

    /* Headings for Email & Password */
    .field-label {
        color: white !important;
        font-weight: bold !important;
        text-align: left !important;
        display: block;
        margin-bottom: 5px;
        font-size: 14px;
    }

    /* Input Box Styling */
    .stTextInput input {
        border-radius: 8px !important;
        background-color: white !important;
        color: #0d47a1 !important; /* BLUE TYPING FONT */
        font-weight: bold !important;
        height: 48px !important;
        border: none !important;
    }

    /* Login Button */
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

    /* Remember me & Footer */
    .stCheckbox label {
        color: white !important;
    }
    
    header, footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN UI ---
st.markdown('<div class="main-login-box">', unsafe_allow_html=True)
st.markdown('<div class="company-header">TAKECARE MANPOWER SERVICES</div>', unsafe_allow_html=True)
st.markdown('<div class="ats-title">ATS LOGIN</div>', unsafe_allow_html=True)

# Centering column
_, col_m, _ = st.columns([1, 1.3, 1])

with col_m:
    # 1. EMAIL SECTION
    st.markdown('<p class="field-label">EMAIL ID</p>', unsafe_allow_html=True)
    u_mail = st.text_input("email", placeholder="Enter your email", label_visibility="collapsed")
    
    st.write("") # Spacer
    
    # 2. PASSWORD SECTION
    st.markdown('<p class="field-label">PASSWORD</p>', unsafe_allow_html=True)
    u_pass = st.text_input("pass", placeholder="Enter your password", type="password", label_visibility="collapsed")
    
    # 3. REMEMBER ME & FORGET PASSWORD
    col_a, col_b = st.columns([1, 1])
    with col_a:
        remember = st.checkbox("Remember Me")
    with col_b:
        st.markdown('<p style="text-align:right; color:white; font-size:12px; margin-top:5px;">Forgot Password?<br><b>Contact Admin</b></p>', unsafe_allow_html=True)

    # 4. LOGIN BUTTON
    if st.button("LOGIN SUCCESSFUL"):
        st.success("Verifying...")

st.markdown('</div>', unsafe_allow_html=True)
