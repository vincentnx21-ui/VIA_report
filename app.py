import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# Simple Role-Based Access Control
ADMIN_PASSWORD = "VIA_LEADER_2026" 

# --- INITIALIZE DATABASE ---
# We use .get() and list checks to prevent ValueErrors
if 'activities' not in st.session_state:
    st.session_state.activities = []
if 'contributions' not in st.session_state:
    st.session_state.contributions = []
if 'members' not in st.session_state:
    st.session_state.members = ["Member 1", "Member 2", "Member 3"]
if 'leaders' not in st.session_state:
    st.session_state.leaders = {"Chairman": "None", "Rep_Skit": "None", "Rep_Brochure": "None"}

# --- SIDEBAR ---
st.sidebar.title("📌 VIA Navigation")
project = st.sidebar.selectbox("Select Project", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Go to", ["Dashboard & Attendance", "Activity Log", "Contribution Tracker", "Admin Panel"])

# Admin Login Logic
is_admin = False
with st.sidebar.expander("Admin Login"):
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == ADMIN_PASSWORD:
        is_admin = True
        st.sidebar.success("Admin Access Granted")

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard & Attendance":
    st.title(f"🚀 {project} Project Dashboard")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Current Leadership")
        st.write(f"**Chairman:** {st.session_state.leaders['Chairman']}")
        st.write(f"**Project Rep:** {st.session_state.leaders['Rep_Skit'] if project == 'SKIT' else st.session_state.leaders['Rep_Brochure']}")

    with col2:
        st.subheader("RSVP")
        name = st.selectbox("Your Name", st.session_state.members)
        if st.button("I'm Attending Next Session"):
            st.toast(f"Recorded attendance for {name}!")

# --- PAGE 2: ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Daily Activity Log")
    
    if is_admin:
        with st.form("log_form", clear_on_submit=True):
            date = st.date_input("Date")
            act_type = st.selectbox("Type", ["Discussion", "Rehearsal", "Production"])
            desc = st.text_area("Summary of work done")
            if st.form_submit_button("Post Log"):
                st.session_state.activities.append({"Project": project, "Date": str(date), "Type": act_type, "Desc": desc})
                st.success("Log saved!")

    st.write("---")
    # Filter logs for the selected project
    project_logs = [log for log in st.session_state.activities if log['Project'] == project]
    
    if not project_logs:
        st.info("No logs recorded for this project yet.")
    else:
        for log in reversed(project_logs):
            with st.expander(f"{log['Date']} - {log['Type']}"):
                st.write(log['Desc'])

# --- PAGE 3: CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Contribution Tracker")
    
    if is_admin:
        with st.form("contrib_form", clear_on_submit=True):
            c_name = st.selectbox("Member", st.session_state.members)
            c_hours = st.number_input("Hours", min_value=0)
            c_mins = st.number_input("Minutes", min_value=0, max_value=59)
            if st.form_submit_button("Log Time"):
                st.session_state.contributions.append({"Name": c_name, "Hours": c_hours, "Mins": c_mins, "Project": project})
                st.success("Time recorded!")

    if not st.session_state.contributions:
        st.warning("No contribution data available yet.")
    else:
        df = pd.DataFrame(st.session_state.contributions)
        st.table(df[df['Project'] == project])

# --- PAGE 4: ADMIN PANEL ---
elif page == "Admin Panel":
    if is_admin:
        st.title("🔑 Chairman's Management")
        
        # Set Leadership
        st.subheader("Assign Roles")
        st.session_state.leaders["Chairman"] = st.text_input("Chairman Name", st.session_state.leaders["Chairman"])
        if project == "SKIT":
            st.session_state.leaders["Rep_Skit"] = st.text_input("Skit Representative", st.session_state.leaders["Rep_Skit"])
        else:
            st.session_state.leaders["Rep_Brochure"] = st.text_input("Brochure Representative", st.session_state.leaders["Rep_Brochure"])
        
        # Member Management
        st.subheader("Class Roster")
        new_mem = st.text_input("Add Member Name")
        if st.button("Add to Class"):
            st.session_state.members.append(new_mem)
            st.rerun() # Refresh to update selectboxes
    else:
        st.error("Access Denied: Please enter the Admin Password in the sidebar.")
