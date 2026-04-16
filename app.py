import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Hub", layout="wide")

# --- USER PASSWORDS (6 Users) ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- INITIALIZE DATA ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "events": [] # List of dicts: {project, date, type, description}
    }

# --- LOGIN SYSTEM ---
st.sidebar.title("🔐 VIA Portal Login")
user_role = st.sidebar.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
password = st.sidebar.text_input("Password", type="password")

if password == USER_CREDENTIALS[user_role]:
    st.sidebar.success(f"Logged in as {user_role}")
    
    # --- NAVIGATION ---
    st.sidebar.write("---")
    view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
    page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Panel"])

    # --- PERMISSIONS LOGIC ---
    is_leader = user_role in ["Chairman", "Representative", "Teacher"]
    is_chairman = user_role == "Chairman"

    # --- 1. DASHBOARD & RSVP ---
    if page == "Dashboard":
        st.title(f"🚀 {view_project} Project Hub")
        
        # Display Representatives for the project
        m_df = st.session_state.data["members"]
        reps = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Representative")]
        rep_names = ", ".join(reps['Name'].tolist()) if not reps.empty else "None Assigned"
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📌 Project Info")
            st.write(f"**Representative(s):** {rep_names}")
            
            st.write("**Scheduled Events:**")
            p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
            if p_events:
                for e in p_events:
                    st.warning(f"{e['type']} on {e['date']} \n\n {e['desc']}")
            else:
                st.write("No upcoming events.")

        with col2:
            st.subheader("👥 Project Members")
            p_members = m_df[m_df['Project'] == view_project]['Name'].tolist()
            if p_members:
                st.write(", ".join(p_members))
            else:
                st.write("Roster is empty.")
            
            st.write("---")
            st.subheader("RSVP")
            if p_members:
                u_name = st.selectbox("Your Name", p_members)
                status = st.radio("Attendance", ["Attending", "Absent", "Late"])
                if st.button("Submit Attendance"):
                    st.toast(f"RSVP recorded for {u_name}")
            else:
                st.info("Ask Chairman to add you to the roster.")

    # --- 2. ACTIVITY LOG (Chairman/Rep/Teacher/Committee) ---
    elif page == "Activity Log":
        st.title(f"📝 {view_project} Activity Log")
        
        # Committee can see but only Leader can add
        if is_leader:
            with st.form("log_form", clear_on_submit=True):
                st.subheader("Record Daily Progress")
                log_date = st.date_input("Date")
                log_type = st.selectbox("Category", ["Discussion", "Rehearsal", "Drafting", "Other"])
                log_desc = st.text_area("What did the class do today?")
                if st.form_submit_button("Post Log"):
                    st.session_state.data["logs"].append({
                        "Project": view_project, "Date": log_date, "Type": log_type, "Desc": log_desc
                    })
                    st.success("Log Saved!")
        
        st.write("---")
        p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
        for l in reversed(p_logs):
            with st.expander(f"{l['Date']} - {l['Type']}"):
                st.write(l['Desc'])

    # --- 3. CONTRIBUTION TRACKER (Chairman/Rep/Teacher/Committee) ---
    elif page == "Contribution Tracker":
        st.title(f"⏳ {view_project} Contribution")
        
        if is_leader:
            with st.form("time_form", clear_on_submit=True):
                p_members = m_df[m_df['Project'] == view_project]['Name'].tolist()
                who = st.selectbox("Member", p_members) if p_members else "None"
                c_h = st.number_input("Hours", min_value=0)
                c_m = st.number_input("Minutes", min_value=0, max_value=59)
                if st.form_submit_button("Log Contribution"):
                    st.session_state.data["contributions"].append({
                        "Project": view_project, "Name": who, "Hours": c_h, "Mins": c_m
                    })
        
        st.write("---")
        c_df = pd.DataFrame([c for c in st.session_state.data["contributions"] if c['Project'] == view_project])
        if not c_df.empty:
            st.dataframe(c_df, use_container_width=True)

    # --- 4. MANAGEMENT PANEL (Chairman/Teacher) ---
    elif page == "Management Panel":
        if is_chairman or user_role == "Teacher":
            st.title("⚙️ Chairman Management Console")
            
            tab1, tab2 = st.tabs(["Add Members", "Schedule Events"])
            
            with tab1:
                with st.form("member_form"):
                    col_name, col_proj, col_role = st.columns(3)
                    m_name = col_name.text_input("Full Name")
                    m_proj = col_proj.selectbox("Assign Project", ["SKIT", "BROCHURE"])
                    m_role = col_role.selectbox("Role", ["Member", "Representative"])
                    
                    if st.form_submit_button("Register Member"):
                        new_member = pd.DataFrame([{"Name": m_name, "Project": m_proj, "Role": m_role}])
                        st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_member], ignore_index=True)
                        st.rerun()
                
                st.subheader("Current Roster")
                st.dataframe(st.session_state.data["members"], use_container_width=True)

            with tab2:
                with st.form("event_form"):
                    st.subheader("Schedule Meeting/Rehearsal")
                    e_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                    e_type = st.radio("Event Type", ["Discussion", "Rehearsal"])
                    e_date = st.date_input("Date")
                    e_time = st.time_input("Time")
                    e_desc = st.text_input("Notes (e.g., Location)")
                    
                    if st.form_submit_button("Post Schedule"):
                        st.session_state.data["events"].append({
                            "project": e_proj, "type": e_type, "date": f"{e_date} {e_time}", "desc": e_desc
                        })
                        st.success(f"{e_type} Scheduled!")
        else:
            st.error("Only the Chairman or Teacher can access Management.")

elif password != "" :
    st.sidebar.error("Incorrect password for this role.")
else:
    st.info("Please enter your role password in the sidebar.")
