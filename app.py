import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Tracker", layout="wide")

# Simple Admin Password (Change this!)
ADMIN_PASSWORD = "via_leader_2026"

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("📌 VIA Navigation")
project = st.sidebar.radio("Select Project", ["SKIT", "BROCHURE"])
page = st.sidebar.selectbox("Go to", ["Home & Attendance", "Activity Log", "Contribution Tracker"])

# --- ADMIN LOGIN ---
st.sidebar.markdown("---")
is_admin = False
admin_code = st.sidebar.text_input("Admin Access", type="password", help="For Chairman/Rep only")
if admin_code == ADMIN_PASSWORD:
    is_admin = True
    st.sidebar.success("Admin Mode Active")

# --- APP LOGIC ---
st.title(f"Project: {project}")

if page == "Home & Attendance":
    st.header("📅 Upcoming Rehearsals / Discussions")
    
    # Placeholder for current schedule
    st.info("Next Meeting: Friday, Oct 20th | 3:00 PM | School Hall")
    
    st.subheader("Attendance Check-in")
    with st.form("attendance_form"):
        name = st.text_input("Your Name")
        can_attend = st.radio("Can you attend?", ["Yes", "No", "Late"])
        reason = st.text_area("Reason (if No/Late)")
        submitted = st.form_submit_button("Submit Attendance")
        if submitted:
            st.success(f"Thank you {name}, your response has been recorded.")

    # Admin: Set the next date
    if is_admin:
        st.divider()
        st.subheader("🛠️ Set New Meeting Date (Admin Only)")
        new_date = st.date_input("Meeting Date")
        new_time = st.time_input("Meeting Time")
        if st.button("Update Meeting Schedule"):
            st.success("Schedule updated for the team!")

elif page == "Activity Log":
    st.header("📝 Daily Activity Log")
    
    # Display what has been done
    st.write("Recent activities will appear here...")
    
    if is_admin:
        with st.expander("Add New Activity Log"):
            log_date = st.date_input("Log Date", datetime.now())
            activity_type = st.selectbox("Type", ["Discussion", "Rehearsal", "Drafting"])
            details = st.text_area("What did the class achieve today?")
            if st.button("Save Log"):
                st.success("Activity logged successfully!")

elif page == "Contribution Tracker":
    st.header("⏳ Contribution Tracker")
    
    # Sample Data Table
    data = {
        "Name": ["Student A", "Student B"],
        "Role": ["Scriptwriter", "Actor"],
        "Hours": [2, 5],
        "Minutes": [30, 0]
    }
    df = pd.DataFrame(data)
    st.table(df)

    if is_admin:
        st.divider()
        st.subheader("➕ Add Member Contribution")
        col1, col2 = st.columns(2)
        with col1:
            m_name = st.text_input("Member Name")
            m_hours = st.number_input("Hours", min_value=0)
        with col2:
            m_role = st.text_input("Role/Task")
            m_mins = st.number_input("Minutes", min_value=0, max_value=59)
        
        if st.button("Update Record"):
            st.success(f"Updated contribution for {m_name}")
