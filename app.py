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
    """Safely saves session data to JSON."""
    try:
        data = {
            "members": st.session_state.data.get("members", []),
            "logs": st.session_state.data.get("logs", []),
            "contributions": st.session_state.data.get("contributions", []),
            "rsvp": st.session_state.data.get("rsvp", []),
            "events": []
        }
        # Convert date/time objects to strings safely
        for e in st.session_state.data.get("events", []):
            e_copy = e.copy()
            # Ensure we only call strftime on actual date/time objects
            e_copy["date"] = str(e["date"]) if hasattr(e["date"], "isoformat") else e["date"]
            e_copy["start_time"] = e["start_time"].strftime("%H:%M:%S") if hasattr(e["start_time"], "strftime") else str(e["start_time"])
            e_copy["end_time"] = e["end_time"].strftime("%H:%M:%S") if hasattr(e["end_time"], "strftime") else str(e["end_time"])
            data["events"].append(e_copy)
        
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Save Error: {e}")

def load_data():
    """Loads JSON data and reconstructs objects safely."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                # Reconstruct date/time objects
                for e in raw.get("events", []):
                    if isinstance(e["date"], str):
                        e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e["start_time"], str):
                        e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                    if isinstance(e["end_time"], str):
                        e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
                return raw
        except Exception:
            return None
    return None

# --- INITIALIZE SESSION STATE ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": [], "events": [], "rsvp": []
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- AUTHENTICATION ---
USER_ROLES = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    name_input = st.text_input("Enter Your Name")
    role_input = st.selectbox("Select Role", list(USER_ROLES.keys()))
    pw_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if name_input.strip() != "" and pw_input == USER_ROLES.get(role_input):
            st.session_state.logged_in = True
            st.session_state.user_name = name_input
            st.session_state.user_role = role_input
            st.rerun()
        else:
            st.error("Please enter your name and the correct password.")
    st.stop()

# --- GLOBALS & LOGOUT ---
u_role = st.session_state.user_role
u_name = st.session_state.user_name
is_chairman = (u_role == "Chairman")
is_skit_rep = (u_role == "Skit Representative")
is_brochure_rep = (u_role == "Brochure Representative")

st.sidebar.title(f"👤 {u_name}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Activity Log", "Time Tracker"]
if is_chairman: nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events")
        events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        if not events:
            st.info("No events scheduled.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()

            with st.expander(f"{e['type']} - {e['date']} ({e['venue']})"):
                # Use .strftime safely
                st.write(f"**Time:** {e['start_time'].strftime('%H:%M')} to {e['end_time'].strftime('%H:%M')}")
                
                if not is_past and u_role != "Classmates":
                    st.write("---")
                    with st.form(f"rsvp_{i}"):
                        status = st.radio("Attendance", ["Attending", "Not Attending", "Late"])
                        reason = st.text_input("Reason (N/A if Attending)", value="N/A")
                        if st.form_submit_button("Submit RSVP"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == u_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": u_name, "status": status, "reason": reason})
                            save_data(); st.success("RSVP Saved!")

                if is_chairman:
                    st.write("---")
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Team")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        if view_proj == "SKIT":
            for role in ["Actors", "Prop makers", "Cameraman"]:
                names = [m["name"] for m in m_list if m.get("sub_role") == role]
                if names: st.write(f"**{role}:** {', '.join(names)}")
        else:
            names = [m["name"] for m in m_list]
            if names: st.write(f"**Members:** {', '.join(names)}")

# --- LOGS ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    if is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE"):
        with st.form("log_form"):
            l_date, l_type = st.date_input("Date"), st.selectbox("Category", ["Discussion", "Rehearsal"])
            l_act = st.text_area("What was done today?")
            if st.form_submit_button("Save Entry"):
                st.session_state.data["logs"].append({"project": view_proj, "date": str(l_date), "type": l_type, "activity": l_act})
                save_data(); st.rerun()

    st.write("---")
    for l in reversed(st.session_state.data.get("logs", [])):
        if l.get("project") == view_proj:
            with st.chat_message("user"):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])

# --- TIME TRACKER ---
elif page == "Time Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    can_track = is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE")
    if can_track:
        with st.form("time_form"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Submit") and target:
                st.session_state.data["contributions"].append({"project": view_proj, "name": target, "time": f"{h}h {m}m", "date": str(datetime.now().date())})
                save_data(); st.rerun()
    df_c = pd.DataFrame([c for c in st.session_state.data.get("contributions", []) if c.get("project") == view_proj])
    if not df_c.empty: st.dataframe(df_c, use_container_width=True)

# --- MANAGEMENT ---
elif page == "Management Center" and is_chairman:
    st.title("👑 Chairman Control")
    t1, t2 = st.tabs(["Members", "Events"])
    with t1:
        with st.form("mem_form", clear_on_submit=True):
            m_n, m_p = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_s = st.selectbox("Role", ["Actors", "Prop makers", "Cameraman"]) if m_p=="SKIT" else "N/A"
            if st.form_submit_button("Add Member") and m_n:
                st.session_state.data["members"].append({"name": m_n, "project": m_p, "sub_role": m_s})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{m['name']} - {m['project']}")
            if c2.button("Delete", key=f"del_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("ev_form"):
            e_p, e_t, e_d = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            e_s, e_e, e_v = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Create Event") and e_v:
                st.session_state.data["events"].append({"project": e_p, "type": e_t, "date": e_d, "start_time": e_s, "end_time": e_e, "venue": e_v})
                save_data(); st.rerun()
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{e['type']} - {e['date']}")
            if c2.button("Cancel", key=f"ev_del_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
