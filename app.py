import streamlit as st

# --- HEADER UI LOGIC (Step 3) ---
def render_fixed_header(username):
    # Fixed Header Container (Point 24, 81)
    st.markdown(f"""
        <style>
        .header-container {{
            position: fixed; top: 0; left: 0; width: 100%; height: 215px;
            background: linear-gradient(135deg, #d32f2f 0%, #0d47a1 100%);
            z-index: 1000; padding: 20px 45px; border-bottom: 2px solid white;
            display: flex; justify-content: space-between; align-items: flex-start;
        }}
        .header-left {{ color: white; flex: 2; }}
        .header-right {{ flex: 1; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }}
        
        /* Fixed Column Headers (Point 27) */
        .table-header-freeze {{
            position: fixed; top: 215px; left: 0; width: 100%; height: 45px;
            background-color: #0d47a1; z-index: 999; display: flex;
            border-bottom: 1px solid #ccc;
        }}
        .h-cell {{
            color: white; font-weight: bold; text-align: center; font-size: 13px;
            border-right: 1px solid white; display: flex; align-items: center; justify-content: center;
        }}
        </style>
        
        <div class="header-container">
            <div class="header-left">
                <h2 style="margin:0;">Takecare Manpower Services Pvt Ltd</h2> <p style="margin:0; font-size:16px;">Successful HR Firm</p> <p style="margin:12px 0 0 0; font-size:18px;">Welcome back, {username}!</p> <div style="background:white; color:#0d47a1; padding:6px 12px; border-radius:4px; font-weight:bold; margin-top:8px; display:inline-block;">
                    📞 Target for Today: 80+ Calls / 3-5 Interview / 1+ Joining </div>
            </div>
            <div id="right-placeholder" style="width: 250px;"></div> </div>
    """, unsafe_allow_html=True)

    # Right Side Buttons Alignment (Point 20-23, 81)
    # Using Streamlit columns inside a placeholder container to keep them interactive
    _, right_col = st.columns([3, 1])
    with right_col:
        st.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True) # Gap from top
        st.button("Logout 🚪", use_container_width=True, key="logout_btn") # Line 1
        st.text_input("Search", placeholder="🔍 Search...", label_visibility="collapsed", key="search_bar") # Line 2
        
        btn_row = st.columns(2)
        btn_row[0].button("Filter ⚙️", use_container_width=True, key="filter_btn") # Line 3
        btn_row[1].button("+ New", type="primary", use_container_width=True, key="add_btn") # Line 4

    # Table Column Headers Freeze (Point 27, 81)
    labels = ["Ref ID", "Candidate", "Contact", "Position", "Commit/Int Date", "Status", "Onboarded", "SR Date", "HR Name", "Action", "WA Invite"]
    widths = [8, 12, 10, 15, 12, 10, 10, 8, 10, 5, 5]
    
    header_html = "".join([f'<div style="width:{w}%;" class="h-cell">{l}</div>' for l, w in zip(labels, widths)])
    st.markdown(f'<div class="table-header-freeze">{header_html}</div>', unsafe_allow_html=True)

# Main Execution Logic
if st.session_state.get('auth'):
    render_fixed_header(st.session_state.user['Username'])
    st.markdown('<div style="margin-top:270px; background:white; min-height:100vh;"></div>', unsafe_allow_html=True)
