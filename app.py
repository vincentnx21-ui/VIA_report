import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# --- USER PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- INITIALIZE DATA (Prevents NameError) ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "events": []
    }

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.rerun()

# --- LOGIN UI ---
if not st.session_state.authenticated:
    st.title("🔐 VIA Project Portal Login")
    col1, col2 = st.columns([1, 2])
    with col1:
        role_input = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
        pw_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw_input == USER_CREDENTIALS[role_input]:
                st.session_state.authenticated = True
                st.session_state.user_role = role_input
                st.rerun()
            else:
                st.error("Invalid password")
    st.stop() # Stop execution here if not logged in

# --- LOGGED IN AREA ---
user_role = st.session_state.user_role

# Sidebar
st.sidebar.title(f"👤 {user_role}")
if st.sidebar.button("🚪 Log Out"):
    logout()

st.sidebar.write("---")
view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Chairman Dashboard"])

# Permissions
# Activity Log & Contribution Tracker: Chairman and Representative only
can_edit_reports = user_role in ["Chairman", "Representative", "Teacher"]
# Management: Chairman and Teacher only
can_manage = user_role in ["Chairman", "Teacher"]

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_project} Dashboard")
    
    m_df = st.session_state.data["members"]
    project_members = m_df[m_df['Project'] == view_project]
    reps = project_members[project_members['Role'] == "Representative"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 Project Leadership")
        if not reps.empty:
            for _, r in reps.iterrows():
                st.write(f"✅ **Representative:** {r['Name']}")
        else:
            st.info("No representatives assigned yet.")
        
        st.write("---")
        st.subheader("📅 Scheduled Events")
        p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
        if p_events:
            for e in p_events:
                color = "blue" if e['type'] == "Discussion" else "green"
                st.markdown(f"**:{color}[{e['type']}]** - {e['date']} \n\n *{e['desc']}*")
        else:
            st.write("No upcoming rehearsals or discussions.")

    with col2:
        st.subheader("👥 Member List")
        if not project_members.empty:
            st.table(project_members[["Name", "Role"]])
            
            st.write("---")
            st.subheader("RSVP")
            u_name = st.selectbox("Select Your Name", project_members["Name"])
            status = st.radio("Can you attend the next event?", ["Yes", "No", "Late"])
            if st.button("Submit Attendance"):
                st.success(f"RSVP recorded for {u_name}")
        else:
            st.warning("The Chairman has not added members to this project yet.")

# --- 2. ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_project} Activity Log")
    
    if can_edit_reports:
        with st.form("log_form", clear_on_submit=True):
            st.subheader("Add Daily Report")
            l_date = st.date_input("Date of Activity")
            l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("What was done today?")
            if st.form_submit_button("Submit Log"):
                st.session_state.data["logs"].append({
                    "Project": view_project, "Date": str(l_date), "Type": l_type, "Desc": l_desc
                })
                st.success("Log added!")
                st.rerun()
    
    st.write("---")
    p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
    if not p_logs:
        st.info("No activity logs recorded.")
    else:
        for l in reversed(p_logs):
            with st.expander(f"{l['Date']} - {l['Type']}"):
                st.write(l['Desc'])

# --- 3. CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Contribution Tracker")
    
    if can_edit_reports:
        with st.form("contrib_form", clear_on_submit=True):
            p_members = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_project]
            if not p_members.empty:
                who = st.selectbox("Member", p_members["Name"])
                c_h = st.number_input("Hours", min_value=0, step=1)
                c_m = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                if st.form_submit_button("Save Contribution"):
                    st.session_state.data["contributions"].append({
                        "Project": view_project, "Name": who, "Time": f"{c_h}h {c_m}m"
                    })
                    st.success("Contribution recorded.")
                    st.rerun()
            else:
                st.error("Add members first in the Dashboard.")
                st.form_submit_button("Disabled", disabled=True)

    st.write("---")
    c_list = [c for c in st.session_state.data["contributions"] if c['Project'] == view_project]
    if c_list:
        st.table(pd.DataFrame(c_list))
    else:
        st.info("No contributions recorded yet.")

# --- 4. CHAIRMAN DASHBOARD ---
elif page == "Chairman Dashboard":
    if can_manage:
        st.title("👑 Chairman's Management Center")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Manage Project Members")
            with st.form("member_add", clear_on_submit=True):
                m_name = st.text_input("Member Name")
                m_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                m_role = st.selectbox("Role", ["Member", "Representative"])
                if st.form_submit_button("Add Member"):
                    new_row = pd.DataFrame([{"Name": m_name, "Project": m_proj, "Role": m_role}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_row], ignore_index=True)
                    st.success(f"Added {m_name} to {m_proj}")
                    st.rerun()

        with col_b:
            st.subheader("Schedule Meeting/Rehearsal")
            with st.form("event_add", clear_on_submit=True):
                e_proj = st.selectbox("For Project", ["SKIT", "BROCHURE"])
                e_type = st.radio("Event Type", ["Discussion", "Rehearsal"])
                e_date = st.date_input("Pick Date")
                e_time = st.time_input("Pick Time")
                e_desc = st.text_input("Notes (e.g. Venue)")
                if st.form_submit_button("Post Event"):
                    st.session_state.data["events"].append({
                        "project": e_proj, "type": e_type, "date": f"{e_date} at {e_time}", "desc": e_desc
                    })
                    st.success("Event scheduled!")
                    st.rerun()

        st.write("---")
        st.subheader("Full Class Roster")
        st.dataframe(st.session_state.data["members"], use_container_width=True)
    else:
        st.error("Access denied. Only the Chairman or Teacher can access this panel.")
