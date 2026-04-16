import streamlit as st
import pandas as pd

# --- 1. SETTINGS & AUTHENTICATION DATA ---
st.set_page_config(page_title="VIA Project Management Hub", layout="wide")

# Passwords for the 6 users
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA Members": "member2026",
    "Classmates": "class2026"
}

# --- 2. DATA INITIALIZATION ---
if 'db' not in st.session_state:
    st.session_state.db = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "schedule": {"SKIT": "No date set", "BROCHURE": "No date set"}
    }

# --- 3. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

if not st.session_state.logged_in:
    st.title("🔐 VIA Project Login")
    role_input = st.selectbox("Select Your Role", list(USER_CREDENTIALS.keys()))
    password_input = st.text_input("Enter Password", type="password")
    
    if st.button("Login"):
        if password_input == USER_CREDENTIALS[role_input]:
            st.session_state.logged_in = True
            st.session_state.user_role = role_input
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
    st.stop()

# --- 4. APP NAVIGATION & UI ---
role = st.session_state.user_role
st.sidebar.title(f"👤 {role}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Logic for Project View
if role in ["Teacher", "VIA Committee", "Chairman"]:
    project_view = st.sidebar.radio("View Project Scope", ["SKIT", "BROCHURE"])
else:
    # Members/Reps usually belong to one, but can toggle to see the other
    project_view = st.sidebar.radio("Selected Project", ["SKIT", "BROCHURE"])

page = st.sidebar.radio("Go to", ["Dashboard & RSVP", "Team Directory", "Activity Log", "Contribution Tracker", "Chairman Panel"])

# --- PAGE: DASHBOARD & RSVP ---
if page == "Dashboard & RSVP":
    st.title(f"🚀 {project_view} Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Event Notice")
        st.info(f"**Next Discussion/Rehearsal:** {st.session_state.db['schedule'][project_view]}")
    
    with col2:
        st.subheader("RSVP")
        if not st.session_state.db["members"].empty:
            m_names = st.session_state.db["members"][st.session_state.db["members"]["Project"] == project_view]["Name"]
            user_name = st.selectbox("Select your Name", m_names if not m_names.empty else ["No members added"])
            status = st.radio("Will you attend?", ["Yes", "No", "Late"])
            if st.button("Submit"):
                st.toast(f"RSVP recorded for {user_name}")
        else:
            st.write("Awaiting member list from Chairman.")

# --- PAGE: TEAM DIRECTORY ---
elif page == "Team Directory":
    st.title("👥 VIA Project Teams")
    df = st.session_state.db["members"]
    
    if df.empty:
        st.info("No members have been assigned yet.")
    else:
        # Displaying different views
        skit_team = df[df["Project"] == "SKIT"]
        brochure_team = df[df["Project"] == "BROCHURE"]
        
        c1, c2 = st.columns(2)
        with c1:
            st.header("🎭 SKIT Team")
            st.table(skit_team)
        with c2:
            st.header("📖 BROCHURE Team")
            st.table(brochure_team)

# --- PAGE: ACTIVITY LOG (Admin/Rep Only) ---
elif page == "Activity Log":
    st.title(f"📝 Activity Log: {project_view}")
    
    can_edit_log = role in ["Chairman", "Representative", "Teacher"]
    
    if can_edit_log:
        with st.expander("➕ Add New Activity (Chairman/Rep Only)"):
            with st.form("log_form"):
                d = st.date_input("Date")
                t = st.selectbox("Type", ["Discussion", "Rehearsal"])
                desc = st.text_area("What was done?")
                if st.form_submit_button("Submit Log"):
                    st.session_state.db["logs"].append({"Project": project_view, "Date": d, "Type": t, "Desc": desc})
                    st.success("Log saved!")

    # View Logs
    logs = [l for l in st.session_state.db["logs"] if l["Project"] == project_view]
    for l in reversed(logs):
        st.write(f"**{l['Date']} ({l['Type']})**")
        st.info(l['Desc'])

# --- PAGE: CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {project_view} Contribution Hours")
    
    if role in ["Chairman", "Representative", "Teacher"]:
        with st.expander("➕ Log Contribution Hours"):
            with st.form("hours_form"):
                m_list = st.session_state.db["members"][st.session_state.db["members"]["Project"] == project_view]["Name"]
                target = st.selectbox("Member", m_list if not m_list.empty else ["None"])
                hrs = st.number_input("Hours", min_value=0)
                mins = st.number_input("Minutes", min_value=0, max_value=59)
                if st.form_submit_button("Save Time"):
                    st.session_state.db["contributions"].append({"Project": project_view, "Name": target, "Time": f"{hrs}h {mins}m"})
                    st.success("Hours recorded.")

    # Table
    c_data = [c for c in st.session_state.db["contributions"] if c["Project"] == project_view]
    if c_data:
        st.table(pd.DataFrame(c_data))
    else:
        st.write("No hours recorded yet.")

# --- PAGE: CHAIRMAN PANEL ---
elif page == "Chairman Panel":
    if role == "Chairman":
        st.title("👑 Chairman Control Panel")
        
        col_m, col_d = st.columns(2)
        with col_m:
            st.subheader("Manage Members")
            with st.form("add_mem"):
                name = st.text_input("Full Name")
                proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                pos = st.selectbox("Role", ["Member", "Representative"])
                if st.form_submit_button("Add Member"):
                    new_mem = pd.DataFrame([{"Name": name, "Project": proj, "Role": pos}])
                    st.session_state.db["members"] = pd.concat([st.session_state.db["members"], new_mem], ignore_index=True)
                    st.success(f"Added {name} to {proj}")
        
        with col_d:
            st.subheader("Set Meeting Dates")
            p_sel = st.selectbox("Project", ["SKIT", "BROCHURE"], key="sch_sel")
            d_val = st.text_input("Date/Time (e.g. April 20, 3 PM)")
            if st.button("Update Date"):
                st.session_state.db["schedule"][p_sel] = d_val
                st.success("Schedule Updated!")
                
    else:
        st.error("Access Denied. Only the Chairman can use this panel.")
