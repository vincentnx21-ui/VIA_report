import streamlit as st
import pandas as pd

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

# --- INITIALIZE DATABASE ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "events": []
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# --- LOGOUT FUNCTION ---
def logout():
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

# --- LOGIN UI ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Class Report Portal")
    with st.container(border=True):
        role_input = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
        pw_input = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw_input == USER_CREDENTIALS[role_input]:
                st.session_state.logged_in = True
                st.session_state.user_role = role_input
                st.rerun()
            else:
                st.error("Invalid password.")
    st.stop()

# --- LOGGED IN CONTENT ---
user_role = st.session_state.user_role
m_df = st.session_state.data["members"]

# Sidebar Logic
st.sidebar.title(f"👤 {user_role}")
if st.sidebar.button("Log Out"):
    logout()

st.sidebar.write("---")
view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Chairman Management Center"])

# Permission Logic
is_chairman = (user_role == "Chairman")
is_rep = (user_role == "Representative")
is_teacher = (user_role == "Teacher")
# Only Chairman and Reps can add data
can_edit = (is_chairman or is_rep) and not is_teacher 

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_project} Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📅 Upcoming Schedule")
        p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
        if p_events:
            for e in p_events:
                with st.expander(f"{e['type']} - {e['date']}", expanded=True):
                    st.write(f"**Time:** {e['start']} to {e['end']}")
                    st.write(f"**Venue:** {e['venue']}")
                    st.caption(f"Note: {e['desc']}")
        else:
            st.info("No events scheduled yet.")

    with col2:
        st.subheader("👥 Team Structure")
        reps = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Representative")]
        mems = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Member")]
        
        st.write(f"**Representatives:** {', '.join(reps['Name'].tolist()) if not reps.empty else 'TBD'}")
        st.write(f"**Members:** {', '.join(mems['Name'].tolist()) if not mems.empty else 'None'}")
        
        st.write("---")
        st.subheader("RSVP")
        all_p_mems = m_df[m_df['Project'] == view_project]['Name'].tolist()
        if all_p_mems:
            name_sel = st.selectbox("Your Name", all_p_mems)
            if st.button("Confirm Attendance"):
                st.success(f"RSVP confirmed for {name_sel}!")
        else:
            st.caption("Awaiting roster from Chairman.")

# --- 2. ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_project} Activity Log")
    
    if can_edit:
        with st.form("activity_form", clear_on_submit=True):
            st.subheader("Add Daily Report")
            date_val = st.date_input("Date")
            type_val = st.selectbox("Type", ["Discussion", "Rehearsal"])
            desc_val = st.text_area("What was achieved?")
            if st.form_submit_button("Post Report"):
                st.session_state.data["logs"].append({"Project": view_project, "Date": str(date_val), "Type": type_val, "Desc": desc_val})
                st.rerun()
    
    st.write("---")
    p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
    for l in reversed(p_logs):
        st.info(f"**{l['Date']} ({l['Type']})**\n\n{l['Desc']}")

# --- 3. CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Contribution")
    
    if can_edit:
        with st.form("time_form", clear_on_submit=True):
            p_mems = m_df[m_df['Project'] == view_project]['Name'].tolist()
            who = st.selectbox("Member", p_mems) if p_mems else "No members"
            c_h = st.number_input("Hours", 0)
            c_m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Submit Hours"):
                st.session_state.data["contributions"].append({"Project": view_project, "Name": who, "Time": f"{c_h}h {c_m}m"})
                st.rerun()

    st.write("---")
    contribs = [c for c in st.session_state.data["contributions"] if c['Project'] == view_project]
    if contribs:
        st.table(pd.DataFrame(contribs))
    else:
        st.info("No data recorded.")

# --- 4. CHAIRMAN MANAGEMENT CENTER ---
elif page == "Chairman Management Center":
    # Visible ONLY to Chairman (Teachers cannot see or access)
    if is_chairman:
        st.title("⚙️ Chairman Control Panel")
        
        t1, t2 = st.tabs(["Member Management", "Event Scheduler"])
        
        with t1:
            with st.form("mem_form", clear_on_submit=True):
                st.subheader("Add Member to Project")
                m_name = st.text_input("Full Name")
                m_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                m_role = st.selectbox("Role", ["Member", "Representative"])
                if st.form_submit_button("Add Member"):
                    new_m = pd.DataFrame([{"Name": m_name, "Project": m_proj, "Role": m_role}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                    st.rerun()
            
            st.subheader("Current Project Roster")
            st.dataframe(st.session_state.data["members"], use_container_width=True)

        with t2:
            with st.form("event_form", clear_on_submit=True):
                st.subheader("Schedule Project Event")
                e_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                e_type = st.radio("Event Type", ["Discussion", "Rehearsal"])
                e_date = st.date_input("Date")
                c1, c2 = st.columns(2)
                e_start = c1.time_input("Start Time")
                e_end = c2.time_input("End Time")
                e_venue = st.text_input("Venue (e.g., Classroom 4A, Hall)")
                e_notes = st.text_input("Description/Notes")
                
                if st.form_submit_button("Schedule Event"):
                    st.session_state.data["events"].append({
                        "project": e_proj, "type": e_type, "date": str(e_date),
                        "start": str(e_start), "end": str(e_end), "venue": e_venue, "desc": e_notes
                    })
                    st.success("Event Added!")
    
    elif is_teacher:
        st.error("Access Denied: The Chairman Management Center is invisible to Teachers.")
    else:
        st.error("Access restricted to Chairman.")
