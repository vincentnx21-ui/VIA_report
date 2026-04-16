import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# Change this password to something your Chairman/Rep knows
ADMIN_PASSWORD = "VIA_LEADER_2026" 

# --- INITIALIZE DATA ---
if 'activities' not in st.session_state:
    st.session_state.activities = []
if 'contributions' not in st.session_state:
    st.session_state.contributions = []
if 'members' not in st.session_state:
    # Default list - Chairman can edit this in Admin Panel
    st.session_state.members = ["Member A", "Member B", "Member C"]
if 'leaders' not in st.session_state:
    st.session_state.leaders = {
        "Chairman": "TBD", 
        "Rep_Skit": "TBD", 
        "Rep_Brochure": "TBD"
    }

# --- SIDEBAR ---
st.sidebar.title("📌 VIA Navigation")
project_choice = st.sidebar.selectbox("Select Project Scope", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Go to", ["Dashboard & Attendance", "Team Directory", "Activity Log", "Contribution Tracker", "Admin Panel"])

# Admin Login Logic
is_admin = False
with st.sidebar.expander("Admin/Rep Login"):
    pw = st.text_input("Password", type="password")
    if pw == ADMIN_PASSWORD:
        is_admin = True
        st.sidebar.success("Logged in as Leader")

# --- PAGE 1: DASHBOARD & ATTENDANCE ---
if page == "Dashboard & Attendance":
    st.title(f"🚀 {project_choice} Project Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Upcoming Events")
        st.info("Check here for the next Discussion or Rehearsal date set by the Chairman.")
    
    with col2:
        st.subheader("RSVP for Next Session")
        name = st.selectbox("Your Name", st.session_state.members)
        can_attend = st.radio("Can you attend?", ["Yes", "No", "Late"])
        if st.button("Submit RSVP"):
            st.toast(f"Status recorded for {name}!")

# --- PAGE 2: TEAM DIRECTORY (Visible to everyone) ---
elif page == "Team Directory":
    st.title("👥 VIA Project Members")
    
    # Leaderboard Cards
    c1, c2, c3 = st.columns(3)
    c1.metric("Class Chairman", st.session_state.leaders["Chairman"])
    c2.metric("Skit Representative", st.session_state.leaders["Rep_Skit"])
    c3.metric("Brochure Representative", st.session_state.leaders["Rep_Brochure"])
    
    st.write("---")
    st.subheader("Full Member List")
    st.write(", ".join(st.session_state.members))

# --- PAGE 3: ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Daily Activity Log")
    
    if is_admin:
        with st.form("log_form", clear_on_submit=True):
            date = st.date_input("Date of Activity")
            act_type = st.selectbox("Type", ["Discussion", "Rehearsal", "Production"])
            desc = st.text_area("Summary of work done")
            if st.form_submit_button("Post Log"):
                st.session_state.activities.append({
                    "Project": project_choice, 
                    "Date": str(date), 
                    "Type": act_type, 
                    "Desc": desc
                })
                st.success("Log added successfully!")
    
    st.write("---")
    logs = [l for l in st.session_state.activities if l['Project'] == project_choice]
    if not logs:
        st.info("No logs recorded for this project yet.")
    else:
        for l in reversed(logs):
            with st.expander(f"{l['Date']} - {l['Type']}"):
                st.write(l['Desc'])

# --- PAGE 4: CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Time Contribution Report")
    
    if is_admin:
        with st.form("contrib_form", clear_on_submit=True):
            c_name = st.selectbox("Select Member", st.session_state.members)
            h = st.number_input("Hours", min_value=0)
            m = st.number_input("Minutes", min_value=0, max_value=59)
            if st.form_submit_button("Save Contribution"):
                st.session_state.contributions.append({
                    "Name": c_name, "Hours": h, "Mins": m, "Project": project_choice
                })
                st.success("Time saved.")

    if st.session_state.contributions:
        df = pd.DataFrame(st.session_state.contributions)
        st.dataframe(df[df['Project'] == project_choice], use_container_width=True)
    else:
        st.warning("No contribution data yet.")

# --- PAGE 5: ADMIN PANEL ---
elif page == "Admin Panel":
    if is_admin:
        st.title("🔑 Chairman's Command Center")
        
        # Setting Leaders
        st.subheader("1. Assign Roles")
        st.session_state.leaders["Chairman"] = st.text_input("Chairman Name", st.session_state.leaders["Chairman"])
        st.session_state.leaders["Rep_Skit"] = st.text_input("Skit Rep Name", st.session_state.leaders["Rep_Skit"])
        st.session_state.leaders["Rep_Brochure"] = st.text_input("Brochure Rep Name", st.session_state.leaders["Rep_Brochure"])
        
        # Setting Members
        st.subheader("2. Add Members")
        new_m = st.text_input("New Member Name")
        if st.button("Add to Class"):
            if new_m and new_m not in st.session_state.members:
                st.session_state.members.append(new_m)
                st.rerun()
    else:
        st.error("Please log in with the Admin Password in the sidebar to access these controls.")
