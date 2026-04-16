import streamlit as st
import pandas as pd
from datetime import datetime

# Page Configuration
st.set_page_config(page_title="VIA Class Report", layout="wide")

# Sidebar Navigation
st.sidebar.title("📌 VIA Project Dashboard")
project = st.sidebar.radio("Select Project:", ["Skit", "Brochure"])
page = st.sidebar.selectbox("Go to:", ["Attendance/Scheduling", "Activity Log", "Contribution Tracker"])

st.title(f"Project: {project}")

# --- 1. Attendance & Scheduling ---
if page == "Attendance/Scheduling":
    st.header("📅 Schedule & Attendance")
    
    with st.form("attendance_form"):
        event_date = st.date_input("Event Date")
        event_type = st.selectbox("Type", ["Discussion", "Rehearsal", "Production"])
        member_name = st.text_input("Your Name")
        status = st.radio("Can you attend?", ["Yes", "No", "Maybe"])
        notes = st.text_area("Reason (if 'No' or 'Maybe')")
        
        if st.form_submit_button("Submit Response"):
            st.success(f"Response recorded for {member_name}!")
            # In a real app, you'd save this to a CSV or Database

# --- 2. Activity Log ---
elif page == "Activity Log":
    st.header("📝 Daily Activity Report")
    
    with st.form("activity_form"):
        log_date = st.date_input("Date of Activity", value=datetime.now())
        activity_summary = st.text_area("What did the class do today?")
        challenges = st.text_area("Any challenges faced?")
        
        if st.form_submit_button("Post Log"):
            st.info("Activity log saved.")

# --- 3. Contribution Tracker ---
elif page == "Contribution Tracker":
    st.header("⏳ Contribution Minutes/Hours")
    
    with st.form("hours_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Member Name")
            task = st.text_input("Task Completed")
        with col2:
            hours = st.number_input("Hours", min_value=0, step=1)
            minutes = st.number_input("Minutes", min_value=0, max_value=59, step=1)
            
        if st.form_submit_button("Log Time"):
            st.success(f"Logged {hours}h {minutes}m for {name}")

    # Example Table View
    st.subheader("Summary Table (Example Data)")
    example_data = pd.DataFrame({
        "Member": ["Alice", "Bob"],
        "Task": ["Script Writing", "Prop Design"],
        "Total Time": ["2h 30m", "1h 45m"]
    })
    st.table(example_data)
