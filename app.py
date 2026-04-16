import streamlit as st
import pandas as pd

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

# --- INITIALIZE DATA (CRITICAL FIX FOR NAMEERROR) ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "events": []
    }

# --- SIDEBAR LOGIN ---
st.sidebar.title("🔐 VIA Portal Login")
user_role = st.sidebar.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
password = st.sidebar.text_input("Password", type="password")

# Verify password before showing any content
if password == USER_CREDENTIALS[user_role]:
    st.sidebar.success(f"Logged in as {user_role}")
    
    # --- NAVIGATION ---
    st.sidebar.write("---")
    view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
    page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Panel"])

    # Define common variables for all pages to avoid NameError
    m_df = st.session_state.data["members"]
    is_leader = user_role in ["Chairman", "Representative", "Teacher"]
    is_chairman = user_role == "Chairman"

    # --- 1. DASHBOARD & RSVP ---
    if page == "Dashboard":
        st.title(f"🚀 {view_project} Project Hub")
        
        # Filter reps safely
        reps = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Representative")]
        rep_names = ", ".join(reps['Name'].tolist()) if not reps.empty else "None Assigned"
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📌 Project Info")
            st.write(f"**Representative(s):** {rep_names}")
            
            p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
            if p_events:
                for e in p_events:
                    st.warning(f"**{e['type']}** on {e['date']} \n\n {e['desc']}")
            else:
                st.info("No upcoming events scheduled.")

        with col2:
            st.subheader("👥 Project Members")
            p_members = m_df[m_df['Project'] == view_project]['Name'].tolist()
            if p_members:
                st.write(", ".join(p_members))
            else:
                st.write("Roster is currently empty.")
            
            st.write("---")
            st.subheader("RSVP")
            if p_members:
                u_name = st.selectbox("Your Name", p_members)
                status = st.radio("Attendance", ["Attending", "Absent", "Late"])
                if st.button("Submit RSVP"):
                    st.toast(f"Recorded: {u_name} is {status}")
            else:
                st.caption("Chairman must add members before RSVP is available.")

    # --- 2. ACTIVITY LOG ---
    elif page == "Activity Log":
        st.title(f"📝 {view_project} Activity Log")
        
        if is_leader:
            with st.form("log_form", clear_on_submit=True):
                st.subheader("New Entry")
                l_date = st.date_input("Date")
                l_type = st.selectbox("Category", ["Discussion", "Rehearsal", "Drafting"])
                l_desc = st.text_area("What happened today?")
                if st.form_submit_button("Post Log"):
                    st.session_state.data["logs"].append({
                        "Project": view_project, "Date": str(l_date), "Type": l_type, "Desc": l_desc
                    })
                    st.success("Log Saved!")
                    st.rerun()
        
        st.write("---")
        p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
        if not p_logs:
            st.info("No logs found for this project.")
        else:
            for l in reversed(p_logs):
                with st.expander(f"{l['Date']} - {l['Type']}"):
                    st.write(l['Desc'])

    # --- 3. CONTRIBUTION TRACKER ---
    elif page == "Contribution Tracker":
        st.title(f"⏳ {view_project} Contributions")
        
        if is_leader:
            with st.form("time_form", clear_on_submit=True):
                p_m_list = m_df[m_df['Project'] == view_project]['Name'].tolist()
                if p_m_list:
                    who = st.selectbox("Select Member", p_m_list)
                    c_h = st.number_input("Hours", min_value=0, step=1)
                    c_m = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                    if st.form_submit_button("Save Time"):
                        st.session_state.data["contributions"].append({
                            "Project": view_project, "Name": who, "Time": f"{c_h}h {c_m}m"
                        })
                        st.success("Time recorded!")
                        st.rerun()
                else:
                    st.warning("Please add members in the Management Panel first.")
                    st.form_submit_button("Disabled", disabled=True)
        
        st.write("---")
        c_list = [c for c in st.session_state.data["contributions"] if c['Project'] == view_project]
        if c_list:
            st.table(pd.DataFrame(c_list))
        else:
            st.info("No contribution records yet.")

    # --- 4. MANAGEMENT PANEL ---
    elif page == "Management Panel":
        if is_chairman or user_role == "Teacher":
            st.title("⚙️ Chairman Management")
            
            t1, t2 = st.tabs(["Roster Management", "Event Scheduling"])
            
            with t1:
                with st.form("add_mem_form", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    new_n = c1.text_input("Name")
                    new_p = c2.selectbox("Project", ["SKIT", "BROCHURE"])
                    new_r = c3.selectbox("Role", ["Member", "Representative"])
                    if st.form_submit_button("Add Member"):
                        if new_n:
                            new_row = pd.DataFrame([{"Name": new_n, "Project": new_p, "Role": new_r}])
                            st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_row], ignore_index=True)
                            st.success(f"Added {new_n} to {new_p}")
                            st.rerun()
                
                st.subheader("Current Roster")
                st.dataframe(st.session_state.data["members"], use_container_width=True)

            with t2:
                with st.form("event_sch_form", clear_on_submit=True):
                    e_p = st.selectbox("Target Project", ["SKIT", "BROCHURE"])
                    e_t = st.radio("Event Type", ["Discussion", "Rehearsal"])
                    e_d = st.date_input("Date")
                    e_clock = st.time_input("Time")
                    e_n = st.text_input("Location/Notes")
                    if st.form_submit_button("Set Event"):
                        st.session_state.data["events"].append({
                            "project": e_p, "type": e_t, "date": f"{e_d} {e_clock}", "desc": e_n
                        })
                        st.success(f"{e_t} scheduled for {e_p}!")
        else:
            st.error("Access restricted to Chairman/Teacher.")

# Error handling for wrong password
elif password != "":
    st.sidebar.error("❌ Incorrect Password")
else:
    st.title("👋 Welcome to the VIA Hub")
    st.info("Please select your role and enter the password in the sidebar to begin.")
