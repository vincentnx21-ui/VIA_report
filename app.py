import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Management", layout="wide")

# Admin Credentials
ADMIN_PASSWORD = "VIA_LEADER_2026" 

# --- INITIALIZE DATABASE ---
if 'data' not in st.session_state:
    st.session_state.data = {
        "members": pd.DataFrame(columns=["Name", "Project", "Role"]),
        "logs": [],
        "contributions": [],
        "schedule": {"SKIT": "None set", "BROCHURE": "None set"}
    }

# --- SIDEBAR AUTHENTICATION ---
st.sidebar.title("🔐 Access Control")
user_role = st.sidebar.selectbox("Login As", ["Member", "Representative", "Chairman"])
access_granted = False

if user_role in ["Representative", "Chairman"]:
    pw = st.sidebar.text_input("Enter Access Password", type="password")
    if pw == ADMIN_PASSWORD:
        access_granted = True
        st.sidebar.success(f"Verified as {user_role}")
    elif pw:
        st.sidebar.error("Incorrect Password")

# --- PROJECT SELECTION ---
st.sidebar.write("---")
view_project = st.sidebar.radio("Select Project View", ["SKIT", "BROCHURE"])

# --- PAGE NAVIGATION ---
page = st.sidebar.radio("Navigation", ["Project Dashboard", "Activity Log", "Contribution Tracker", "Chairman Dashboard"])

# --- 1. PROJECT DASHBOARD (Visible to Everyone) ---
if page == "Project Dashboard":
    st.title(f"📂 Project: {view_project}")
    
    # Display Leaders
    reps = st.session_state.data["members"]
    project_reps = reps[(reps['Project'] == view_project) & (reps['Role'] == "Representative")]
    rep_names = ", ".join(project_reps['Name'].tolist()) if not project_reps.empty else "TBD"
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Project Leadership")
        st.info(f"**Representative(s):** {rep_names}")
        st.write(f"**Next Date:** {st.session_state.data['schedule'][view_project]}")
    
    with col2:
        st.subheader("Project Members")
        m_list = reps[reps['Project'] == view_project]['Name'].tolist()
        if m_list:
            st.write(", ".join(m_list))
        else:
            st.write("No members assigned yet.")

    st.write("---")
    st.subheader("RSVP / Attendance")
    if not reps[reps['Project'] == view_project].empty:
        att_name = st.selectbox("Your Name", reps[reps['Project'] == view_project]['Name'])
        status = st.radio("Attendance for next session:", ["Attending", "Not Attending", "Late"])
        if st.button("Submit RSVP"):
            st.toast(f"Recorded: {att_name} is {status}")
    else:
        st.warning("Chairman needs to add members to this project first.")

# --- 2. ACTIVITY LOG (Locked to Reps/Chairman) ---
elif page == "Activity Log":
    st.title(f"📝 {view_project} Activity Log")
    
    if access_granted:
        with st.form("log_form", clear_on_submit=True):
            st.write("### Add New Entry")
            date = st.date_input("Date")
            type_act = st.selectbox("Activity Type", ["Discussion", "Rehearsal"])
            summary = st.text_area("What was accomplished?")
            if st.form_submit_button("Save Log"):
                st.session_state.data["logs"].append({
                    "Project": view_project, "Date": date, "Type": type_act, "Desc": summary
                })
                st.success("Activity logged!")
    
    st.write("---")
    # Display Logs
    p_logs = [l for l in st.session_state.data["logs"] if l['Project'] == view_project]
    if not p_logs:
        st.info("No logs for this project.")
    else:
        for l in reversed(p_logs):
            st.write(f"**{l['Date']} [{l['Type']}]**")
            st.info(l['Desc'])

# --- 3. CONTRIBUTION TRACKER (Locked to Reps/Chairman) ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_project} Contribution Tracker")
    
    if access_granted:
        with st.form("contrib_form", clear_on_submit=True):
            project_members = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_project]
            target_mem = st.selectbox("Select Member", project_members["Name"]) if not project_members.empty else "None"
            h = st.number_input("Hours", min_value=0)
            m = st.number_input("Minutes", min_value=0, max_value=59)
            if st.form_submit_button("Record Time"):
                st.session_state.data["contributions"].append({
                    "Project": view_project, "Name": target_mem, "Time": f"{h}h {m}m"
                })
                st.success("Contribution recorded.")

    st.write("---")
    c_df = pd.DataFrame([c for c in st.session_state.data["contributions"] if c['Project'] == view_project])
    if not c_df.empty:
        st.table(c_df[["Name", "Time"]])
    else:
        st.write("No contributions recorded yet.")

# --- 4. CHAIRMAN DASHBOARD (Locked to Chairman) ---
elif page == "Chairman Dashboard":
    if user_role == "Chairman" and access_granted:
        st.title("👑 Chairman Management Center")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("Manage Roster")
            with st.form("add_member"):
                new_name = st.text_input("Name")
                new_proj = st.selectbox("Assign to Project", ["SKIT", "BROCHURE"])
                new_role = st.selectbox("Assign Role", ["Member", "Representative"])
                if st.form_submit_button("Add to VIA"):
                    new_row = pd.DataFrame([{"Name": new_name, "Project": new_proj, "Role": new_role}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_row], ignore_index=True)
                    st.rerun()

        with col_b:
            st.subheader("Set Event Dates")
            s_proj = st.selectbox("Project", ["SKIT", "BROCHURE"], key="date_sel")
            s_date = st.text_input("Meeting Date/Time (e.g. Oct 12, 2pm)")
            if st.button("Update Schedule"):
                st.session_state.data["schedule"][s_proj] = s_date
                st.success("Date updated!")

        st.write("---")
        st.subheader("Current Roster")
        st.dataframe(st.session_state.data["members"], use_container_width=True)

    else:
        st.error("Only the Chairman can access this dashboard.")
