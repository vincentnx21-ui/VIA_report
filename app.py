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
    try:
        data = {
            "members": st.session_state.data.get("members", []),
            "logs": st.session_state.data.get("logs", []),
            "contributions": st.session_state.data.get("contributions", []),
            "rsvp": st.session_state.data.get("rsvp", []),
            "events": []
        }
        for e in st.session_state.data.get("events", []):
            e_copy = e.copy()
            e_copy["date"] = str(e["date"]) if hasattr(e["date"], "isoformat") else e["date"]
            e_copy["start_time"] = e["start_time"].strftime("%H:%M") if hasattr(e["start_time"], "strftime") else str(e["start_time"])
            e_copy["end_time"] = e["end_time"].strftime("%H:%M") if hasattr(e["end_time"], "strftime") else str(e["end_time"])
            data["events"].append(e_copy)
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Save Error: {e}")

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                for key in ["members", "logs", "contributions", "rsvp", "events"]:
                    if key not in raw: raw[key] = []
                for e in raw["events"]:
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                return raw
        except: return None
    return None

# --- INITIALIZE STATE ---
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
    st.title("🔐 VIA Class Report Login")
    name_input = st.text_input("Enter Your Name").strip().title()
    role_input = st.selectbox("Select Role", list(USER_ROLES.keys()))
    pw_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if name_input and pw_input == USER_ROLES.get(role_input):
            st.session_state.logged_in = True
            st.session_state.u_name = name_input
            st.session_state.u_role = role_input
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# --- GLOBALS & LOGOUT ---
u_name, u_role = st.session_state.u_name, st.session_state.u_role
is_chairman = (u_role == "Chairman")
is_teacher = (u_role == "Teacher")
is_skit_rep = (u_role == "Skit Representative")
is_broch_rep = (u_role == "Brochure Representative")

st.sidebar.title(f"👤 {u_name}")
st.sidebar.write(f"Role: {u_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Activity Log", "Contribution Tracker"]
if is_chairman: nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events")
        events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        if not events: st.info("No events scheduled.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()

            with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} ({e['venue']})"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                
                # Teacher, Member, and Rep RSVP
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        status = st.radio("Status", ["Attending", "Not Attending", "Late"])
                        reason = st.text_input("Reason (N/A if Attending)", value="N/A")
                        if st.form_submit_button("Submit Vote"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == u_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": u_name, "status": status, "reason": reason})
                            save_data(); st.success("Vote recorded!"); st.rerun()

                if is_chairman:
                    st.write("**Chairman's View: Member Responses**")
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Team")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        if view_proj == "SKIT":
            for r in ["Actors", "Prop makers", "Cameraman"]:
                names = [m["name"] for m in m_list if m.get("sub_role") == r]
                if names: st.write(f"**{r}:** {', '.join(names)}")
        else:
            names = [m["name"] for m in m_list]
            if names: st.write(f"**Members:** {', '.join(names)}")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    if is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("log_f"):
            l_d, l_t = st.date_input("Date"), st.selectbox("Category", ["Discussion", "Rehearsal"])
            l_a = st.text_area("Work Summary")
            if st.form_submit_button("Add Log"):
                st.session_state.data["logs"].append({"project": view_proj, "date": str(l_d), "type": l_t, "activity": l_a})
                save_data(); st.rerun()
    for l in reversed(st.session_state.data.get("logs", [])):
        if l.get("project") == view_proj:
            with st.chat_message("user"):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])

# --- TIME TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    can_track = is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
    if can_track:
        with st.form("time_f"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record Time") and target:
                st.session_state.data["contributions"].append({"project": view_proj, "name": target, "time": f"{h}h {m}m", "date": str(datetime.now().date())})
                save_data(); st.rerun()
    df_c = pd.DataFrame([c for c in st.session_state.data.get("contributions", []) if c.get("project") == view_proj])
    if not df_c.empty: st.dataframe(df_c, use_container_width=True)

# --- MANAGEMENT CENTER (CHAIRMAN ONLY) ---
elif page == "Management Center" and is_chairman:
    st.title("👑 Chairman Management Center")
    t1, t2 = st.tabs(["Member Roster", "Event Scheduler"])
    
    with t1:
        with st.form("add_m"):
            col_n, col_p = st.columns(2)
            m_n = col_n.text_input("Name")
            m_p = col_p.selectbox("Project", ["SKIT", "BROCHURE"])
            m_s = st.selectbox("Role (SKIT)", ["Actors", "Prop makers", "Cameraman"]) if m_p == "SKIT" else "N/A"
            if st.form_submit_button("Add/Update Member") and m_n:
                # Update logic: If name exists, delete old one first
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != m_n.lower()]
                st.session_state.data["members"].append({"name": m_n, "project": m_p, "sub_role": m_s})
                save_data(); st.rerun()
        
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c_name, c_del = st.columns([4, 1])
            c_name.write(f"{m['name']} ({m['project']})")
            if c_del.button("Delete", key=f"del_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()

    with t2:
        with st.form("ev_f"):
            e_p = st.selectbox("Project", ["SKIT", "BROCHURE"])
            e_t = st.selectbox("Type", ["Discussion", "Rehearsal"])
            e_d = st.date_input("Date")
            e_s, e_e = st.time_input("Start"), st.time_input("End")
            e_v = st.text_input("Venue")
            if st.form_submit_button("Schedule Event") and e_v:
                st.session_state.data["events"].append({"project": e_p, "type": e_t, "date": e_d, "start_time": e_s, "end_time": e_e, "venue": e_v})
                save_data(); st.rerun()
        
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c_ev, c_can = st.columns([4, 1])
            c_ev.write(f"{e['type']} - {e['date']} @ {e['venue']}")
            if c_can.button("Cancel Event", key=f"ecan_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
