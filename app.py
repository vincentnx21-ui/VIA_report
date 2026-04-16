import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Portal", layout="wide")

# --- DATA PERSISTENCE HELPERS ---
DATA_FILE = "via_data.json"

def save_data():
    """Saves the current session state data to a JSON file."""
    data_to_save = {
        "members": st.session_state.data["members"].to_dict(orient="records"),
        "logs": st.session_state.data["logs"],
        "contributions": st.session_state.data["contributions"],
        "rsvp": st.session_state.data["rsvp"],
        "events": []
    }
    # Special handling for dates and times in events
    for e in st.session_state.data["events"]:
        event_copy = e.copy()
        event_copy["date"] = e["date"].isoformat()
        event_copy["start_time"] = e["start_time"].strftime("%H:%M:%S")
        event_copy["end_time"] = e["end_time"].strftime("%H:%M:%S")
        data_to_save["events"].append(event_copy)
        
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f)

def load_data():
    """Loads data from the JSON file and restores types."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                # Convert list of dicts back to DataFrame
                raw["members"] = pd.DataFrame(raw["members"])
                # Convert strings back to date/time objects
                for e in raw["events"]:
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
                return raw
        except Exception as e:
            st.error(f"Error loading saved data: {e}")
            return None
    return None

# --- INITIALIZE SESSION STATE ---
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
            "rsvp": []
        }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Representative": "rep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- LOGIN SCREEN ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    role_choice = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pw_choice = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw_choice == USER_CREDENTIALS[role_choice]:
            st.session_state.logged_in = True
            st.session_state.user_role = role_choice
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- GLOBAL VARIABLES & LOGOUT ---
u_role = st.session_state.user_role
is_chairman = (u_role == "Chairman")
is_rep = (u_role == "Representative")
is_teacher = (u_role == "Teacher")
can_edit = u_role in ["Chairman", "Representative"]

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Center"])

# --- DASHBOARD PAGE ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Events & Attendance")
        # Filter project events
        p_events = [e for e in st.session_state.data["events"] if e['project'] == view_proj]
        
        if not p_events:
            st.info("No events scheduled yet.")
        else:
            for i, e in enumerate(p_events):
                # Unique Key for RSVP logic
                event_key = f"{view_proj}_{e['date']}_{e['start_time']}"
                event_dt = datetime.combine(e['date'], e['start_time'])
                is_past = event_dt < datetime.now()
                
                with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} ({e['venue']})"):
                    st.write(f"**Time:** {e['start_time'].strftime('%H:%M')} - {e['end_time'].strftime('%H:%M')}")
                    
                    # RSVP FORM (Hidden if event passed)
                    if not is_past:
                        st.write("**Submit RSVP:**")
                        with st.form(key=f"rsvp_form_{i}"):
                            m_names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
                            res_name = st.selectbox("Your Name", m_names) if not m_names.empty else None
                            res_status = st.radio("Status", ["Attending", "Not Attending", "Late"])
                            res_reason = st.text_input("Reason (if not N/A)")
                            if st.form_submit_button("Submit"):
                                if res_name:
                                    # Update or Add RSVP
                                    new_rsvp = {"event_id": event_key, "name": res_name, "status": res_status, "reason": res_reason}
                                    st.session_state.data["rsvp"].append(new_rsvp)
                                    save_data()
                                    st.success("RSVP Submitted!")
                                    st.rerun()

                    # VIEW RSVPs (Visible to Chairman/Rep/Teacher)
                    if u_role in ["Chairman", "Representative", "Teacher"]:
                        st.write("**Member Responses:**")
                        responses = [r for r in st.session_state.data["rsvp"] if r["event_id"] == event_key]
                        if responses:
                            st.table(pd.DataFrame(responses)[["name", "status", "reason"]])
                        else:
                            st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Project Roster")
        proj_m = st.session_state.data["members"][st.session_state.data["members"]['Project'] == view_proj]
        if view_proj == "SKIT":
            for sr in ["Actors", "Prop makers", "Cameraman"]:
                sr_list = proj_m[proj_m['SubRole'] == sr]['Name'].tolist()
                if sr_list: st.write(f"**{sr}:** {', '.join(sr_list)}")
        else:
            m_list = proj_m['Name'].tolist()
            if m_list: st.write(f"**Members:** {', '.join(m_list)}")

# --- ACTIVITY LOG PAGE ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Logs")
    if can_edit:
        with st.form("log_entry"):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("What did you do?")
            if st.form_submit_button("Save Log"):
                st.session_state.data["logs"].append({"Project": view_proj, "Date": str(l_date), "Type": l_type, "Desc": l_desc})
                save_data()
                st.rerun()
    
    logs = [l for l in st.session_state.data["logs"] if l["Project"] == view_proj]
    for l in reversed(logs):
        with st.expander(f"{l['Date']} - {l['Type']}"):
            st.write(l["Desc"])

# --- CONTRIBUTION TRACKER PAGE ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    if can_edit:
        with st.form("time_entry"):
            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
            target = st.selectbox("Member", names) if not names.empty else None
            h = st.number_input("Hours", 0)
            m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record Time") and target:
                st.session_state.data["contributions"].append({"Project": view_proj, "Name": target, "Time": f"{h}h {m}m"})
                save_data()
                st.rerun()
    
    c_list = [c for c in st.session_state.data["contributions"] if c["Project"] == view_proj]
    if c_list: st.table(pd.DataFrame(c_list))

# --- MANAGEMENT CENTER ---
elif page == "Management Center":
    if is_chairman:
        st.title("👑 Management")
        t1, t2 = st.tabs(["Roster", "Schedule"])
        
        with t1:
            with st.form("add_member_form"):
                n = st.text_input("Name")
                p = st.selectbox("Project", ["SKIT", "BROCHURE"])
                r = st.selectbox("Role", ["Member", "Representative"])
                sr = st.selectbox("Sub-Role (SKIT)", ["Actors", "Prop makers", "Cameraman", "N/A"]) if p=="SKIT" else "N/A"
                if st.form_submit_button("Add Member"):
                    new_m = pd.DataFrame([{"Name": n, "Project": p, "Role": r, "SubRole": sr}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                    save_data()
                    st.rerun()
            st.dataframe(st.session_state.data["members"], use_container_width=True)

        with t2:
            with st.form("event_scheduler"):
                ep = st.selectbox("Project", ["SKIT", "BROCHURE"])
                et = st.radio("Type", ["Discussion", "Rehearsal"])
                ed = st.date_input("Date")
                col1, col2 = st.columns(2)
                ts = col1.time_input("Start")
                te = col2.time_input("End")
                ev = st.text_input("Venue")
                if st.form_submit_button("Add Event"):
                    if ev:
                        st.session_state.data["events"].append({
                            "project": ep, "type": et, "date": ed, 
                            "start_time": ts, "end_time": te, "venue": ev
                        })
                        save_data()
                        st.success("Event added!")
                        st.rerun()
                    else:
                        st.error("Please enter a Venue.")
    else:
        st.error("Access restricted to Chairman.")
