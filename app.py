import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- PERSISTENT LOGIN TRICK ---
# Streamlit clears session_state on refresh. 
# We use query_params to keep the user "soft-logged in" if they refresh.
if "logged_in" not in st.session_state:
    params = st.query_params
    if params.get("user") and params.get("role"):
        st.session_state.logged_in = True
        st.session_state.u_name = params.get("user")
        st.session_state.u_role = params.get("role")
    else:
        st.session_state.logged_in = False

# --- DATA PERSISTENCE ---
DATA_FILE = "via_v8.json"

def save_data():
    try:
        data = {
            "members": st.session_state.data.get("members", []),
            "logs": st.session_state.data.get("logs", []),
            "contributions": st.session_state.data.get("contributions", {}),
            "rsvp": st.session_state.data.get("rsvp", []),
            "attendance": st.session_state.data.get("attendance", {}),
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
                # Cleanup and fix keys
                for d in ["contributions", "attendance"]:
                    if d not in raw or not isinstance(raw[d], dict): raw[d] = {}
                for l in ["members", "logs", "rsvp", "events"]:
                    if l not in raw or not isinstance(raw[l], list): raw[l] = []
                
                for e in raw["events"]:
                    if isinstance(e.get("date"), str): e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    if isinstance(e.get("start_time"), str): e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    if isinstance(e.get("end_time"), str): e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                return raw
        except: return None
    return None

if "data" not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": [], "logs": [], "contributions": {}, "events": [], "rsvp": [], "attendance": {}
    }

# --- AUTH ---
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
            st.query_params["user"] = u_name_in
            st.query_params["role"] = u_role_in
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# --- GLOBALS ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_comm = (c_role == "VIA Committee")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# --- SIDEBAR ---
st.sidebar.title(f"👤 {c_name}")
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.query_params.clear()
    st.rerun()

view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav_options = ["Dashboard", "Attendance Tab", "Activity Log", "Contribution Tracker"]
if is_chair: nav_options.append("Management Center")
page = st.sidebar.radio("Navigation", nav_options)

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Schedule & RSVP")
        proj_events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        if not proj_events: st.info("No events scheduled.")
        
        for i, e in enumerate(proj_events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            user_rsvp = next((r for r in st.session_state.data["rsvp"] if r['name'] == c_name and r['event_id'] == e_id), None)

            with st.expander(f"{'🔴 PASSED' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                
                if not is_past:
                    with st.form(f"v_{i}"):
                        v_stat = st.radio("Status", ["Attending", "Not Attending", "Late"], index=0)
                        v_res = st.text_input("Reason (N/A if Attending)", value=user_rsvp['reason'] if user_rsvp else "N/A")
                        if st.form_submit_button("Submit & Print Confirmation"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name'] == c_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": c_name, "status": v_stat, "reason": v_res})
                            save_data(); st.rerun()

                if user_rsvp:
                    st.success(f"📄 **CONFIRMATION**\nName: {c_name} | Status: {user_rsvp['status']}\nReason: {user_rsvp['reason']}")

                if is_chair or (is_skit_rep and view_proj == "SKIT"):
                    st.write("**Leader Insight:**")
                    r_list = [r for r in st.session_state.data["rsvp"] if r["event_id"] == e_id]
                    if r_list: st.table(pd.DataFrame(r_list)[["name", "status", "reason"]])

    with col2:
        st.subheader("👥 Roster")
        m_list = [m for m in st.session_state.data["members"] if m["project"] == view_proj]
        for m in m_list:
            rep_tag = "⭐ Representative | " if m.get("is_rep") else ""
            st.write(f"**{m['name']}**")
            st.caption(f"{rep_tag}Role: {m['sub_role']}")

# --- ATTENDANCE ---
elif page == "Attendance Tab":
    st.title("✅ Attendance Recording")
    proj_events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
    if not proj_events:
        st.warning("No events.")
    else:
        sel_ev = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in proj_events])
        idx = [f"{e['type']} - {e['date']}" for e in proj_events].index(sel_ev)
        e = proj_events[idx]
        e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        
        voted_attending = [r['name'] for r in st.session_state.data["rsvp"] if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        
        if not voted_attending:
            st.info("No members marked 'Attending'.")
        else:
            can_edit_att = is_chair or is_teach or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE")
            
            for p in voted_attending:
                cur = st.session_state.data["attendance"].get(e_id, {}).get(p, {"present": False, "dur": "Full Session"})
                c1, c2, c3 = st.columns(3)
                c1.write(p)
                if can_edit_att:
                    is_p = c2.checkbox("Present", value=cur["present"], key=f"att_{p}_{e_id}")
                    stay = c3.selectbox("Session", ["Full Session", "Half Session"], index=0 if cur["dur"]=="Full Session" else 1, key=f"dur_{p}_{e_id}")
                    if e_id not in st.session_state.data["attendance"]: st.session_state.data["attendance"][e_id] = {}
                    st.session_state.data["attendance"][e_id][p] = {"present": is_p, "dur": stay}
                else:
                    c2.write("✅" if cur["present"] else "❌")
                    c3.write(cur["dur"])
            if can_edit_att and st.button("Save Records"):
                save_data(); st.success("Saved")

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title("📝 Activity Log")
    # Log Addition
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("new_log"):
            ld, lt, la = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.text_area("Summary")
            if st.form_submit_button("Add Log"):
                new_id = str(datetime.now().timestamp())
                st.session_state.data["logs"].append({"id": new_id, "project": view_proj, "date": str(ld), "type": lt, "activity": la, "comments": []})
                save_data(); st.rerun()

    # Log Display
    for i, l in enumerate(reversed(st.session_state.data["logs"])):
        if l["project"] == view_proj:
            with st.container(border=True):
                st.write(f"**{l['date']} - {l['type']}**")
                st.write(l["activity"])
                
                # Delete Log
                if is_chair:
                    if st.button(f"🗑️ Delete Log", key=f"del_log_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x["id"] != l["id"]]
                        save_data(); st.rerun()

                st.write("---")
                # Teacher Comments
                for ci, com in enumerate(l["comments"]):
                    st.caption(f"💬 **{com['author']}**: {com['text']}")
                    if is_teach and com['author'] == c_name:
                        c_col1, c_col2 = st.columns(2)
                        if c_col1.button("✏️ Edit", key=f"ed_com_{l['id']}_{ci}"):
                            st.session_state[f"edit_mode_{l['id']}_{ci}"] = True
                        if c_col2.button("🗑️ Delete", key=f"del_com_{l['id']}_{ci}"):
                            l["comments"].pop(ci)
                            save_data(); st.rerun()
                        
                        if st.session_state.get(f"edit_mode_{l['id']}_{ci}"):
                            new_text = st.text_input("Edit Comment", value=com['text'], key=f"inp_{l['id']}_{ci}")
                            if st.button("Update", key=f"up_{l['id']}_{ci}"):
                                com['text'] = new_text
                                del st.session_state[f"edit_mode_{l['id']}_{ci}"]
                                save_data(); st.rerun()

                if is_teach:
                    with st.form(f"com_f_{l['id']}"):
                        t_msg = st.text_input("Add Feedback")
                        if st.form_submit_button("Post"):
                            l["comments"].append({"author": c_name, "text": t_msg})
                            save_data(); st.rerun()

# --- CONTRIBUTION ---
elif page == "Contribution Tracker":
    st.title("⏳ Time Tracker")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.form("c_f"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Log Time") and target:
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h * 60) + m
                save_data(); st.rerun()
    
    table = [{"Name": m["name"], "Total": f"{st.session_state.data['contributions'].get(m['name'],0)//60}h {st.session_state.data['contributions'].get(m['name'],0)%60}m"} 
             for m in st.session_state.data["members"] if m["project"] == view_proj]
    if table: st.table(pd.DataFrame(table))

# --- MANAGEMENT ---
elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Management")
    t1, t2 = st.tabs(["Roster", "Schedule"])
    with t1:
        with st.form("m_a"):
            mn = st.text_input("Name")
            mp = st.selectbox("Project", ["SKIT", "BROCHURE"])
            m_rep = st.checkbox("Representative?")
            ms = st.selectbox("Skit Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if mp == "SKIT" else "Designer"
            if st.form_submit_button("Add Member"):
                st.session_state.data["members"] = [x for x in st.session_state.data["members"] if x["name"] != mn]
                st.session_state.data["members"].append({"name": mn, "project": mp, "sub_role": ms, "is_rep": m_rep})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            st.write(f"**{m['name']}** ({m['project']}) - {m['sub_role']} {'[REP]' if m.get('is_rep') else ''}")
            if st.button("Remove", key=f"rem_{i}"):
                st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("e_a"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            es, ee, ev = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": es, "end_time": ee, "venue": ev})
                save_data(); st.rerun()
        for i, e in enumerate(st.session_state.data["events"]):
            st.write(f"{e['type']} - {e['date']} @ {e['venue']}")
            if st.button("Cancel", key=f"can_{i}"):
                st.session_state.data["events"].pop(i); save_data(); st.rerun()
