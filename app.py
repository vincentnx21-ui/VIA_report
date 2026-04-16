import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# This password is required for Chairman/Reps to unlock sensitive logs
ADMIN_PASSWORD = "VIA_LEADER_2026" 

# --- INITIALIZE DATA ---
if 'activities' not in st.session_state:
    st.session_state.activities = []
if 'contributions' not in st.session_state:
    st.session_state.contributions = []
if 'members' not in st.session_state:
    st.session_state.members = ["Member 1", "Member 2", "Member 3"]
if 'leaders' not in st.session_state:
    st.session_state.leaders = {
        "Chairman": "TBD", 
        "Rep_Skit": "TBD", 
        "Rep_Brochure": "TBD"
    }

# --- SIDEBAR ---
st.sidebar.title("📌 VIA Navigation")
project_choice = st.sidebar.selectbox("Current Project", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Go to", ["Dashboard & RSVP", "Team Directory", "Activity Log", "Contribution Tracker", "Chairman's Panel"])

# Leader Authentication
st.sidebar.markdown("---")
st.sidebar.subheader("🔒 Leader Access")
user_role = st.sidebar.selectbox("Identify as:", ["Member", "Chairman", "Project Representative"])
pw = st.sidebar.text_input("Enter Password", type="password")

# Permission Check
is_authorized = (pw == ADMIN_PASSWORD and user_role in ["Chairman", "Project Representative"])
is_chairman = (pw == ADMIN_PASSWORD and user_role == "Chairman")

# --- PAGE 1: DASHBOARD & RSVP ---
if page == "Dashboard & RSVP":
    st.title(f"🚀 {project_choice} Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upcoming Schedule")
        # These would ideally be set in the Chairman's panel
        st.info("Next Discussion: April 25, 2026\n\nNext Rehearsal: May 2, 2026")
    
    with col2:
        st.subheader("Attendance RSVP")
        name = st.selectbox("Select Your Name", st.session_state.members)
        can_attend = st.radio("Will you be there?", ["Yes", "No", "Late"])
        if st.button("Submit Attendance"):
            st.success(f"RSVP recorded for {name}!")

# --- PAGE 2: TEAM DIRECTORY (Public) ---
elif page == "Team Directory":
    st.title("👥 VIA Project Organization")
    
    st.subheader("Leadership Team")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"**Class Chairman**\n\n{st.session_state.leaders['Chairman']}")
    with c2:
        st.success(f"**Skit Representative**\n\n{st.session_state.leaders['Rep_Skit']}")
    with c3:
        st.warning(f"**Brochure Representative**\n\n{st.session_state.leaders['Rep_Brochure']}")
    
    st.write("---")
    st.subheader("Class Members")
    st.write(", ".join(st.session_state.members))

# --- PAGE 3: ACTIVITY LOG (Protected) ---
elif page == "Activity Log":
    st.title("📝 Activity Log")
    
    if is_authorized:
        st.write(f"Logged in as: **{user_role}**")
        with st.form("log_form", clear_on_submit=True):
            date = st.date_input("Date")
            act_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            desc = st.text_area("Detailed Report (What was done?)")
            if st.form_submit_button("Submit Report"):
                st.session_state.activities.append({
                    "Project": project_choice, "Date": str(date), "Type": act_type, "Desc": desc
                })
                st.balloons()
        
        st.write("### Past Logs")
        logs = [l for l in st.session_state.activities if l['Project'] == project_choice]
        for l in reversed(logs):
            with st.expander(f"{l['Date']} - {l['Type']}"):
                st.write(l['Desc'])
    else:
        st.error("🔒 Access Restricted. This page is only for the Chairman and Project Representatives. Please enter the password in the sidebar.")

# --- PAGE 4: CONTRIBUTION TRACKER (Protected) ---
elif page == "Contribution Tracker":
    st.title("⏳ Contribution Tracker")
    
    if is_authorized:
        with st.form("contrib_form", clear_on_submit=True):
            c_name = st.selectbox("Member Name", st.session_state.members)
            h = st.number_input("Hours", min_value=0)
            m = st.number_input("Minutes", min_value=0, max_value=59)
            if st.form_submit_button("Add Contribution"):
                st.session_state.contributions.append({
                    "Name": c_name, "Hours": h, "Mins": m, "Project": project_choice
                })
        
        if st.session_state.contributions:
            df = pd.DataFrame(st.session_state.contributions)
            st.table(df[df['Project'] == project_choice])
    else:
        st.error("🔒 Access Restricted. This page is only for the Chairman and Project Representatives.")

# --- PAGE 5: CHAIRMAN'S PANEL (Chairman Only) ---
elif page == "Chairman's Panel":
    if is_chairman:
        st.title("🔑 Chairman's Administrative Control")
        
        st.subheader("Assign Leadership")
        st.session_state.leaders["Chairman"] = st.text_input("Chairman Name", st.session_state.leaders["Chairman"])
        st.session_state.leaders["Rep_Skit"] = st.text_input("Skit Rep Name", st.session_state.leaders["Rep_Skit"])
        st.session_state.leaders["Rep_Brochure"] = st.text_input("Brochure Rep Name", st.session_state.leaders["Rep_Brochure"])
        
        st.subheader("Class Roster Management")
        new_m = st.text_input("Add New Member Name")
        if st.button("Add Member"):
            st.session_state.members.append(new_m)
            st.rerun()
    else:
        st.error("🚫 Exclusive Access. Only the Chairman can modify leaders and members.")
