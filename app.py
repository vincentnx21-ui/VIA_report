import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# Simple Role-Based Access Control
ADMIN_PASSWORD = "VIA_LEADER_2026" # Change this!

# Initialize "Database" (In a real app, use a CSV or Database)
if 'activities' not in st.session_state:
    st.session_state.activities = []
if 'attendance' not in st.session_state:
    st.session_state.attendance = {}
if 'members' not in st.session_state:
    st.session_state.members = ["Member 1", "Member 2", "Member 3"]
if 'leaders' not in st.session_state:
    st.session_state.leaders = {"Chairman": "None", "Rep_Skit": "None", "Rep_Brochure": "None"}

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 VIA Navigation")
project = st.sidebar.selectbox("Select Project", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Go to", ["Dashboard & Attendance", "Activity Log", "Contribution Tracker", "Admin Panel"])

# --- ADMIN CHECK ---
is_admin = False
with st.sidebar.expander("Admin Login"):
    pw = st.text_input("Enter Admin Password", type="password")
    if pw == ADMIN_PASSWORD:
        is_admin = True
        st.success("Admin Access Granted")

# --- PAGE 1: DASHBOARD & ATTENDANCE ---
if page == "Dashboard & Attendance":
    st.title(f"🚀 {project} Project Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Upcoming Events")
        # In a full version, these would be pulled from a list set by the Chairman
        st.info("Next Meeting: April 20, 2026 - 2:00 PM (Rehearsal)")
    
    with col2:
        st.subheader("RSVP / Attendance")
        name = st.selectbox("Select Your Name", st.session_state.members)
        status = st.radio("Can you attend?", ["Yes", "No", "Maybe"])
        if st.button("Submit RSVP"):
            st.success(f"Thank you {name}, your status '{status}' has been recorded.")

# --- PAGE 2: ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Daily Activity Log")
    
    if is_admin:
        with st.form("log_form"):
            date = st.date_input("Date")
            type = st.selectbox("Type", ["Discussion", "Rehearsal", "Production"])
            desc = st.text_area("What did the class do today?")
            submit = st.form_submit_button("Post Log")
            if submit:
                st.session_state.activities.append({"Date": date, "Type": type, "Desc": desc})
    
    st.write("---")
    for log in reversed(st.session_state.activities):
        st.write(f"**{log['Date']} - {log['Type']}**")
        st.info(log['Desc'])

# --- PAGE 3: CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Contribution Tracker (Minutes/Hours)")
    
    if is_admin:
        with st.expander("Add Contribution Record"):
            c_name = st.selectbox("Member", st.session_state.members)
            c_hours = st.number_input("Hours", min_value=0, step=1)
            c_mins = st.number_input("Minutes", min_value=0, max_value=59, step=1)
            if st.button("Save Contribution"):
                st.success(f"Recorded {c_hours}h {c_mins}m for {c_name}")

    # Visual Table
    st.table(pd.DataFrame({
        "Member": st.session_state.members,
        "Total Time": ["2h 30m", "1h 45m", "3h 00m"] # Placeholder data
    }))

# --- PAGE 4: ADMIN PANEL ---
elif page == "Admin Panel":
    if is_admin:
        st.title("🔑 Chairman's Management")
        
        st.subheader("Set Project Leadership")
        st.session_state.leaders["Chairman"] = st.text_input("Chairman Name", st.session_state.leaders["Chairman"])
        st.session_state.leaders["Rep_Skit"] = st.text_input("Skit Representative", st.session_state.leaders["Rep_Skit"])
        
        st.subheader("Manage Members")
        new_member = st.text_input("Add New Member")
        if st.button("Add Member"):
            st.session_state.members.append(new_member)
            st.rerun()
            
    else:
        st.error("This page is restricted to the VIA Chairman and Representative.")
