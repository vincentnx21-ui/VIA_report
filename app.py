import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- 2. DATA PERSISTENCE ---
DATA_FILE = "via_data_v11.json"

# --- 3. SESSION INITIALIZATION (The Fix for Persistence) ---
# We initialize these once. On refresh, Streamlit checks if they already exist.
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "u_name" not in st.session_state:
    st.session_state.u_name = ""
if "u_role" not in st.session_state:
    st.session_state.u_role = ""

# Load data into session state if not already there
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                # Convert date/time strings back to Python objects
                for e in raw.get("events", []):
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                st.session_state.data = raw
        except:
            st.session_state.data = {"members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}}
    else:
        st.session_state.data = {"members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance_records": {}}

# --- 4. HELPER FUNCTIONS ---
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

# --- 5. AUTHENTICATION GATE ---
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

# If the user is NOT authenticated, show ONLY the login form
if not st.session_state.authenticated:
    st.title("🛡️ VIA Class Portal 2026")
    with st.form("login_form"):
        name_input = st.text_input("Full Name").strip().title()
        role_input = st.selectbox("Role", list(USER_PASSWORDS.keys()))
        pass_input = st.text_input("Password", type="password")
        
        if st.form_submit_button("Login"):
            if name_input and pass_input == USER_PASSWORDS.get(role_input):
                st.session_state.authenticated = True
                st.session_state.u_name = name_input
                st.session_state.u_role = role_input
                st.rerun() # Refresh to clear login form and show app
            else:
                st.error("Invalid credentials. Please try again.")
    st.stop() # This prevents the rest of the code from running if not logged in

# --- 6. SECURE APP CONTENT (Only reached if authenticated) ---
c_name = st.session_state.u_name
c_role = st.session_state.u_role

# Role checks
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# Sidebar
st.sidebar.title(f"👤 {c_name}")
st.sidebar.caption(f"Role: {c_role}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.authenticated = False
    st.session_state.u_name = ""
    st.session_state.u_role = ""
    st.rerun()

st.sidebar.divider()
view_proj = st.sidebar.radio("View Project", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair:
    nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

# --- DASHBOARD PAGE ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Scheduled Events")
        events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        if not events:
            st.info("No events scheduled yet.")
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            vote = next((r for r in st.session_state.data["rsvp"] if r['name'] == c_name and r['event_id'] == e_id), None)
            
            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Time:** {e['start_time']} to {e['end_time']}")
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        v_stat = st.radio("Attendance", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason", value=vote['reason'] if vote else "N/A")
                        if st.form_submit_button("Submit RSVP"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name']==c_name and r['event_id']==e_id)]
                            st.session_state.data["rsvp"].append({"event_id":e_id, "name":c_name, "status":v_stat, "reason":v_res})
                            save_data()
                            st.success("RSVP Saved!")
                            st.rerun()
                
                if vote:
                    st.info(f"**Your RSVP:** {vote['status']} | **Reason:** {vote['reason']}")
                
                # Leaders can see the list
                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    st.write("---")
                    st.write("**Responses:**")
                    resps = [r for r in st.session_state.data["rsvp"] if r['event_id'] == e_id]
                    if resps: st.table(pd.DataFrame(resps))

    with col2:
        st.subheader("👥 Project Roster")
        for m in [m for m in st.session_state.data["members"] if m["project"] == view_proj]:
            st.write(f"**{m['name']}**")
            st.caption(f"{'⭐ Rep' if m['is_rep'] else 'Member'} | Role: {m['sub_role']}")

# --- ATTENDANCE TAB ---
elif page == "Attendance Tab":
    st.title("✅ Event Attendance")
    events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
    if not events:
        st.warning("No events available.")
    else:
        sel = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(sel)
        e = events[idx]
        e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        
        voted = [r['name'] for r in st.session_state.data["rsvp"] if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        can_mark = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT")
        
        if not voted:
            st.info("No members have RSVP'd 'Attending' for this event yet.")
        else:
            for name in voted:
                rec = st.session_state.data["attendance_records"].get(e_id, {}).get(name, {"present": False, "duration": "Full"})
                c1, c2, c3 = st.columns(3)
                c1.write(name)
                if can_mark:
                    p = c2.checkbox("Present", value=rec["present"], key=f"att_{name}_{e_id}")
                    d = c3.selectbox("Session", ["Full", "Half"], index=0 if rec["duration"]=="Full" else 1, key=f"dur_{name}_{e_id}")
                    if e_id not in st.session_state.data["attendance_records"]: st.session_state.data["attendance_records"][e_id] = {}
                    st.session_state.data["attendance_records"][e_id][name] = {"present": p, "duration": d}
                else:
                    c2.write("✅" if rec["present"] else "❌")
                    c3.write(rec["duration"])
            
            if can_mark and st.button("Save Attendance Records"):
                save_data()
                st.success("Attendance Updated!")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Activity Log")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.expander("Add Entry"):
            with st.form("new_log"):
                ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("Summary")
                if st.form_submit_button("Post"):
                    st.session_state.data["logs"].append({"id": str(datetime.now().timestamp()), "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []})
                    save_data()
                    st.rerun()
    
    for l in reversed(st.session_state.data["logs"]):
        if l["project"] == view_proj:
            with st.container(border=True):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])
                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    if st.button("Delete Log", key=f"dl_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x['id'] != l['id']]
                        save_data()
                        st.rerun()
                st.divider()
                for i, c in enumerate(l["comments"]):
                    st.caption(f"**{c['author']}**: {c['text']}")
                    if is_teach and c['author'] == c_name:
                        if st.button("Remove", key=f"rc_{l['id']}_{i}"):
                            l["comments"].pop(i)
                            save_data()
                            st.rerun()
                if is_teach:
                    with st.form(f"f_{l['id']}"):
                        msg = st.text_input("Comment")
                        if st.form_submit_button("Post"):
                            l["comments"].append({"author": c_name, "text": msg})
                            save_data()
                            st.rerun()

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title("⏳ Time Tracker")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("time"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Contribution"):
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h*60) + m
                save_data()
                st.rerun()
    
    disp = [{"Name": m["name"], "Total": f"{st.session_state.data['contributions'].get(m['name'],0)//60}h {st.session_state.data['contributions'].get(m['name'],0)%60}m"} 
            for m in st.session_state.data["members"] if m["project"]==view_proj]
    if disp: st.table(pd.DataFrame(disp))

# --- MANAGEMENT CENTER ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Hub")
    t1, t2 = st.tabs(["Roster Management", "Event Schedule"])
    with t1:
        with st.form("m"):
            mn, mp = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            mr = st.checkbox("Representative")
            ms = st.selectbox("Skit Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp=="SKIT" else "Designer"
            if st.form_submit_button("Save Member"):
                st.session_state.data["members"] = [x for x in st.session_state.data["members"] if x['name'] != mn]
                st.session_state.data["members"].append({"name": mn, "project": mp, "is_rep": mr, "sub_role": ms})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{m['name']} ({m['project']}) - {m['sub_role']}")
            if c2.button("Remove Member", key=f"rm_m_{i}"):
                st.session_state.data["members"].pop(i)
                save_data(); st.rerun()
    with t2:
        with st.form("e"):
            p, t, d = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            s, et, v = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": p, "type": t, "date": d, "start_time": s, "end_time": et, "venue": v})
                save_data(); st.rerun()
        for i, ev in enumerate(st.session_state.data["events"]):
            if st.button(f"Cancel {ev['type']} ({ev['date']})", key=f"ce_{i}"):
                st.session_state.data["events"].pop(i)
                save_data(); st.rerun()
