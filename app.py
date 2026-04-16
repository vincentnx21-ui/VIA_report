import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Portal", layout="wide")

# --- FILE PATH FOR SAVING DATA ---
DATA_FILE = "via_data.json"

def save_data():
    # Convert dataframes to dict for JSON compatibility
    serializable_data = st.session_state.data.copy()
    serializable_data["members"] = st.session_state.data["members"].to_dict()
    # Handle dates/times in events
    serializable_data["events"] = [
        {**e, "date": str(e["date"]), "start_time": str(e["start_time"]), "end_time": str(e["end_time"])} 
        for e in st.session_state.data["events"]
    ]
    with open(DATA_FILE, "w") as f:
        json.dump(serializable_data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            loaded = json.load(f)
            loaded["members"] = pd.DataFrame.from_dict(loaded["members"])
            # Convert strings back to dates/times
            for e in loaded["events"]:
                e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
            return loaded
    return None

# --- INITIALIZE DATA ---
if 'data' not in st.session_state:
    saved = load_data()
    if saved:
        st.session_state.data = saved
    else:
        st.session_state.data = {
            "members": pd.DataFrame(columns=["Name", "Project", "Role", "SubRole"]),
            "logs": [],
            "contributions": [],
            "events": [],
            "rsvp": [] # {event_id, name, status, reason}
        }

# --- PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    role = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == USER_CREDENTIALS[role]:
            st.session_state.logged_in = True
            st.session_state.user_role = role
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- SIDEBAR & GLOBAL VARS ---
u_role = st.session_state.user_role
is_chairman = u_role == "Chairman"
is_rep = u_role == "Representative"
is_teacher = u_role == "Teacher"
can_edit = u_role in ["Chairman", "Representative"]

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Center"])

# --- PAGE 1: DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Scheduled Events & RSVP")
        events = [e for e in st.session_state.data["events"] if e['project'] == view_proj]
        
        if not events:
            st.info("No events scheduled.")
        else:
            for idx, e in enumerate(events):
                event_dt = datetime.combine(e['date'], e['start_time'])
                is_past = event_dt < datetime.now()
                status_color = "🔴" if is_past else "🟢"
                
                with st.expander(f"{status_color} {e['type']} - {e['date']} ({e['venue']})"):
                    st.write(f"**Time:** {e['start_time']} - {e['end_time']}")
                    
                    # RSVP Section for Members
                    if not is_past:
                        st.write("---")
                        with st.form(f"rsvp_{idx}"):
                            r_name = st.selectbox("Your Name", st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"])
                            r_status = st.radio("Attendance", ["Attending", "Not Attending", "Late"])
                            r_reason = st.text_input("Reason (Put N/A if Attending)")
                            if st.form_submit_button("Submit RSVP"):
                                st.session_state.data["rsvp"].append({
                                    "event_id": f"{view_proj}_{e['date']}", "name": r_name, 
                                    "status": r_status, "reason": r_reason
                                })
                                save_data()
                                st.success("RSVP Saved!")
                    
                    # View RSVPs (Chairman/Reps/Teacher)
                    if u_role in ["Chairman", "Representative", "Teacher"]:
                        st.write("**Responses:**")
                        resp_df = pd.DataFrame([r for r in st.session_state.data["rsvp"] if r["event_id"] == f"{view_proj}_{e['date']}"])
                        if not resp_df.empty:
                            st.dataframe(resp_df[["name", "status", "reason"]], use_container_width=True)

    with col2:
        st.subheader("👥 Team")
        m_df = st.session_state.data["members"]
        proj_m = m_df[m_df['Project'] == view_proj]
        
        if view_proj == "SKIT":
            for role_name in ["Actors", "Prop makers", "Cameraman"]:
                names = proj_m[proj_m['SubRole'] == role_name]['Name'].tolist()
                if names: st.write(f"**{role_name}:** {', '.join(names)}")
        else:
            names = proj_m['Name'].tolist()
            if names: st.write(f"**Members:** {', '.join(names)}")

# --- PAGE 2: ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Progress")
    if can_edit:
        with st.form("log_f"):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("What was done?")
            if st.form_submit_button("Add Log"):
                st.session_state.data["logs"].append({"Project": view_proj, "Date": str(l_date), "Type": l_type, "Desc": l_desc})
                save_data()
                st.rerun()
    
    for l in reversed([l for l in st.session_state.data["logs"] if l["Project"] == view_proj]):
        with st.expander(f"{l['Date']} - {l['Type']}"):
            st.write(l["Desc"])

# --- PAGE 3: CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Contribution Tracker")
    if can_edit:
        with st.form("time_f"):
            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
            who = st.selectbox("Member", names) if not names.empty else None
            h = st.number_input("Hours", 0)
            m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record Time") and who:
                st.session_state.data["contributions"].append({"Project": view_proj, "Name": who, "Time": f"{h}h {m}m"})
                save_data()
                st.rerun()
    
    contribs = [c for c in st.session_state.data["contributions"] if c["Project"] == view_proj]
    if contribs: st.table(pd.DataFrame(contribs))

# --- PAGE 4: MANAGEMENT CENTER ---
elif page == "Management Center":
    if is_chairman:
        st.title("👑 Chairman Management Center")
        t1, t2 = st.tabs(["Roster", "Schedule"])
        
        with t1:
            with st.form("mem_f"):
                n = st.text_input("Name")
                p = st.selectbox("Project", ["SKIT", "BROCHURE"])
                r = st.selectbox("Role", ["Representative", "Member"])
                sr = "N/A"
                if p == "SKIT":
                    sr = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman"])
                if st.form_submit_button("Add Member"):
                    new_m = pd.DataFrame([{"Name": n, "Project": p, "Role": r, "SubRole": sr}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                    save_data()
                    st.rerun()
            st.dataframe(st.session_state.data["members"])

        with t2:
            with st.form("ev_f"):
                ep = st.selectbox("Project", ["SKIT", "BROCHURE"])
                et = st.radio("Type", ["Discussion", "Rehearsal"])
                ed = st.date_input("Date")
                ts = st.time_input("Start")
                te = st.time_input("End")
                ev = st.text_input("Venue")
                if st.form_submit_button("Schedule"):
                    st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": ts, "end_time": te, "venue": ev})
                    save_data()
                    st.rerun()
    else:
        st.error("Restricted to Chairman.")
