import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_data_v8.json"

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

# --- SESSION INITIALIZATION ---
if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}
    }

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.u_name = ""
    st.session_state.u_role = ""

# --- AUTHENTICATION ---
USER_PASSWORDS = {
    "Teacher": "teach2026", 
    "Chairman": "chair2026", 
    "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", 
    "Brochure Representative": "brochure2026",
    "VIA members": "member2026", 
    "Classmates": "class2026"
}

def login():
    st.title("🛡️ VIA Class Portal 2026")
    with st.form("login_form"):
        u_name = st.text_input("Enter Your Name").strip().title()
        u_role = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
        u_pw = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if u_name and u_pw == USER_PASSWORDS.get(u_role):
                st.session_state.logged_in = True
                st.session_state.u_name = u_name
                st.session_state.u_role = u_role
                st.rerun()
            else:
                st.error("Invalid credentials.")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- PERMISSIONS & ROLE LOGIC ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_comm = (c_role == "VIA Committee")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# --- SIDEBAR NAVIGATION ---
st.sidebar.title(f"👤 {c_name}")
st.sidebar.info(f"Role: {c_role}")

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.session_state.u_name = ""
    st.session_state.u_role = ""
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])

nav_options = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair:
    nav_options.append("Management Center")

page = st.sidebar.radio("Navigation", nav_options)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Event RSVP")
        events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
        
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            existing_vote = next((r for r in st.session_state.data.get("rsvp", []) if r['name'] == c_name and r['event_id'] == e_id), None)

            with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Time:** {e['start_time']} to {e['end_time']}")
                
                # RSVP Logic
                if not is_past:
                    with st.form(f"vote_{i}"):
                        v_stat = st.radio("Will you attend?", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason", value=existing_vote['reason'] if existing_vote else "N/A")
                        if st.form_submit_button("Submit Vote"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data.get("rsvp", []) if not (r['name'] == c_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({
                                "event_id": e_id, "name": c_name, "status": v_stat, 
                                "reason": v_res, "timestamp": str(datetime.now().strftime("%Y-%m-%d %H:%M"))
                            })
                            save_data(); st.rerun()

                if existing_vote:
                    st.success(f"📄 **CONFIRMATION**\nStatus: {existing_vote['status']}\nReason: {existing_vote['reason']}")

                # Restricted visibility of responses
                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    st.write("**Leader's RSVP View:**")
                    resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                    if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])

    with col2:
        st.subheader("👥 Roster")
        m_list = [m for m in st.session_state.data.get("members", []) if m.get("project") == view_proj]
        for m in m_list:
            role_tag = "⭐ Representative" if m.get("is_rep") else "Member"
            st.write(f"**{m['name']}**")
            st.caption(f"{role_tag} | Role: {m.get('sub_role')}")
            st.write("---")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title("✅ Attendance Recording")
    events = [e for e in st.session_state.data.get("events", []) if e.get("project") == view_proj]
    
    if not events:
        st.info("No events scheduled for this project.")
    else:
        sel_ev_str = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        e = events[[f"{e['type']} - {e['date']}" for e in events].index(sel_ev_str)]
        e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        
        # Only show people who RSVP'd Attending or Late
        voted_names = [r['name'] for r in st.session_state.data.get("rsvp", []) if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        
        can_mark = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
        
        if not voted_names:
            st.warning("No members marked 'Attending' for this event.")
        else:
            for name in voted_names:
                rec = st.session_state.data.get("attendance_records", {}).get(e_id, {}).get(name, {"present": False, "duration": "Full Session"})
                col_n, col_p, col_d = st.columns(3)
                col_n.write(name)
                
                if can_mark:
                    p = col_p.checkbox("Present", value=rec["present"], key=f"att_{name}_{e_id}")
                    d = col_d.selectbox("Duration", ["Full Session", "Half Session"], index=0 if rec["duration"]=="Full Session" else 1, key=f"dur_{name}_{e_id}")
                    if e_id not in st.session_state.data["attendance_records"]: st.session_state.data["attendance_records"][e_id] = {}
                    st.session_state.data["attendance_records"][e_id][name] = {"present": p, "duration": d}
                else:
                    col_p.write("✅ Present" if rec["present"] else "❌ Absent")
                    col_d.write(rec["duration"])
            
            if can_mark and st.button("Save Attendance"):
                save_data(); st.success("Attendance Saved.")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Activity Log")
    
    # Leaders can add entries
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.expander("➕ Add New Entry"):
            with st.form("new_log"):
                ld = st.date_input("Date")
                lt = st.selectbox("Type", ["Discussion", "Rehearsal"])
                la = st.text_area("Description of activities")
                if st.form_submit_button("Post Log"):
                    st.session_state.data["logs"].append({
                        "id": str(datetime.now().timestamp()), "project": view_proj, 
                        "date": str(ld), "type": lt, "activity": la, "comments": []
                    })
                    save_data(); st.rerun()

    # Display Logs
    for i, l in enumerate(reversed(st.session_state.data.get("logs", []))):
        if l.get("project") == view_proj:
            with st.container(border=True):
                st.write(f"### {l['type']} ({l['date']})")
                st.write(l["activity"])
                
                # Delete Log (Leaders Only)
                if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
                    if st.button("🗑️ Delete Log", key=f"dellog_{l['id']}"):
                        st.session_state.data["logs"] = [log for log in st.session_state.data["logs"] if log['id'] != l['id']]
                        save_data(); st.rerun()

                st.write("---")
                st.write("**Teacher Comments:**")
                
                for idx, c in enumerate(l.get("comments", [])):
                    st.caption(f"**{c['author']}**: {c['text']}")
                    # Edit/Delete Teacher Comments
                    if is_teach and c['author'] == c_name:
                        c_edit, c_del = st.columns(2)
                        if c_del.button("❌ Delete Comment", key=f"delc_{l['id']}_{idx}"):
                            l["comments"].pop(idx)
                            save_data(); st.rerun()
                
                if is_teach:
                    with st.form(f"comment_form_{l['id']}"):
                        new_c = st.text_input("Add/Edit Comment")
                        if st.form_submit_button("Post Comment"):
                            l["comments"].append({"author": c_name, "text": new_c, "time": str(datetime.now())})
                            save_data(); st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Contribution Tracker")
    can_track = is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
    
    if can_track:
        with st.form("contribution_form"):
            names = [m["name"] for m in st.session_state.data.get("members", []) if m["project"] == view_proj]
            target = st.selectbox("Select Member", names) if names else None
            h = st.number_input("Hours", 0)
            m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Time"):
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h * 60) + m
                save_data(); st.rerun()

    # Display Table
    tracker_list = []
    for m in st.session_state.data.get("members", []):
        if m["project"] == view_proj:
            total = st.session_state.data["contributions"].get(m["name"], 0)
            tracker_list.append({"Name": m["name"], "Total Time": f"{total//60}h {total%60}m"})
    if tracker_list: st.table(pd.DataFrame(tracker_list))

# --- MANAGEMENT CENTER ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Control Center")
    tab1, tab2 = st.tabs(["Members", "Events"])
    
    with tab1:
        with st.form("add_member"):
            m_name = st.text_input("Member Name")
            m_proj = st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Set as Representative")
            if m_proj == "SKIT":
                m_role = st.selectbox("Skit Role", ["Actors", "Prop makers", "Cameraman", "N/A"])
            else:
                m_role = "Designer" # Auto for Brochure
            
            if st.form_submit_button("Add Member"):
                # Clean existing to allow editing
                st.session_state.data["members"] = [m for m in st.session_state.data["members"] if m["name"] != m_name]
                st.session_state.data["members"].append({"name": m_name, "project": m_proj, "is_rep": m_rep, "sub_role": m_role})
                save_data(); st.success(f"Saved {m_name}"); st.rerun()
        
        # Display & Delete Members
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4,1])
            c1.write(f"{m['name']} - {m['project']} ({m['sub_role']}) {'[REP]' if m['is_rep'] else ''}")
            if c2.button("🗑️", key=f"delm_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()

    with tab2:
        with st.form("add_event"):
            ep = st.selectbox("Project", ["SKIT", "BROCHURE"])
            et = st.selectbox("Event Type", ["Discussion", "Rehearsal"])
            ed = st.date_input("Date")
            es = st.time_input("Start Time")
            ee = st.time_input("End Time")
            ev = st.text_input("Venue")
            if st.form_submit_button("Schedule Event"):
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        
        for i, ev in enumerate(st.session_state.data["events"]):
            st.write(f"**{ev['type']}** - {ev['date']} @ {ev['venue']}")
            if st.button("❌ Cancel Event", key=f"cevent_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
