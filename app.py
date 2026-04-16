import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data_v7.json"

def save_data():
    try:
        # Standardize state to prevent serialization errors
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
                for d_key in ["contributions", "attendance_records"]:
                    if d_key not in raw or not isinstance(raw[d_key], dict): raw[d_key] = {}
                for l_key in ["members", "logs", "rsvp", "events"]:
                    if l_key not in raw or not isinstance(raw[l_key], list): raw[l_key] = []
                for e in raw["events"]:
                    if isinstance(e.get("date"), str): e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e.get("start_time"), str): e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    if isinstance(e.get("end_time"), str): e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                return raw
        except: return None
    return None

# --- STATE INITIALIZATION ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}
    }

if "logged_in" not in st.session_state: st.session_state.logged_in = False

# --- AUTHENTICATION ---
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.logged_in:
    st.title("🛡️ VIA Class Portal 2026")
    u_name_in = st.text_input("Enter Your Name").strip().title()
    u_role_in = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
    u_pw_in = st.text_input("Password", type="password")
    if st.button("Login"):
        if u_name_in and u_pw_in == USER_PASSWORDS.get(u_role_in):
            st.session_state.logged_in, st.session_state.u_name, st.session_state.u_role = True, u_name_in, u_role_in
            st.rerun()
        else: st.error("Incorrect credentials.")
    st.stop()

# --- GLOBALS ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair, is_teach, is_comm = (c_role == "Chairman"), (c_role == "Teacher"), (c_role == "VIA Committee")
is_skit_rep, is_broch_rep = (c_role == "Skit Representative"), (c_role == "Brochure Representative")

# --- SIDEBAR ---
st.sidebar.title(f"👤 {c_name}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair: nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Event RSVP")
        events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        if not events: st.info("No events scheduled.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            existing = next((r for r in st.session_state.data.get("rsvp", []) if r['name'] == c_name and r['event_id'] == e_id), None)

            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                if not is_past:
                    with st.form(f"v_{i}"):
                        v_stat = st.radio("Attendance Choice:", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason", value=existing['reason'] if existing else "N/A")
                        if st.form_submit_button("Submit Vote"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == c_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": c_name, "status": v_stat, "reason": v_res, "timestamp": str(datetime.now().strftime("%H:%M"))})
                            save_data(); st.rerun()
                if existing:
                    st.info(f"📄 **CONFIRMATION LETTER**\nTo: {c_name}\nStatus: {existing['status']}\nReason: {existing['reason']}")
                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])

    with col2:
        st.subheader("👥 Roster")
        for m in [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]:
            st.write(f"**{m['name']}**")
            st.caption(f"{'⭐ Rep | ' if m.get('is_rep') else ''}{m.get('sub_role')}")
            st.write("---")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title(f"✅ {view_proj} Attendance")
    events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
    if not events: st.warning("No events.")
    else:
        sel = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(sel)
        e = events[idx]
        e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        voted = [r['name'] for r in st.session_state.data.get("rsvp", []) if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        if not voted: st.info("No members marked 'Attending'.")
        else:
            can_ed = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
            for person in voted:
                rec = st.session_state.data.get("attendance_records", {}).get(e_id, {}).get(person, {"present": False, "duration": "Full Session"})
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.write(f"**{person}**")
                if can_ed:
                    is_p = c2.checkbox("Attended", value=rec["present"], key=f"p_{person}_{e_id}")
                    dur = c3.selectbox("Length", ["Full Session", "Half Session"], index=0 if rec["duration"]=="Full Session" else 1, key=f"d_{person}_{e_id}")
                    if e_id not in st.session_state.data["attendance_records"]: st.session_state.data["attendance_records"][e_id] = {}
                    st.session_state.data["attendance_records"][e_id][person] = {"present": is_p, "duration": dur}
                else:
                    c2.write("✅ Present" if rec["present"] else "❌ Absent")
                    c3.write(f"🕒 {rec['duration']}")
            if can_ed and st.button("Save Attendance"): save_data(); st.success("Saved!")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("log_f"):
            ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("What was done?")
            if st.form_submit_button("Post Log"):
                st.session_state.data["logs"].append({"id": datetime.now().timestamp(), "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []})
                save_data(); st.rerun()

    for i, l in enumerate(reversed(st.session_state.data.get("logs", []))):
        if l.get("project") == view_proj:
            with st.chat_message("user"):
                c1, c2 = st.columns([5, 1])
                c1.write(f"**{l['date']} - {l['type']}**")
                if (is_chair or is_comm) and c2.button("🗑️ Delete Log", key=f"dl_{l['id']}"):
                    st.session_state.data["logs"] = [log for log in st.session_state.data["logs"] if log["id"] != l["id"]]
                    save_data(); st.rerun()
                st.write(l["activity"])
                
                # Feedback Section
                can_see = is_chair or is_comm or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE") or is_teach
                if l.get("comments") and can_see:
                    st.write("---")
                    for ci, com in enumerate(l["comments"]):
                        f1, f2, f3 = st.columns([4, 1, 1])
                        f1.caption(f"👩‍🏫 {com['author']}: {com['text']}")
                        if is_teach and com['author'] == c_name:
                            if f2.button("✏️", key=f"ed_{l['id']}_{ci}"):
                                st.session_state[f"edit_{l['id']}_{ci}"] = True
                            if f3.button("🗑️", key=f"dc_{l['id']}_{ci}"):
                                l["comments"].pop(ci); save_data(); st.rerun()
                        
                        if st.session_state.get(f"edit_{l['id']}_{ci}", False):
                            new_t = st.text_input("Edit Comment", value=com['text'], key=f"ti_{l['id']}_{ci}")
                            if st.button("Save Edit", key=f"se_{l['id']}_{ci}"):
                                com['text'] = new_t
                                st.session_state[f"edit_{l['id']}_{ci}"] = False
                                save_data(); st.rerun()

                if is_teach:
                    with st.form(f"t_f_{l['id']}"):
                        t_msg = st.text_input("Leave feedback")
                        if st.form_submit_button("Submit"):
                            l.setdefault("comments", []).append({"author": c_name, "text": t_msg})
                            save_data(); st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("t_add"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Time") and target:
                st.session_state.data["contributions"][target] = st.session_state.data.get("contributions", {}).get(target, 0) + (h * 60) + m
                save_data(); st.rerun()
    tracker_data = [{"Name": m["name"], "Total": f"{st.session_state.data.get('contributions',{}).get(m['name'],0)//60}h {st.session_state.data.get('contributions',{}).get(m['name'],0)%60}m"} 
                    for m in st.session_state.data["members"] if m["project"] == view_proj]
    if tracker_data: st.table(pd.DataFrame(tracker_data))

# --- MANAGEMENT ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Control")
    t1, t2 = st.tabs(["Roster", "Events"])
    with t1:
        with st.form("m_a"):
            mn, mp = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep, ms = st.checkbox("Rep?"), st.selectbox("Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp == "SKIT" else "Designer"
            if st.form_submit_button("Save"):
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != mn.lower()]
                st.session_state.data["members"].append({"name": mn, "project": mp, "sub_role": ms, "is_rep": m_rep})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{m['name']} ({m['project']}) - {m['sub_role']} {'[REP]' if m.get('is_rep') else ''}")
            if c2.button("Remove", key=f"rm_m_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("e_a"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            es, ee, ev = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Schedule"):
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        for i, e in enumerate(st.session_state.data["events"]):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{e['type']} - {e['date']} @ {e['venue']}")
            if c2.button("Cancel", key=f"cn_e_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
