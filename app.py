import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub", layout="wide")

# --- FILE PATHS FOR SAVING ---
# In a real GitHub/Streamlit deployment, these files save to the server's local disk
MEMBERS_FILE = "via_members.csv"

# --- USER PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- DATA INITIALIZATION & LOADING ---
def load_data():
    if os.path.exists(MEMBERS_FILE):
        return pd.read_csv(MEMBERS_FILE)
    return pd.DataFrame(columns=["Name", "Project", "Role", "SubRole"])

if 'data' not in st.session_state:
    st.session_state.data = {
        "members": load_data(),
        "logs": [],
        "contributions": [],
        "events": []
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
    st.rerun()

st.sidebar.write("---")
view_project = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Center"])

# Permissions
u_role = st.session_state.user_role
is_chairman = u_role == "Chairman"
is_rep = u_role == "Representative"
is_teacher = u_role == "Teacher"
can_edit = u_role in ["Chairman", "Representative"]

# --- 1. DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_project} Hub")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Scheduled Events")
        p_events = [e for e in st.session_state.data["events"] if e.get('project') == view_project]
        
        if not p_events:
            st.info(f"No {view_project} events scheduled yet.")
        else:
            for i, e in enumerate(p_events):
                # Combine date and time for comparison
                event_dt = datetime.combine(e['date'], e['start_time'])
                is_past = event_dt < datetime.now()
                
                status = "🔴 PASSED" if is_past else "🟢 UPCOMING"
                with st.expander(f"{e['type']} - {e['date'].strftime('%d %b')} ({status})"):
                    st.write(f"**Time:** {e['start_time'].strftime('%H:%M')} to {e['end_time'].strftime('%H:%M')}")
                    st.write(f"**Venue:** {e['venue']}")
                    st.write(f"**Details:** {e['notes']}")
                    
                    if can_edit and not is_past:
                        if st.button(f"Cancel Event {i}", key=f"del_ev_{i}"):
                            st.session_state.data["events"].pop(i)
                            st.rerun()

    with col2:
        st.subheader("👥 Project Team")
        m_df = st.session_state.data["members"]
        proj_members = m_df[m_df['Project'] == view_project]
        
        if proj_members.empty:
            st.write("No members assigned yet.")
        else:
            # Display Representatives
            reps = proj_members[proj_members['Role'] == "Representative"]
            st.markdown("**Representatives:** " + (", ".join(reps['Name'].tolist()) if not reps.empty else "TBD"))
            
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
            l_desc = st.text_area("What was done?")
            if st.form_submit_button("Submit Report"):
                st.session_state.data["logs"].append({"Project": view_project, "Date": l_date, "Type": l_type, "Desc": l_desc})
                st.success("Log Saved.")
                st.rerun()
    
    logs = [l for l in st.session_state.data["logs"] if l.get('Project') == view_project]
    for l in reversed(logs):
        with st.expander(f"{l['Date']} - {l['Type']}"):
            st.write(l['Desc'])

# --- 3. CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Contribution Tracker")
    
    if can_edit:
        with st.form("time_form", clear_on_submit=True):
            m_df = st.session_state.data["members"]
            p_names = m_df[m_df['Project'] == view_project]['Name'].tolist()
            if p_names:
                who = st.selectbox("Select Member", p_names)
                h = st.number_input("Hours", min_value=0, step=1)
                m = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                if st.form_submit_button("Log Time"):
                    st.session_state.data["contributions"].append({"Project": view_project, "Name": who, "Time": f"{h}h {m}m"})
                    st.rerun()
            else:
                st.warning("No members found for this project.")
                st.form_submit_button("Disabled", disabled=True)

    c_list = [c for c in st.session_state.data["contributions"] if c.get('Project') == view_project]
    if c_list:
        st.table(pd.DataFrame(c_list))

# --- 4. MANAGEMENT CENTER ---
elif page == "Management Center":
    if is_chairman:
        st.title("👑 Chairman Management Center")
        tab1, tab2 = st.tabs(["Add Members", "Schedule Event"])
        
        with tab1:
            with st.form("mem_form", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                new_n = c1.text_input("Member Name")
                new_p = c2.selectbox("Project", ["SKIT", "BROCHURE"])
                new_r = c3.selectbox("Role", ["Member", "Representative"])
                new_sub = "N/A"
                if new_p == "SKIT":
                    new_sub = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman"])
                
                if st.form_submit_button("Save Member"):
                    if new_n:
                        new_row = pd.DataFrame([{"Name": new_n, "Project": new_p, "Role": new_r, "SubRole": new_sub}])
                        st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_row], ignore_index=True)
                        # SAVE TO CSV
                        st.session_state.data["members"].to_csv(MEMBERS_FILE, index=False)
                        st.success(f"Saved {new_n} permanently.")
                        st.rerun()

            st.write("### Current Roster")
            st.dataframe(st.session_state.data["members"], use_container_width=True)

        with tab2:
            with st.form("event_form", clear_on_submit=True):
                e_p = st.selectbox("Project", ["SKIT", "BROCHURE"])
                e_t = st.radio("Type", ["Discussion", "Rehearsal"])
                e_d = st.date_input("Date")
                col_t1, col_t2 = st.columns(2)
                e_s = col_t1.time_input("Start")
                e_e = col_t2.time_input("End")
                e_v = st.text_input("Venue")
                e_notes = st.text_input("Notes")
                if st.form_submit_button("Schedule"):
                    st.session_state.data["events"].append({
                        "project": e_p, "type": e_t, "date": e_d, 
                        "start_time": e_s, "end_time": e_e, "venue": e_v, "notes": e_notes
                    })
                    st.success("Event added!")
    else:
        st.error("Access Denied: Teachers and other roles cannot access the Management Center.")
