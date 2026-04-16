import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub", layout="wide")

# --- USER PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- INITIALIZE DATABASE (FIXED TO PREVENT KEYERROR) ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role", "SubRole"]),
        "logs": [],
        "contributions": [],
        "events": [] 
    }
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- LOGIN / LOGOUT LOGIC ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    role_input = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pw_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if pw_input == USER_CREDENTIALS[role_input]:
            st.session_state.logged_in = True
            st.session_state.user_role = role_input
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- SIDEBAR & NAVIGATION ---
st.sidebar.title(f"👤 {st.session_state.user_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

st.sidebar.write("---")
view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Center"])

# Permissions
u_role = st.session_state.user_role
is_chairman = u_role == "Chairman"
is_rep = u_role == "Representative"
is_teacher = u_role == "Teacher"
# Teachers, VIA Committee, Classmates, and Members cannot edit
can_edit = u_role in ["Chairman", "Representative"]

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_project} Hub")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Scheduled Events")
        # Safety check: filtering events
        all_events = st.session_state.data.get("events", [])
        p_events = [e for e in all_events if e.get('project') == view_project]
        
        if not p_events:
            st.info(f"No {view_project} events scheduled yet.")
        else:
            for i, e in enumerate(p_events):
                # Check if event has passed
                event_dt = datetime.combine(e['date'], e['start_time'])
                is_past = event_dt < datetime.now()
                
                status_label = "🔴 PASSED" if is_past else "🟢 UPCOMING"
                with st.expander(f"{e['type']} - {e['date'].strftime('%d %b')} ({status_label})"):
                    st.write(f"**Time:** {e['start_time'].strftime('%H:%M')} to {e['end_time'].strftime('%H:%M')}")
                    st.write(f"**Venue:** {e['venue']}")
                    
                    if can_edit and not is_past:
                        if st.button(f"Cancel Event {i}", key=f"del_{i}"):
                            st.session_state.data["events"].remove(e)
                            st.rerun()

    with col2:
        st.subheader("👥 Project Team")
        m_df = st.session_state.data["members"]
        proj_members = m_df[m_df['Project'] == view_project]
        
        if proj_members.empty:
            st.write("No members assigned by Chairman yet.")
        else:
            # Display Reps
            reps = proj_members[proj_members['Role'] == "Representative"]
            st.markdown("**Representatives:** " + (", ".join(reps['Name'].tolist()) if not reps.empty else "None"))
            
            if view_project == "SKIT":
                for sr in ["Actors", "Prop makers", "Cameraman"]:
                    sr_list = proj_members[proj_members['SubRole'] == sr]['Name'].tolist()
                    if sr_list:
                        st.write(f"**{sr}:** {', '.join(sr_list)}")
            else:
                others = proj_members[proj_members['Role'] == "Member"]['Name'].tolist()
                st.write("**Members:** " + (", ".join(others) if others else "None"))

# --- 2. ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_project} Activity Log")
    
    if can_edit:
        with st.form("log_form", clear_on_submit=True):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Activity", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("Progress Report")
            if st.form_submit_button("Submit Report"):
                st.session_state.data["logs"].append({
                    "Project": view_project, "Date": l_date, "Type": l_type, "Desc": l_desc
                })
                st.success("Log added!")
                st.rerun()
    
    st.write("---")
    logs = [l for l in st.session_state.data["logs"] if l.get('Project') == view_project]
    if not logs:
        st.info("No logs recorded.")
    for l in reversed(logs):
        with st.expander(f"{l['Date']} - {l['Type']}"):
            st.write(l['Desc'])

# --- 3. CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Contribution")
    
    if can_edit:
        with st.form("time_form", clear_on_submit=True):
            m_list = st.session_state.data["members"]
            p_names = m_list[m_list['Project'] == view_project]['Name'].tolist()
            if p_names:
                who = st.selectbox("Member", p_names)
                h = st.number_input("Hours", min_value=0, step=1)
                m = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                if st.form_submit_button("Record Time"):
                    st.session_state.data["contributions"].append({
                        "Project": view_project, "Name": who, "Time": f"{h}h {m}m"
                    })
                    st.rerun()
            else:
                st.warning("Chairman must add members to this project first.")
                st.form_submit_button("Submit (Disabled)", disabled=True)

    c_records = [c for c in st.session_state.data["contributions"] if c.get('Project') == view_project]
    if c_records:
        st.table(pd.DataFrame(c_records))
    else:
        st.info("No contributions recorded yet.")

# --- 4. MANAGEMENT CENTER ---
elif page == "Management Center":
    if is_chairman:
        st.title("👑 Chairman Management Center")
        t1, t2 = st.tabs(["Member Management", "Event Scheduler"])
        
        with t1:
            with st.form("mem_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                m_name = c1.text_input("Member Name")
                m_proj = c2.selectbox("Project", ["SKIT", "BROCHURE"])
                m_role = c3.selectbox("Role", ["Member", "Representative"])
                
                m_sub = "N/A"
                if m_proj == "SKIT":
                    m_sub = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman"])
                
                if st.form_submit_button("Add Member"):
                    if m_name:
                        new_m = pd.DataFrame([{"Name": m_name, "Project": m_proj, "Role": m_role, "SubRole": m_sub}])
                        st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                        st.rerun()
            st.dataframe(st.session_state.data["members"], use_container_width=True)

        with t2:
            with st.form("event_form", clear_on_submit=True):
                e_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                e_type = st.radio("Type", ["Discussion", "Rehearsal"])
                e_date = st.date_input("Date")
                col_t1, col_t2 = st.columns(2)
                e_start = col_t1.time_input("Start Time")
                e_end = col_t2.time_input("End Time")
                e_venue = st.text_input("Venue")
                
                if st.form_submit_button("Schedule Event"):
                    st.session_state.data["events"].append({
                        "project": e_proj, "type": e_type, "date": e_date, 
                        "start_time": e_start, "end_time": e_end, "venue": e_venue
                    })
                    st.success("Event added!")
                    st.rerun()
    else:
        st.title("🛡️ Access Denied")
        st.error("The Chairman Management Center is only visible to the Chairman.")
