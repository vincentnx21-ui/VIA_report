import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data.json"

def save_data():
    data = {
        "members": st.session_state.data["members"],
        "logs": st.session_state.data["logs"],
        "contributions": st.session_state.data["contributions"],
        "rsvp": st.session_state.data["rsvp"],
        "events": []
    }
    # Convert dates/times to strings for JSON
    for e in st.session_state.data["events"]:
        e_copy = e.copy()
        e_copy["date"] = str(e["date"])
        e_copy["start_time"] = str(e["start_time"])
        e_copy["end_time"] = str(e["end_time"])
        data["events"].append(e_copy)
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
            # Restore date/time objects
            for e in raw["events"]:
                e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
            return raw
    return None

# --- SESSION INITIALIZATION ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": [], "events": [], "rsvp": []
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- AUTHENTICATION ---
USER_ROLES = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Skit Representative": "skit2026",
    "Brochure Representative": "brochure2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    name_input = st.text_input("Enter Your Name")
    role_input = st.selectbox("Select Role", list(USER_ROLES.keys()))
    pw_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if name_input and pw_input == USER_ROLES[role_input]:
            st.session_state.logged_in = True
            st.session_state.user_name = name_input
            st.session_state.user_role = role_input
            st.rerun()
        else:
            st.error("Invalid Name or Password.")
    st.stop()

# --- GLOBALS ---
u_role = st.session_state.user_role
u_name = st.session_state.user_name
is_chairman = (u_role == "Chairman")
is_teacher = (u_role == "Teacher")
is_skit_rep = (u_role == "Skit Representative")
is_brochure_rep = (u_role == "Brochure Representative")

# --- SIDEBAR ---
st.sidebar.title(f"👤 {u_name}")
st.sidebar.write(f"**Role:** {u_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Activity Log", "Time Tracker"]
if is_chairman:
    nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD (RSVP & ROSTER) ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events")
        events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        if not events:
            st.info("No events scheduled.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            dt_now = datetime.now()
            event_dt = datetime.combine(e["date"], e["start_time"])
            is_past = event_dt < dt_now

            with st.expander(f"{e['type']} - {e['date']} ({e['venue']})"):
                st.write(f"**Time:** {e['start_time']} to {e['end_time']}")
                
                # RSVP Logic for Members, Reps, and Teachers
                can_rsvp = u_role in ["VIA members", "Skit Representative", "Brochure Representative", "Teacher", "VIA Committee"]
                if not is_past and can_rsvp:
                    st.write("---")
                    st.write("**Your RSVP**")
                    with st.form(f"rsvp_{i}"):
                        status = st.radio("Attendance", ["Attending", "Not Attending", "Late"], key=f"stat_{i}")
                        reason = st.text_input("Reason (N/A if Attending)", value="N/A", key=f"res_{i}")
                        if st.form_submit_button("Submit RSVP"):
                            # Filter out existing RSVP from same person for same event
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name'] == u_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({
                                "event_id": e_id, "name": u_name, "status": status, "reason": reason
                            })
                            save_data()
                            st.success("RSVP Saved!")

                # Only Chairman can see responses
                if is_chairman:
                    st.write("---")
                    st.write("**Member Responses**")
                    resps = [r for r in st.session_state.data["rsvp"] if r["event_id"] == e_id]
                    if resps:
                        st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    else:
                        st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Team Roster")
        m_list = [m for m in st.session_state.data["members"] if m["project"] == view_proj]
        if not m_list:
            st.write("No members assigned.")
        else:
            if view_proj == "SKIT":
                for role in ["Actors", "Prop makers", "Cameraman"]:
                    names = [m["name"] for m in m_list if m["sub_role"] == role]
                    if names: st.write(f"**{role}:** {', '.join(names)}")
            else:
                names = [m["name"] for m in m_list]
                st.write(f"**Members:** {', '.join(names)}")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    
    # Chairman and Reps can add logs
    if is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE"):
        with st.form("log_form"):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Category", ["Discussion", "Rehearsal"])
            l_act = st.text_area("What was done today?")
            if st.form_submit_button("Save Entry"):
                st.session_state.data["logs"].append({
                    "project": view_proj, "date": str(l_date), "type": l_type, "activity": l_act
                })
                save_data()
                st.rerun()

    # View Logs (All can see)
    st.write("---")
    for l in reversed(st.session_state.data["logs"]):
        if l["project"] == view_proj:
            with st.chat_message("user"):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])

# --- TIME TRACKER ---
elif page == "Time Tracker":
    st.title(f"⏳ {view_proj} Contribution Tracker")
    
    # Permission: Reps for their project, Chairman for all
    can_track = is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE")
    
    if can_track:
        with st.form("time_form"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Select Member", names) if names else None
            c_h = st.number_input("Hours", 0, 24)
            c_m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Submit Hours") and target:
                st.session_state.data["contributions"].append({
                    "project": view_proj, "name": target, "time": f"{c_h}h {c_m}m", "date": str(datetime.now().date())
                })
                save_data()
                st.rerun()

    st.write("---")
    df_c = pd.DataFrame([c for c in st.session_state.data["contributions"] if c["project"] == view_proj])
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)
    else:
        st.info("No records found.")

# --- MANAGEMENT CENTER (CHAIRMAN ONLY) ---
elif page == "Management Center":
    st.title("👑 Chairman Control Center")
    t1, t2 = st.tabs(["Member Management", "Event Planning"])

    with t1:
        st.subheader("Add / Edit Members")
        with st.form("mem_form", clear_on_submit=True):
            m_name = st.text_input("Full Name")
            m_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_sub = "N/A"
            if m_proj == "SKIT":
                m_sub = st.selectbox("Role", ["Actors", "Prop makers", "Cameraman"])
            if st.form_submit_button("Add Member"):
                st.session_state.data["members"].append({"name": m_name, "project": m_proj, "sub_role": m_sub})
                save_data(); st.rerun()
        
        st.write("---")
        # Display and Edit
        for i, m in enumerate(st.session_state.data["members"]):
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(f"{m['name']} ({m['project']} - {m['sub_role']})")
            if col_b.button("Delete", key=f"del_{i}"):
                st.session_state.data["members"].pop(i)
                save_data(); st.rerun()

    with t2:
        st.subheader("Schedule Project Events")
        with st.form("ev_form"):
            e_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
            e_type = st.selectbox("Event Type", ["Discussion", "Rehearsal"])
            e_date = st.date_input("Pick Date")
            e_s = st.time_input("Start Time", time(14, 0))
            e_e = st.time_input("End Time", time(16, 0))
            e_v = st.text_input("Venue")
            if st.form_submit_button("Create Event"):
                st.session_state.data["events"].append({
                    "project": e_proj, "type": e_type, "date": e_date, 
                    "start_time": e_s, "end_time": e_e, "venue": e_v
                })
                save_data(); st.rerun()

        st.write("---")
        for i, e in enumerate(st.session_state.data["events"]):
            st.write(f"**{e['project']} {e['type']}** on {e['date']} at {e['venue']}")
            if st.button("Cancel Event", key=f"ev_del_{i}"):
                st.session_state.data["events"].pop(i)
                save_data(); st.rerun()
