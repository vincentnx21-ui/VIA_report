import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- 1. PAGE CONFIG & PERSISTENCE ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# This file stores all your class data
DATA_FILE = "via_data_final_v10.json"

# --- 2. SESSION STATE INITIALIZATION (The Fix for Refreshing) ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.u_name = ""
    st.session_state.u_role = ""

# Initialize Data Structure
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
            # Date/Time conversion
            for e in raw.get("events", []):
                e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
            st.session_state.data = raw
    else:
        st.session_state.data = {
            "members": [], "logs": [], "contributions": {}, 
            "events": [], "rsvp": [], "attendance_records": {}
        }

# --- 3. HELPER FUNCTIONS ---
def save_data():
    data_to_save = st.session_state.data.copy()
    serializable_events = []
    for e in data_to_save.get("events", []):
        e_copy = e.copy()
        e_copy["date"] = e["date"].isoformat()
        e_copy["start_time"] = e["start_time"].strftime("%H:%M")
        e_copy["end_time"] = e["end_time"].strftime("%H:%M")
        serializable_events.append(e_copy)
    data_to_save["events"] = serializable_events
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f)

# --- 4. AUTHENTICATION GATE ---
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.authenticated:
    st.title("🛡️ VIA Class Portal 2026")
    with st.form("secure_login"):
        u_name = st.text_input("Full Name").strip().title()
        u_role = st.selectbox("Role", list(USER_PASSWORDS.keys()))
        u_pw = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u_name and u_pw == USER_PASSWORDS.get(u_role):
                st.session_state.authenticated = True
                st.session_state.u_name = u_name
                st.session_state.u_role = u_role
                st.rerun()
            else:
                st.error("Invalid Login Credentials")
    st.stop() # CRITICAL: Stops the app here until authenticated is True

# --- 5. APP CONTENT (Only reaches here if logged in) ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# Sidebar Navigation
st.sidebar.title(f"👤 {c_name}")
st.sidebar.caption(f"Role: {c_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.divider()
view_proj = st.sidebar.radio("View Project", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair: nav.append("Management Center")
page = st.sidebar.radio("Go To", nav)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Project Events")
        events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            vote = next((r for r in st.session_state.data["rsvp"] if r['name'] == c_name and r['event_id'] == e_id), None)
            
            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        st.write(f"Time: {e['start_time']} - {e['end_time']}")
                        v_stat = st.radio("Will you attend?", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason", value=vote['reason'] if vote else "N/A")
                        if st.form_submit_button("Submit RSVP"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name']==c_name and r['event_id']==e_id)]
                            st.session_state.data["rsvp"].append({"event_id":e_id, "name":c_name, "status":v_stat, "reason":v_res})
                            save_data(); st.rerun()
                if vote: st.info(f"Your Status: {vote['status']} | {vote['reason']}")
                if is_chair or (is_skit_rep and view_proj=="SKIT"):
                    resps = [r for r in st.session_state.data["rsvp"] if r['event_id'] == e_id]
                    if resps: st.table(pd.DataFrame(resps))

    with col2:
        st.subheader("👥 Members")
        for m in [m for m in st.session_state.data["members"] if m["project"] == view_proj]:
            st.write(f"**{m['name']}**")
            st.caption(f"{'⭐ Rep' if m['is_rep'] else 'Member'} | {m['sub_role']}")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title("✅ Attendance")
    events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
    if events:
        sel = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(sel)
        e = events[idx]; e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        
        # Only Attending/Late people
        voted = [r['name'] for r in st.session_state.data["rsvp"] if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        can_mark = is_chair or is_teach or (is_skit_rep and view_proj=="SKIT")
        
        for name in voted:
            rec = st.session_state.data["attendance_records"].get(e_id, {}).get(name, {"present": False, "duration": "Full"})
            c1, c2, c3 = st.columns(3)
            c1.write(name)
            if can_mark:
                p = c2.checkbox("Present", value=rec["present"], key=f"p_{name}_{e_id}")
                d = c3.selectbox("Session", ["Full", "Half"], index=0 if rec["duration"]=="Full" else 1, key=f"d_{name}_{e_id}")
                if e_id not in st.session_state.data["attendance_records"]: st.session_state.data["attendance_records"][e_id] = {}
                st.session_state.data["attendance_records"][e_id][name] = {"present": p, "duration": d}
            else:
                c2.write("✅" if rec["present"] else "❌")
                c3.write(rec["duration"])
        if can_mark and st.button("Save Attendance"): save_data(); st.success("Saved")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Activity Log")
    if is_chair or (is_skit_rep and view_proj=="SKIT") or (is_broch_rep and view_proj=="BROCHURE"):
        with st.expander("Add New Log"):
            with st.form("log"):
                ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("Details")
                if st.form_submit_button("Post"):
                    st.session_state.data["logs"].append({"id": str(datetime.now().timestamp()), "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []})
                    save_data(); st.rerun()
    
    for l in reversed(st.session_state.data["logs"]):
        if l["project"] == view_proj:
            with st.container(border=True):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])
                if is_chair or (is_skit_rep and view_proj=="SKIT"):
                    if st.button("Delete Log", key=f"dl_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x['id'] != l['id']]
                        save_data(); st.rerun()
                st.divider()
                for i, c in enumerate(l["comments"]):
                    st.caption(f"**{c['author']}**: {c['text']}")
                    if is_teach and c['author'] == c_name:
                        if st.button("Remove Comment", key=f"rc_{l['id']}_{i}"):
                            l["comments"].pop(i); save_data(); st.rerun()
                if is_teach:
                    with st.form(f"f_{l['id']}"):
                        msg = st.text_input("Add Feedback")
                        if st.form_submit_button("Post"):
                            l["comments"].append({"author": c_name, "text": msg})
                            save_data(); st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Time Tracker")
    if is_chair or (is_skit_rep and view_proj=="SKIT") or (is_broch_rep and view_proj=="BROCHURE"):
        with st.form("time"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Time"):
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h*60) + m
                save_data(); st.rerun()
    
    # Display table
    disp = [{"Name": m["name"], "Time": f"{st.session_state.data['contributions'].get(m['name'],0)//60}h {st.session_state.data['contributions'].get(m['name'],0)%60}m"} 
            for m in st.session_state.data["members"] if m["project"]==view_proj]
    if disp: st.table(pd.DataFrame(disp))

# --- MANAGEMENT ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Hub")
    t1, t2 = st.tabs(["Members", "Schedule"])
    with t1:
        with st.form("m"):
            name, proj = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            rep = st.checkbox("Representative")
            role = st.selectbox("Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if proj=="SKIT" else "Designer"
            if st.form_submit_button("Save Member"):
                st.session_state.data["members"] = [x for x in st.session_state.data["members"] if x['name'] != name]
                st.session_state.data["members"].append({"name": name, "project": proj, "is_rep": rep, "sub_role": role})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{m['name']} ({m['project']})")
            if c2.button("Remove", key=f"rm_m_{i}"): st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("e"):
            p, t, d = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            s, et, v = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": p, "type": t, "date": d, "start_time": s, "end_time": et, "venue": v})
                save_data(); st.rerun()
        for i, ev in enumerate(st.session_state.data["events"]):
            if st.button(f"Cancel {ev['type']} ({ev['date']})", key=f"ce_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
