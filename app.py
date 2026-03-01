# --- 6. DASHBOARD HEADER (NEW ALIGNMENT STRUCTURE) ---

u_data = st.session_state.user_data

# --------- TOP FIXED 25% HEADER AREA ----------
header_container = st.container()

with header_container:
    left_col, right_col = st.columns([3, 1])

    # -------- LEFT SIDE (Company + Welcome + Target) --------
    with left_col:
        st.markdown("## TAKECARE MANPOWER SERVICES PVT LTD")
        st.markdown("### Successful HR Firm")
        st.markdown(f"### Welcome back, {u_data['Username']}!")
        st.markdown(
            "#### Target for Today: 📞 80+ Telescreening Calls / 3-5 Interview / 1+ Joining"
        )

    # -------- RIGHT SIDE (Search + Logout + Filter + New Shortlist) --------
    with right_col:

        search_query = st.text_input("🔍 Search")

        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

        # FILTER BUTTON → Only TL & ADMIN
        if u_data['Role'] in ["TL", "ADMIN"]:
            st.button("Filter")

        if st.button("+ New Shortlist"):
            new_entry_popup()

st.markdown("---")
