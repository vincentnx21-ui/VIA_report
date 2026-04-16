import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data_v9.json"

def save_data():
    try:
        data = {
            "members": st.session_state.data.get("members", []),
            "logs": st.session_state.data.get("logs", []),
            "contributions": st.session_state.data.get("contributions", {}),
            "rsvp": st.session_state.data.get("rsvp", []),
            "attendance_records": st.session_state.data.get("attendance_records", {}),
            "events": []
        }
        for e in st.session_state.data.get("events", []):
            e_copy = e.copy()
            e_copy["date"] = e["date"].isoformat() if isinstance(e["date"], (date, datetime)) else str(e["date"])
            e_copy["start_time"] = e["start_time"].strftime("%H:%M")
            e_copy["end_time"] = e["end_time"].strftime("%H:%M")
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
                # Ensure all keys exist to prevent KeyErrors
                for d_key in ["contributions", "attendance_records"]:
                    if d_key not in raw or not isinstance(raw[d_key], dict): raw[d_key] = {}
                for l_key in ["members", "logs", "rsvp", "events"]:
                    if l_key not in raw or not isinstance(raw[l_key], list): raw[l_key] = []
                
                # Format time/date objects
                for e in raw["events"]:
                    if isinstance(e.get("date"), str): e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e.get("start_time"), str): e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    if isinstance(e.get("end_time"), str): e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                return raw
        except: return None
    return None

# --- INITIALIZE SESSION STATE ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.u_name = ""
    st.session_state.u_role = ""

# --- LOGIN SYSTEM ---
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🛡️ VIA Class Portal 2026")
    with st.form("login_panel"):
        u_name = st.text_input("Enter Your Name").strip().title()
        u_role = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
        u_pw = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_name and u_pw == USER_PASSWORDS.get(u_role):
                st.session_state.logged_in = True
                st.session_state.u_name = u_name
                st.session_state.u_role = u_role
                st.rerun()
            else: st.error("Incorrect credentials.")
    st.stop()

# --- GLOBALS & PERMISSIONS ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_comm = (c_role == "VIA Committee")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# --- SIDEBAR ---
st.sidebar.title(f"👤 {c_name}")
st.sidebar.info(f"Role: {c_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project Context", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair: nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD (RSVP & ROSTER) ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📅 Event RSVP")
        events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        if not events: st.info("No events scheduled.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            existing = next((r for r in st.session_state.data["rsvp"] if r['name'] == c_name and r['event_id'] == e_id), None)
            
            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        v_stat = st.radio("Status", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason (N/A if attending)", value=existing['reason'] if existing else "N/A")
                        if st.form_submit_button("Submit Response"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name']==c_name and r['event_id']==e_id)]
                            st.session_state.data["rsvp"].append({"event_id":e_id, "name":c_name, "status":v_stat, "reason":v_res})
                            save_data(); st.rerun()
                if existing: st.success(f"Confirmation: {existing['status']} | Reason: {existing['reason']}")
                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    resps = [r for r in st.session_state.data["rsvp"] if r['event_id'] == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
    with col2:
        st.subheader("👥 Project Roster")
        for m in [m for m in st.session_state.data["members"] if m["project"] == view_proj]:
            st.write(f"**{m['name']}**")
            st.caption(f"{'⭐ Representative' if m['is_rep'] else 'Member'} | Role: {m['sub_role']}")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title("✅ Event Attendance")
    events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
    if events:
        sel_ev = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(sel_ev)
        e = events[idx]; e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        voted = [r['name'] for r in st.session_state.data["rsvp"] if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        can_edit = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
        for p_name in voted:
            rec = st.session_state.data["attendance_records"].get(e_id, {}).get(p_name, {"present": False, "duration": "Full Session"})
            c1, c2, c3 = st.columns(3)
            c1.write(p_name)
            if can_edit:
                p = c2.checkbox("Attended", value=rec["present"], key=f"att_{p_name}_{e_id}")
                dur = c3.selectbox("Session", ["Full Session", "Half Session"], index=0 if rec["duration"]=="Full Session" else 1, key=f"dur_{p_name}_{e_id}")
                if e_id not in st.session_state.data["attendance_records"]: st.session_state.data["attendance_records"][e_id] = {}
                st.session_state.data["attendance_records"][e_id][p_name] = {"present": p, "duration": dur}
            else:
                c2.write("✅" if rec["present"] else "❌")
                c3.write(rec["duration"])
        if can_edit and st.button("Save Attendance"): save_data(); st.success("Updated")

# --- ACTIVITY LOG (WITH TEACHER FEEDBACK) ---
elif page == "Activity Log":
    st.title("📝 Activity Log & Feedback")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.expander("Add Entry"):
            with st.form("log_entry"):
                ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("Details")
                if st.form_submit_button("Post"):
                    st.session_state.data["logs"].append({"id": str(datetime.now().timestamp()), "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []})
                    save_data(); st.rerun()
    for l in reversed(st.session_state.data["logs"]):
        if l["project"] == view_proj:
            with st.container(border=True):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])
                if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
                    if st.button("Delete Entry", key=f"del_l_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x['id'] != l['id']]
                        save_data(); st.rerun()
                st.write("---")
                for i, c in enumerate(l["comments"]):
                    st.caption(f"**{c['author']}**: {c['text']}")
                    if is_teach and c['author'] == c_name:
                        c_edit, c_del = st.columns(2)
                        if c_del.button("Delete Comment", key=f"dc_{l['id']}_{i}"):
                            l["comments"].pop(i); save_data(); st.rerun()
                if is_teach:
                    with st.form(f"com_{l['id']}"):
                        msg = st.text_input("Teacher Feedback")
                        if st.form_submit_button("Post Feedback"):
                            l["comments"].append({"author": c_name, "text": msg})
                            save_data(); st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Cumulative Time Log")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("time_track"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Contribution"):
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h*60) + m
                save_data(); st.rerun()
    t_df = [{"Name": m["name"], "Total Time": f"{st.session_state.data['contributions'].get(m['name'],0)//60}h {st.session_state.data['contributions'].get(m['name'],0)%60}m"} for m in st.session_state.data["members"] if m["project"]==view_proj]
    if t_df: st.table(pd.DataFrame(t_df))

# --- MANAGEMENT CENTER (CHAIRMAN ONLY) ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Hub")
    tab1, tab2 = st.tabs(["Roster", "Schedule"])
    with tab1:
        with st.form("m_man"):
            m_n, m_p = st.text_input("Member Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_r = st.checkbox("Representative")
            m_s = st.selectbox("Skit Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if m_p == "SKIT" else "Designer"
            if st.form_submit_button("Save Member"):
                st.session_state.data["members"] = [x for x in st.session_state.data["members"] if x['name'] != m_n]
                st.session_state.data["members"].append({"name": m_n, "project": m_p, "is_rep": m_r, "sub_role": m_s})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{m['name']} ({m['project']}) - {m['sub_role']}")
            if c2.button("Remove", key=f"rm_m_{i}"): st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with tab2:
        with st.form("e_man"):
            p, t, d = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            s, et, v = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": p, "type": t, "date": d, "start_time": s, "end_time": et, "venue": v})
                save_data(); st.rerun()
        for i, ev in enumerate(st.session_state.data["events"]):
            if st.button(f"Cancel Event: {ev['type']} ({ev['date']})", key=f"can_e_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
