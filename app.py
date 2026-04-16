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

# --- LOGIN / LOGOUT LOGIC ---
def logout():
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal")
    with st.container(border=True):
        role = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
        pwd = st.text_input("Password", type="password")
        if st.button("Login"):
            if pwd == USER_CREDENTIALS[role]:
                st.session_state.logged_in = True
                st.session_state.user_role = role
                st.rerun()
            else:
                st.error("Invalid password.")
    st.stop() # Stop execution here if not logged in

# --- POST-LOGIN NAVIGATION ---
user_role = st.session_state.user_role
st.sidebar.title(f"👤 {user_role}")
if st.sidebar.button("Log Out"):
    logout()

st.sidebar.write("---")
view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Chairman Management"])

# --- PERMISSIONS ---
# Teacher/Committee can only view. Chairman/Rep can edit.
can_edit = user_role in ["Chairman", "Representative"]
is_chairman = user_role == "Chairman"

# Define shared data pointer
m_df = st.session_state.data["members"]

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_project} Dashboard")
    
    # Show Leaders
    reps = m_df[(m_df['Project'] == view_project) & (m_df['Role'] == "Representative")]
    rep_names = ", ".join(reps['Name'].tolist()) if not reps.empty else "TBD"
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📌 Project Info")
        st.write(f"**Representative(s):** {rep_names}")
        
        st.write("**Next Scheduled Event:**")
        p_events = [e for e in st.session_state.data["events"] if e['project'] == view_project]
        if p_events:
            last_event = p_events[-1]
            st.info(f"**{last_event['type']}**\n\nDate: {last_event['date']}\n\nNote: {last_event['desc']}")
        else:
            st.write("No events scheduled.")

    with c2:
        st.subheader("👥 Project Roster")
        p_m_list = m_df[m_df['Project'] == view_project]['Name'].tolist()
        if p_m_list:
            st.write(", ".join(p_m_list))
        else:
            st.write("No members assigned to this project yet.")

# --- 2. ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_project} Progress Log")
    
    if can_edit:
        with st.expander("➕ Add New Report (Chairman/Rep Only)"):
            with st.form("log_form", clear_on_submit=True):
                l_date = st.date_input("Date")
                l_type = st.selectbox("Category", ["Discussion", "Rehearsal"])
                l_desc = st.text_area("What was achieved?")
                if st.form_submit_button("Post Report"):
                    st.session_state.data["logs"].append({
                        "Project": view_project, "Date": str(l_date), "Type": l_type, "Desc": l_desc
                    })
                    st.rerun()
    else:
        st.caption("Read-only access for Teacher/Committee/Members.")

    st.write("---")
    p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
    if not p_logs:
        st.info("No logs available.")
    for l in reversed(p_logs):
        with st.container(border=True):
            st.write(f"**{l['Date']} | {l['Type']}**")
            st.write(l['Desc'])

# --- 3. CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Time Tracker")
    
    if can_edit:
        with st.expander("➕ Log Hours (Chairman/Rep Only)"):
            p_m_list = m_df[m_df['Project'] == view_project]['Name'].tolist()
            if p_m_list:
                with st.form("time_form", clear_on_submit=True):
                    who = st.selectbox("Member", p_m_list)
                    h = st.number_input("Hours", 0, 10)
                    m = st.number_input("Minutes", 0, 59)
                    if st.form_submit_button("Save"):
                        st.session_state.data["contributions"].append({
                            "Project": view_project, "Name": who, "Time": f"{h}h {m}m"
                        })
                        st.rerun()
            else:
                st.warning("Add members in Management first.")
    
    st.write("---")
    c_list = [c for c in st.session_state.data["contributions"] if c['Project'] == view_project]
    if c_list:
        st.table(pd.DataFrame(c_list))
    else:
        st.write("No data recorded.")

# --- 4. CHAIRMAN MANAGEMENT ---
elif page == "Chairman Management":
    if is_chairman:
        st.title("⚙️ Chairman Management Centre")
        
        tab1, tab2 = st.tabs(["Manage Members", "Schedule Events"])
        
        with tab1:
            st.subheader("Add Member to Project")
            with st.form("add_mem", clear_on_submit=True):
                name = st.text_input("Name")
                proj = st.selectbox("Assign to Project", ["SKIT", "BROCHURE"])
                role_type = st.selectbox("Role", ["Member", "Representative"])
                if st.form_submit_button("Register"):
                    new_row = pd.DataFrame([{"Name": name, "Project": proj, "Role": role_type}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_row], ignore_index=True)
                    st.rerun()
            
            st.write("### Current Roster")
            st.dataframe(st.session_state.data["members"], use_container_width=True)

        with tab2:
            st.subheader("Schedule Meeting/Rehearsal")
            with st.form("event_form", clear_on_submit=True):
                e_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
                e_type = st.radio("Type", ["Discussion", "Rehearsal"])
                e_date = st.date_input("Pick Date")
                e_time = st.time_input("Pick Time")
                e_desc = st.text_input("Location/Notes")
                if st.form_submit_button("Set Event"):
                    st.session_state.data["events"].append({
                        "project": e_proj, "type": e_type, "date": f"{e_date} @ {e_time}", "desc": e_desc
                    })
                    st.success("Event posted to Dashboard.")
    else:
        st.error("🚫 Access Denied. Only the Chairman can access this centre. Teachers and others have View-Only access to Logs and Dashboards.")
