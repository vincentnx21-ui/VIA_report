import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Portal 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data_v7.json"

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
                # Defensive formatting
                if "contributions" not in raw or not isinstance(raw["contributions"], dict): raw["contributions"] = {}
                if "attendance_records" not in raw: raw["attendance_records"] = {}
                for key in ["members", "logs", "rsvp", "events"]:
                    if key not in raw or not isinstance(raw[key], list): raw[key] = []
                for e in raw["events"]:
                    if isinstance(e.get("date"), str): e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e.get("start_time"), str): 
                        try: e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                        except: e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                    if isinstance(e.get("end_time"), str): 
                        try: e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                        except: e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
                return raw
        except: return None
    return None

# --- INITIALIZE STATE ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}
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
    st.title("🛡️ VIA Class Portal 2026")
    u_name_in = st.text_input("Enter Your Name").strip().title()
    u_role_in = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
    u_pw_in = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_name_in and u_pw_in == USER_PASSWORDS.get(u_role_in):
            st.session_state.logged_in = True
            st.session_state.u_name = u_name_in
            st.session_state.u_role = u_role_in
            st.rerun()
        else: st.error("Incorrect credentials.")
    st.stop()

# --- GLOBALS & SIDEBAR ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_comm = (c_role == "VIA Committee")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

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
            existing_vote = next((r for r in st.session_state.data.get("rsvp", []) if r['name'] == c_name and r['event_id'] == e_id), None)

            with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                
                if not is_past:
                    with st.form(f"vote_{i}"):
                        v_stat = st.radio("Status:", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason (N/A if attending)", value=existing_vote['reason'] if existing_vote else "N/A")
                        if st.form_submit_button("Submit & Generate Confirmation"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == c_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": c_name, "status": v_stat, "reason": v_res, "timestamp": str(datetime.now().strftime("%H:%M"))})
                            save_data(); st.rerun()

                if existing_vote:
                    st.info(f"📄 **CONFIRMATION LETTER**\nTo: {c_name}\nStatus: {existing_vote['status']}\nReason: {existing_vote['reason']}")

                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    st.write("**Leader's RSVP Tracking:**")
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])

    with col2:
        st.subheader("👥 Roster")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        for m in m_list:
            rep_tag = "⭐ Representative | " if m.get("is_rep") else ""
            st.write(f"**{m['name']}**")
            st.caption(f"{rep_tag}Role: {m.get('sub_role')}")
            st.write("---")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title(f"✅ {view_proj} Attendance Check-in")
    events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
    
    if not events:
        st.warning("No events available for this project.")
    else:
        selected_event = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(selected_event)
        e = events[idx]
        e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        
        voted_attending = [r['name'] for r in st.session_state.data.get("rsvp", []) if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        
        if not voted_attending:
            st.info("No members marked 'Attending' for this event.")
        else:
            can_edit = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
            
            for person in voted_attending:
                event_recs = st.session_state.data.get("attendance_records", {}).get(e_id, {})
                rec = event_recs.get(person, {"present": False, "duration": "Full Session"})
                
                c1, c2, c3 = st.columns([2, 2, 2])
                c1.write(f"**{person}**")
                
                if can_edit:
                    is_p = c2.checkbox("Attended", value=rec["present"], key=f"p_{person}_{e_id}")
                    dur = c3.selectbox("Session", ["Full Session", "Half Session"], index=0 if rec["duration"]=="Full Session" else 1, key=f"d_{person}_{e_id}")
                    
                    if e_id not in st.session_state.data["attendance_records"]:
                        st.session_state.data["attendance_records"][e_id] = {}
                    st.session_state.data["attendance_records"][e_id][person] = {"present": is_p, "duration": dur}
                else:
                    c2.write("✅ Present" if rec["present"] else "❌ Not Checked")
                    c3.write(f"🕒 {rec['duration']}")

            if can_edit:
                if st.button("Save Attendance Records"):
                    save_data(); st.success("Attendance Updated!")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    can_log = is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
    
    if can_log:
        with st.form("log_f"):
            ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("What was done today?")
            if st.form_submit_button("Save Log Entry"):
                st.session_state.data["logs"].append({
                    "id": str(datetime.now().timestamp()), 
                    "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []
                })
                save_data(); st.rerun()
    
    for i, l in enumerate(reversed(st.session_state.data.get("logs", []))):
        if l.get("project") == view_proj:
            with st.container(border=True):
                col_txt, col_del = st.columns([5, 1])
                col_txt.write(f"### {l['date']} - {l['type']}")
                col_txt.write(l["activity"])
                
                if can_log:
                    if col_del.button("🗑️ Delete", key=f"dellog_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x['id'] != l['id']]
                        save_data(); st.rerun()
                
                # Teacher Comments
                can_see_feedback = is_chair or is_comm or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE") or is_teach
                if l.get("comments") and can_see_feedback:
                    st.write("---")
                    for c in l["comments"]: st.caption(f"👩‍🏫 Teacher Feedback: {c}")

                if is_teach:
                    with st.form(f"t_com_{l['id']}"):
                        t_msg = st.text_input("Comment for leaders")
                        if st.form_submit_button("Submit"):
                            l.setdefault("comments", []).append(t_msg)
                            save_data(); st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("time_f"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Contribution"):
                curr = st.session_state.data.get("contributions", {}).get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h * 60) + m
                save_data(); st.rerun()
    
    st.write("---")
    tracker_data = [{"Name": m["name"], "Total Time": f"{st.session_state.data.get('contributions', {}).get(m['name'],0)//60}h {st.session_state.data.get('contributions', {}).get(m['name'],0)%60}m"} 
                    for m in st.session_state.data.get("members", []) if m["project"] == view_proj]
    if tracker_data: st.table(pd.DataFrame(tracker_data))

# --- MANAGEMENT CENTER ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Hub")
    t1, t2 = st.tabs(["Roster Management", "Event Management"])
    with t1:
        with st.form("m_add"):
            mn, mp = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Is Representative?")
            ms = st.selectbox("Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp == "SKIT" else "Designer"
            if st.form_submit_button("Save Member"):
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"].lower() != mn.lower()]
                st.session_state.data["members"].append({"name": mn, "project": mp, "sub_role": ms, "is_rep": m_rep})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data.get("members", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{m['name']}** ({m['project']}) - {m['sub_role']} {'[REP]' if m.get('is_rep') else ''}")
            if c2.button("Remove", key=f"rm_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("e_add"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            es, ee, ev = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        for i, e in enumerate(st.session_state.data.get("events", [])):
            c1, c2 = st.columns([4, 1])
            c1.write(f"**{e['type']}** - {e['date']} @ {e['venue']}")
            if c2.button("Cancel Event", key=f"cn_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
