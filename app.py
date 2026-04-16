import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Management", layout="wide")

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
            # Strict type checking before formatting
            e_copy["date"] = e["date"].isoformat() if isinstance(e["date"], (date, datetime)) else str(e["date"])
            e_copy["start_time"] = e["start_time"].strftime("%H:%M") if hasattr(e["start_time"], "strftime") else str(e["start_time"])
            e_copy["end_time"] = e["end_time"].strftime("%H:%M") if hasattr(e["end_time"], "strftime") else str(e["end_time"])
            data["events"].append(e_copy)
            
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        st.error(f"Save Error: {e}")

def load_data():
    """Loads JSON and converts strings back to proper Python objects."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                for key in ["members", "logs", "contributions", "rsvp", "events"]:
                    if key not in raw: raw[key] = []
                
                for e in raw["events"]:
                    if isinstance(e["date"], str):
                        e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e["start_time"], str):
                        e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    if isinstance(e["end_time"], str):
                        e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
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
    st.title("🛡️ VIA Project Hub Login")
    name_in = st.text_input("Enter Your Name").strip().title()
    role_in = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
    pw_in = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if name_in and pw_in == USER_PASSWORDS.get(role_in):
            st.session_state.logged_in = True
            st.session_state.u_name = name_in
            st.session_state.u_role = role_in
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.stop()

# --- GLOBALS & SIDEBAR ---
u_name, u_role = st.session_state.u_name, st.session_state.u_role
is_chair = (u_role == "Chairman")
is_teach = (u_role == "Teacher")
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
            dt_now = datetime.now()
            event_dt = datetime.combine(e["date"], e["start_time"])
            is_past = event_dt < dt_now

            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} ({e['venue']})"):
                s_t = e['start_time'].strftime("%H:%M") if hasattr(e['start_time'], 'strftime') else str(e['start_time'])
                e_t = e['end_time'].strftime("%H:%M") if hasattr(e['end_time'], 'strftime') else str(e['end_time'])
                st.write(f"**Duration:** {s_t} to {e_t}")
                
                # Teachers, Members, and Reps can RSVP
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        stat = st.radio("Status", ["Attending", "Not Attending", "Late"], key=f"s{i}")
                        res = st.text_input("Reason (N/A if attending)", value="N/A", key=f"r{i}")
                        if st.form_submit_button("Submit Vote"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == u_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": u_name, "status": stat, "reason": res})
                            save_data(); st.success("Vote recorded!"); st.rerun()

                if is_chair:
                    st.write("---")
                    st.write("**Chairman Data: Member Responses**")
                    rs = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if rs: st.table(pd.DataFrame(rs)[["name", "status", "reason"]])
                    else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Project Roster")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        
        # Display Representatives
        reps = [m["name"] for m in m_list if m.get("is_rep")]
        if reps: st.success(f"**Representatives:** \n{', '.join(reps)}")
        
        st.write("---")
        if view_proj == "SKIT":
            for r in ["Actors", "Prop makers", "Cameraman", "N/A"]:
                ns = [m["name"] for m in m_list if m.get("sub_role") == r and not m.get("is_rep")]
                if ns: st.write(f"**{r}:** {', '.join(ns)}")
        else:
            ns = [m["name"] for m in m_list if not m.get("is_rep")]
            if ns: st.write(f"**Members:** {', '.join(ns)}")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Logs")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("log_f"):
            ld, lt = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"])
            la = st.text_area("What did the class do today?")
            if st.form_submit_button("Save Report"):
                st.session_state.data["logs"].append({"project": view_proj, "date": str(ld), "type": lt, "activity": la})
                save_data(); st.rerun()
    
    st.write("---")
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
            col_h, col_m = st.columns(2)
            h = col_h.number_input("Hours", 0)
            m = col_m.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record Time Contribution") and target:
                st.session_state.data["contributions"].append({"project": view_proj, "name": target, "time": f"{h}h {m}m", "date": str(date.today())})
                save_data(); st.rerun()
    
    df_c = pd.DataFrame([c for c in st.session_state.data.get("contributions", []) if c.get("project") == view_proj])
    if not df_c.empty: st.dataframe(df_c, use_container_width=True)

# --- MANAGEMENT CENTER ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Management Center")
    t1, t2 = st.tabs(["Member & Rep Management", "Schedule Management"])
    
    with t1:
        with st.form("add_m"):
            mn = st.text_input("Name")
            mp = st.selectbox("Assign to Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Is Representative for this project?")
            ms = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp == "SKIT" else "N/A"
            if st.form_submit_button("Save Entry"):
                # Overwrite if same name exists (Account Recovery Logic)
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != mn.lower()]
                st.session_state.data["members"].append({"name": mn, "project": mp, "sub_role": ms, "is_rep": m_rep})
                save_data(); st.rerun()
        
        st.write("---")
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c1, c2 = st.columns([4, 1])
            tag = " 🌟 [REPRESENTATIVE]" if m.get("is_rep") else f" ({m.get('sub_role')})"
            c1.write(f"**{m['name']}** - {m['project']} {tag}")
            if c2.button("Delete", key=f"del{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()

    with t2:
        with st.form("ev_f"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            es, ee, ev = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Create Event") and ev:
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        
        st.write("---")
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c1, c2 = st.columns([4, 1])
            is_p = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            c1.write(f"**{e['type']}** on {e['date']} @ {e['venue']} {'(Passed)' if is_p else ''}")
            if c2.button("Cancel", key=f"ecan{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
