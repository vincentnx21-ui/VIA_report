import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub", layout="wide")

# --- CREDENTIALS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- INITIALIZE DATABASE ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "events": []
    }

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- LOGIN / LOGOUT LOGIC ---
def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

if not st.session_state.authenticated:
    st.title("🔐 VIA Project Portal Login")
    role_input = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if pass_input == USER_CREDENTIALS[role_input]:
            st.session_state.authenticated = True
            st.session_state.user_role = role_input
            st.rerun()
        else:
            st.error("Incorrect Password")
else:
    # --- LOGGED IN UI ---
    user_role = st.session_state.user_role
    
    # Sidebar Setup
    st.sidebar.title(f"👤 {user_role}")
    if st.sidebar.button("Log Out"):
        logout()
    
    st.sidebar.write("---")
    view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
    page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Panel"])

    # Permission Flags
    # Teacher can view everything but cannot add reports/logs and cannot see Management
    can_edit = user_role in ["Chairman", "Representative"]
    is_chairman = user_role == "Chairman"
    
    # Pre-load data for NameError prevention
    m_df = st.session_state.data["members"]

    # --- 1. DASHBOARD ---
    if page == "Dashboard":
        st.title(f"🚀 {view_project} Project")
        
        # Display Reps
        reps = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Representative")]
        rep_names = ", ".join(reps['Name'].tolist()) if not reps.empty else "TBD"
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📌 Status & Schedule")
            st.write(f"**Representatives:** {rep_names}")
            
            p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
            if p_events:
                for e in p_events:
                    st.warning(f"**{e['type']}** scheduled for: \n\n {e['date_str']}")
            else:
                st.info("No upcoming sessions.")

        with col2:
            st.subheader("👥 Project Roster")
            p_members = m_df[m_df['Project'] == view_project]['Name'].tolist()
            if p_members:
                st.write(", ".join(p_members))
                st.write("---")
                # RSVP is viewable by all members
                u_name = st.selectbox("Select Your Name to RSVP", p_members)
                if st.button("I am Attending"):
                    st.toast(f"RSVP recorded for {u_name}")
            else:
                st.write("No members assigned by Chairman yet.")

    # --- 2. ACTIVITY LOG ---
    elif page == "Activity Log":
        st.title(f"📝 {view_project} Progress Logs")
        
        if can_edit:
            with st.form("log_form", clear_on_submit=True):
                l_date = st.date_input("Date")
                l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
                l_desc = st.text_area("What was done?")
                if st.form_submit_button("Submit Log"):
                    st.session_state.data["logs"].append({
                        "Project": view_project, "Date": str(l_date), "Type": l_type, "Desc": l_desc
                    })
                    st.success("Log added!")
                    st.rerun()
        
        st.write("---")
        p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
        if not p_logs:
            st.info("No logs available yet.")
        else:
            for l in reversed(p_logs):
                with st.expander(f"{l['Date']} - {l['Type']}"):
                    st.write(l['Desc'])

    # --- 3. CONTRIBUTION TRACKER ---
    elif page == "Contribution Tracker":
        st.title(f"⏳ {view_project} Time Report")
        
        if can_edit:
            with st.form("contrib_form", clear_on_submit=True):
                p_m_list = m_df[m_df['Project'] == view_project]['Name'].tolist()
                if p_m_list:
                    target = st.selectbox("Member", p_m_list)
                    h = st.number_input("Hours", min_value=0, step=1)
                    m = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                    if st.form_submit_button("Record Hours"):
                        st.session_state.data["contributions"].append({
                            "Project": view_project, "Name": target, "Time": f"{h}h {m}m"
                        })
                        st.success("Contribution recorded.")
                        st.rerun()
                else:
                    st.warning("Chairman must add members first.")
                    st.form_submit_button("Add Member First", disabled=True)

        st.write("---")
        c_list = [c for c in st.session_state.data["contributions"] if c['Project'] == view_project]
        if c_list:
            st.table(pd.DataFrame(c_list))
        else:
            st.info("No hours logged yet.")

    # --- 4. MANAGEMENT PANEL ---
    elif page == "Management Panel":
        # EXPLICIT BLOCK: Teacher cannot see this
        if is_chairman:
            st.title("👑 Chairman Management Centre")
            
            tab1, tab2 = st.tabs(["Add Members", "Schedule Event"])
            
            with tab1:
                with st.form("add_member"):
                    n = st.text_input("Member Name")
                    p = st.selectbox("Assign Project", ["SKIT", "BROCHURE"])
                    r = st.selectbox("Role", ["Member", "Representative"])
                    if st.form_submit_button("Add to Project"):
                        if n:
                            nr = pd.DataFrame([{"Name": n, "Project": p, "Role": r}])
                            st.session_state.data["members"] = pd.concat([st.session_state.data["members"], nr], ignore_index=True)
                            st.rerun()
                
                st.subheader("Full Class Roster")
                st.dataframe(st.session_state.data["members"], use_container_width=True)

            with tab2:
                with st.form("sched_form"):
                    e_p = st.selectbox("Project", ["SKIT", "BROCHURE"])
                    e_t = st.radio("Event Type", ["Discussion", "Rehearsal"])
                    e_d = st.date_input("Date")
                    e_c = st.time_input("Time")
                    if st.form_submit_button("Set Meeting"):
                        st.session_state.data["events"].append({
                            "project": e_p, "type": e_t, "date_str": f"{e_d} at {e_c}"
                        })
                        st.success("Event scheduled!")
        
        elif user_role == "Teacher":
            st.error("Access Denied: Teachers can view reports but cannot access the Management Centre.")
        else:
            st.error("Access Denied: Only the Chairman can access this page.")
