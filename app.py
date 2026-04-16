import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Portal 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data.json"

def save_data():
    """Safely converts objects to strings and saves to JSON."""
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
            # Ensure types are strings for JSON storage
            e_copy["date"] = e["date"].isoformat() if isinstance(e["date"], (date, datetime)) else str(e["date"])
            e_copy["start_time"] = e["start_time"].strftime("%H:%M") if hasattr(e["start_time"], "strftime") else str(e["start_time"])
            e_copy["end_time"] = e["end_time"].strftime("%H:%M") if hasattr(e["end_time"], "strftime") else str(e["end_time"])
            data["events"].append(e_copy)
            
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        st.error(f"Save Error: {e}")

def load_data():
    """Loads JSON and converts strings back to proper Python objects."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                # Ensure all keys exist
                for key in ["members", "logs", "contributions", "rsvp", "events"]:
                    if key not in raw: raw[key] = []
                
                # Convert strings back to date/time objects to avoid AttributeError
                for e in raw["events"]:
                    if isinstance(e["date"], str):
                        e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e["start_time"], str):
                        # Handle cases where time might be stored as HH:MMS:SS or HH:MM
                        try:
                            e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                        except:
                            e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                    if isinstance(e["end_time"], str):
                        try:
                            e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                        except:
                            e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
                return raw
        except:
            return None
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
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🔐 VIA Class Portal Login")
    u_name_in = st.text_input("Enter Your Name").strip().title()
    u_role_in = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
    u_pw_in = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_name_in and u_pw_in == USER_PASSWORDS.get(u_role_in):
            st.session_state.logged_in = True
            st.session_state.u_name = u_name_in
            st.session_state.u_role = u_role_in
            st.rerun()
        else:
            st.error("Incorrect name or password.")
    st.stop()

# --- GLOBALS & SIDEBAR ---
u_name, u_role = st.session_state.u_name, st.session_state.u_role
is_chair = (u_role == "Chairman")
is_skit_rep = (u_role == "Skit Representative")
is_broch_rep = (u_role == "Brochure Representative")

st.sidebar.title(f"👤 {u_name}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Activity Log", "Contribution Tracker"]
if is_chair: nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events & Attendance")
        evs = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        if not evs: st.info("No events scheduled.")
        
        for i, e in enumerate(evs):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            # Combine safely for past check
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()

            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                s_fmt = e['start_time'].strftime("%H:%M") if hasattr(e['start_time'], 'strftime') else str(e['start_time'])
                e_fmt = e['end_time'].strftime("%H:%M") if hasattr(e['end_time'], 'strftime') else str(e['end_time'])
                st.write(f"**Duration:** {s_fmt} to {e_fmt}")
                
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        stat = st.radio("Attendance", ["Attending", "Not Attending", "Late"], key=f"s{i}")
                        res = st.text_input("Reason (N/A if attending)", value="N/A", key=f"r{i}")
                        if st.form_submit_button("Submit Vote"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == u_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": u_name, "status": stat, "reason": res})
                            save_data(); st.success("Vote recorded!"); st.rerun()

                if is_chair:
                    st.write("---")
                    st.write("**Chairman RSVP Report:**")
                    r_list = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if r_list: st.table(pd.DataFrame(r_list)[["name", "status", "reason"]])
                    else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Member Roster")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        for m in m_list:
            prefix = "⭐ Representative | " if m.get("is_rep") else ""
            st.write(f"**{m['name']}**")
            st.caption(f"{prefix}Role: {m.get('sub_role')}")
            st.write("---")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Logs")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("log_f"):
            ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("Entry")
            if st.form_submit_button("Save Log"):
                st.session_state.data["logs"].append({"project": view_proj, "date": str(ld), "type": lt, "activity": la})
                save_data(); st.rerun()
    
    for l in reversed(st.session_state.data.get("logs", [])):
        if l.get("project") == view_proj:
            with st.chat_message("user"):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    can_track = is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
    if can_track:
        with st.form("time_f"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Select Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Log Contribution") and target:
                st.session_state.data["contributions"].append({"project": view_proj, "name": target, "time": f"{h}h {m}m", "date": str(date.today())})
                save_data(); st.rerun()
    
    df_c = pd.DataFrame([c for c in st.session_state.data.get("contributions", []) if c.get("project") == view_proj])
    if not df_c.empty: st.dataframe(df_c, use_container_width=True)

# --- MANAGEMENT CENTER ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Control")
    t1, t2 = st.tabs(["Manage Members", "Manage Events"])
    
    with t1:
        with st.form("add_m"):
            mn, mp = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Set as Representative?")
            ms = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp == "SKIT" else "N/A"
            if st.form_submit_button("Add/Update Member") and mn:
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != mn.lower()]
                st.session_state.data["members"].append({"name": mn, "project": mp, "sub_role": ms, "is_rep": m_rep})
                save_data(); st.rerun()
        
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{m['name']}** {'[REP]' if m.get('is_rep') else ''} - {m['project']} ({m['sub_role']})")
            if c2.button("Delete", key=f"del{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()

    with t2:
        with st.form("ev_f"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            es, ee, ev = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Schedule Event") and ev:
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{e['type']}** - {e['date']} @ {e['venue']}")
            if c2.button("Cancel Event", key=f"ecan{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
