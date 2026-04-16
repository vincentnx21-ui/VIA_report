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
            e_copy["date"] = e["date"].isoformat() if isinstance(e["date"], (date, datetime)) else str(e["date"])
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
                    if isinstance(e["date"], str): e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e["start_time"], str): e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    if isinstance(e["end_time"], str): e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
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
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🔐 VIA Class Report Portal")
    u_name = st.text_input("Full Name").strip().title()
    u_role = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
    u_pw = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_name and u_pw == USER_PASSWORDS.get(u_role):
            st.session_state.logged_in = True
            st.session_state.curr_user = u_name
            st.session_state.curr_role = u_role
            st.rerun()
        else: st.error("Incorrect name or password.")
    st.stop()

# --- GLOBALS & SIDEBAR ---
curr_name = st.session_state.curr_user
curr_role = st.session_state.curr_role
is_chairman = (curr_role == "Chairman")
is_teacher = (curr_role == "Teacher")
is_skit_rep = (curr_role == "Skit Representative")
is_brochure_rep = (curr_role == "Brochure Representative")

st.sidebar.title(f"👤 {curr_name}")
st.sidebar.caption(f"Role: {curr_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Switch Project View", ["SKIT", "BROCHURE"])
nav_options = ["Dashboard", "Activity Log", "Contribution Tracker"]
if is_chairman: nav_options.append("Management Center")
page = st.sidebar.radio("Navigation", nav_options)

# --- DASHBOARD (RSVP & ROSTER) ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Project Hub")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Schedule & RSVP")
        proj_events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        
        if not proj_events: st.info("No events scheduled for this project.")
        
        for i, e in enumerate(proj_events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            
            with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} ({e['venue']})"):
                st.write(f"**Time:** {e['start_time']} to {e['end_time']}")
                
                # Teachers, Members, and Reps can Vote
                if not is_past:
                    with st.form(f"vote_{i}"):
                        status = st.radio("Will you attend?", ["Attending", "Not Attending", "Late"])
                        reason = st.text_input("Reason (N/A if Attending)", value="N/A")
                        if st.form_submit_button("Submit Vote"):
                            # Update existing vote or add new
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == curr_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": curr_name, "status": status, "reason": reason})
                            save_data(); st.success("Vote Recorded!"); st.rerun()

                if is_chairman:
                    st.write("**Chairman Data: Member Responses**")
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Project Team")
        team = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        
        # Display Representatives
        reps = [m["name"] for m in team if m.get("is_rep")]
        if reps: st.write(f"**Project Representatives:** \n{', '.join(reps)}")
        
        st.write("---")
        if view_proj == "SKIT":
            for cat in ["Actors", "Prop makers", "Cameraman", "N/A"]:
                m_names = [m["name"] for m in team if m.get("sub_role") == cat and not m.get("is_rep")]
                if m_names: st.write(f"**{cat}:** {', '.join(m_names)}")
        else:
            m_names = [m["name"] for m in team if not m.get("is_rep")]
            if m_names: st.write(f"**Members:** {', '.join(m_names)}")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Logs")
    # Chairman and Reps for their respective projects can add logs
    if is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE"):
        with st.form("log_entry"):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("Activity Description")
            if st.form_submit_button("Post Report"):
                st.session_state.data["logs"].append({"project": view_proj, "date": str(l_date), "type": l_type, "desc": l_desc})
                save_data(); st.rerun()
    
    st.write("---")
    for l in reversed(st.session_state.data.get("logs", [])):
        if l.get("project") == view_proj:
            with st.chat_message("user"):
                st.write(f"**{l['date']} | {l['type']}**")
                st.write(l["desc"])

# --- TIME TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    can_track = is_chairman or (is_skit_rep and view_proj == "SKIT") or (is_brochure_rep and view_proj == "BROCHURE")
    
    if can_track:
        with st.form("time_input"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Select Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Save Time Contribution") and target:
                st.session_state.data["contributions"].append({
                    "project": view_proj, "name": target, "time": f"{h}h {m}m", "date": str(date.today())
                })
                save_data(); st.rerun()
    
    st.write("---")
    history = [c for c in st.session_state.data.get("contributions", []) if c.get("project") == view_proj]
    if history: st.table(pd.DataFrame(history))

# --- MANAGEMENT CENTER (CHAIRMAN ONLY) ---
elif page == "Management Center" and is_chairman:
    st.title("👑 Chairman Control Center")
    t1, t2 = st.tabs(["Member Management", "Schedule Management"])
    
    with t1:
        st.subheader("Add or Edit Members")
        with st.form("add_member"):
            m_name = st.text_input("Full Name")
            m_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Assign as Representative?")
            m_sub = st.selectbox("SKIT Category", ["Actors", "Prop makers", "Cameraman", "N/A"]) if m_proj == "SKIT" else "N/A"
            if st.form_submit_button("Save Person to Roster"):
                # Remove existing entry for account update logic
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != m_name.lower()]
                st.session_state.data["members"].append({"name": m_name, "project": m_proj, "sub_role": m_sub, "is_rep": m_rep})
                save_data(); st.rerun()
        
        st.write("---")
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c1, c2 = st.columns([4, 1])
            rep_tag = " [REP]" if m.get("is_rep") else ""
            c1.write(f"**{m['name']}**{rep_tag} | {m['project']} ({m['sub_role']})")
            if c2.button("Delete", key=f"del_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()

    with t2:
        st.subheader("Create New Event")
        with st.form("sch_event"):
            e_p = st.selectbox("Project", ["SKIT", "BROCHURE"])
            e_t = st.selectbox("Category", ["Discussion", "Rehearsal"])
            e_d = st.date_input("Date")
            e_s, e_e = st.time_input("Start"), st.time_input("End")
            e_v = st.text_input("Venue")
            if st.form_submit_button("Add to Schedule") and e_v:
                st.session_state.data["events"].append({"project": e_p, "type": e_t, "date": e_d, "start_time": e_s, "end_time": e_e, "venue": e_v})
                save_data(); st.rerun()
        
        st.write("---")
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c_ev, c_can = st.columns([4, 1])
            c_ev.write(f"**{e['type']}** on {e['date']} @ {e['venue']}")
            if c_can.button("Cancel Event", key=f"ecan_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
