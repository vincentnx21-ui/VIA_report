import streamlit as st
import pandas as pd
from datetime import datetime, time, date
import json
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="VIA Project Hub 2026", layout="wide")

# --- 2. DATA PERSISTENCE ---
DATA_FILE = "via_system_data.json"

# Initialize Session State for Persistence
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "u_name" not in st.session_state:
    st.session_state.u_name = ""
if "u_role" not in st.session_state:
    st.session_state.u_role = ""

# Load or Initialize Global Data
if "data" not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            raw = json.load(f)
            
            # --- FIX: Ensure all required keys exist (Prevents KeyError) ---
            required_keys = {
                "members": [], 
                "accounts": [], 
                "logs": [], 
                "contributions": {}, 
                "events": [], 
                "rsvp": [], 
                "attendance": {}
            }
            for key, default_value in required_keys.items():
                if key not in raw:
                    raw[key] = default_value
            
            # Convert date/time strings back to objects
            for e in raw.get("events", []):
                if isinstance(e["date"], str):
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                if isinstance(e["start_time"], str):
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                if isinstance(e["end_time"], str):
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
            st.session_state.data = raw
    else:
        st.session_state.data = {
            "members": [], "accounts": [], "logs": [], 
            "contributions": {}, "events": [], "rsvp": [], "attendance": {}
        }

def save_data():
    data_copy = st.session_state.data.copy()
    serializable_events = []
    for e in data_copy.get("events", []):
        e_c = e.copy()
        e_c["date"] = e["date"].isoformat() if hasattr(e["date"], 'isoformat') else e["date"]
        e_c["start_time"] = e["start_time"].strftime("%H:%M") if hasattr(e["start_time"], 'strftime') else e["start_time"]
        e_c["end_time"] = e["end_time"].strftime("%H:%M") if hasattr(e["end_time"], 'strftime') else e["end_time"]
        serializable_events.append(e_c)
    data_copy["events"] = serializable_events
    with open(DATA_FILE, "w") as f:
        json.dump(data_copy, f)

# --- 3. AUTHENTICATION GATE ---
USER_PASSWORDS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Skit Representative": "skit2026", "Brochure Representative": "brochure2026",
    "VIA members": "member2026", "Classmates": "class2026"
}

if not st.session_state.authenticated:
    st.title("🛡️ VIA Class Portal 2026")
    with st.form("login_form"):
        name_in = st.text_input("Enter Your Name").strip().title()
        role_in = st.selectbox("Select Role", list(USER_PASSWORDS.keys()))
        pw_in = st.text_input("Password", type="password")
        
        if st.form_submit_button("Sign In"):
            if name_in and pw_in == USER_PASSWORDS.get(role_in):
                st.session_state.authenticated = True
                st.session_state.u_name = name_in
                st.session_state.u_role = role_in
                
                # Save account to history if new
                exists = any(a['name'] == name_in for a in st.session_state.data["accounts"])
                if not exists:
                    st.session_state.data["accounts"].append({"name": name_in, "role": role_in, "joined": str(date.today())})
                    save_data()
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- 4. APP LOGIC (Authenticated Only) ---
c_name, c_role = st.session_state.u_name, st.session_state.u_role
is_chair = (c_role == "Chairman")
is_teach = (c_role == "Teacher")
is_skit_rep = (c_role == "Skit Representative")
is_broch_rep = (c_role == "Brochure Representative")

# Sidebar
st.sidebar.title(f"👤 {c_name}")
st.sidebar.info(f"Access Level: {c_role}")
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.rerun()

st.sidebar.divider()
view_proj = st.sidebar.radio("Active Project", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Attendance", "Activity Log", "Contribution Tracker"]
if is_chair: nav.append("Management Center")
page = st.sidebar.radio("Navigate", nav)

# --- PAGES ---

if page == "Dashboard":
    st.title(f"🚀 {view_proj} Project Hub")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📅 RSVP & Events")
        events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
        for i, e in enumerate(events):
            e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e["date"], e["start_time"]) < datetime.now()
            vote = next((r for r in st.session_state.data["rsvp"] if r['name'] == c_name and r['event_id'] == e_id), None)
            with st.expander(f"{'🔴 Past' if is_past else '🟢 Active'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Time:** {e['start_time']} - {e['end_time']}")
                if not is_past:
                    with st.form(f"rsvp_{i}"):
                        stat = st.radio("Attendance", ["Attending", "Not Attending", "Late"], index=0)
                        res = st.text_input("Reason", value=vote['reason'] if vote else "N/A")
                        if st.form_submit_button("Submit RSVP"):
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name']==c_name and r['event_id']==e_id)]
                            st.session_state.data["rsvp"].append({"event_id":e_id, "name":c_name, "status":stat, "reason":res})
                            save_data(); st.rerun()
                if vote: st.success(f"Confirmed: {vote['status']} ({vote['reason']})")
                if is_chair or (is_skit_rep and view_proj=="SKIT"):
                    st.write("**Responses:**")
                    st.table(pd.DataFrame([r for r in st.session_state.data["rsvp"] if r['event_id'] == e_id]))
    with col2:
        st.subheader("👥 Members")
        for m in [m for m in st.session_state.data["members"] if m["project"] == view_proj]:
            st.write(f"**{m['name']}** {'(REP)' if m['is_rep'] else ''}")
            st.caption(f"Role: {m['sub_role']}")

elif page == "Attendance":
    st.title("✅ Attendance Marking")
    events = [e for e in st.session_state.data["events"] if e["project"] == view_proj]
    if events:
        sel_ev = st.selectbox("Select Event", [f"{e['type']} - {e['date']}" for e in events])
        idx = [f"{e['type']} - {e['date']}" for e in events].index(sel_ev)
        e = events[idx]; e_id = f"{e['project']}_{e['date']}_{e['start_time']}"
        voted_names = [r['name'] for r in st.session_state.data["rsvp"] if r['event_id'] == e_id and r['status'] in ["Attending", "Late"]]
        can_mark = is_chair or is_teach or (is_skit_rep and view_proj=="SKIT")
        for name in voted_names:
            rec = st.session_state.data["attendance"].get(e_id, {}).get(name, {"present": False, "leave": "Full"})
            c1, c2, c3 = st.columns(3)
            c1.write(name)
            if can_mark:
                p = c2.checkbox("Present", value=rec["present"], key=f"p_{name}_{e_id}")
                l = c3.selectbox("Session", ["Full", "Half"], index=0 if rec["leave"]=="Full" else 1, key=f"l_{name}_{e_id}")
                if e_id not in st.session_state.data["attendance"]: st.session_state.data["attendance"][e_id] = {}
                st.session_state.data["attendance"][e_id][name] = {"present": p, "leave": l}
            else:
                c2.write("✅" if rec["present"] else "❌")
                c3.write(rec["leave"])
        if can_mark and st.button("Save Attendance"): save_data(); st.success("Updated")

elif page == "Activity Log":
    st.title("📝 Activity Reports")
    if is_chair or (is_skit_rep and view_proj == "SKIT") or (is_broch_rep and view_proj == "BROCHURE"):
        with st.expander("Add Entry"):
            with st.form("new_log"):
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
                    if st.button("Delete Log", key=f"del_{l['id']}"):
                        st.session_state.data["logs"] = [x for x in st.session_state.data["logs"] if x['id'] != l['id']]
                        save_data(); st.rerun()
                st.divider()
                for i, c in enumerate(l["comments"]):
                    st.caption(f"**{c['author']}**: {c['text']}")
                    if is_teach and c['author'] == c_name:
                        if st.button("Delete Comment", key=f"dc_{l['id']}_{i}"):
                            l["comments"].pop(i); save_data(); st.rerun()
                if is_teach:
                    with st.form(f"tc_{l['id']}"):
                        msg = st.text_input("Add Feedback")
                        if st.form_submit_button("Post"):
                            l["comments"].append({"author": c_name, "text": msg})
                            save_data(); st.rerun()

elif page == "Contribution Tracker":
    st.title("⏳ Time Management")
    if is_chair or (is_skit_rep and view_proj=="SKIT") or (is_broch_rep and view_proj=="BROCHURE"):
        with st.form("time"):
            names = [m["name"] for m in st.session_state.data["members"] if m["project"] == view_proj]
            target = st.selectbox("Member", names) if names else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Add Contribution"):
                curr = st.session_state.data["contributions"].get(target, 0)
                st.session_state.data["contributions"][target] = curr + (h*60) + m
                save_data(); st.rerun()
    t_list = [{"Name": m["name"], "Total": f"{st.session_state.data['contributions'].get(m['name'],0)//60}h {st.session_state.data['contributions'].get(m['name'],0)%60}m"} 
            for m in st.session_state.data["members"] if m["project"]==view_proj]
    if t_list: st.table(pd.DataFrame(t_list))

elif page == "Management Center" and is_chair:
    st.title("👑 Chairman Control")
    t1, t2, t3 = st.tabs(["Roster", "Schedule", "Accounts"])
    with t1:
        with st.form("m_man"):
            n, p = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"])
            r, s = st.checkbox("Representative"), st.selectbox("Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if p=="SKIT" else "Designer"
            if st.form_submit_button("Save"):
                st.session_state.data["members"] = [x for x in st.session_state.data["members"] if x['name'] != n]
                st.session_state.data["members"].append({"name": n, "project": p, "is_rep": r, "sub_role": s})
                save_data(); st.rerun()
        for i, m in enumerate(st.session_state.data["members"]):
            c1, c2 = st.columns([4, 1]); c1.write(f"{m['name']} ({m['project']})")
            if c2.button("Remove", key=f"rm_m_{i}"): st.session_state.data["members"].pop(i); save_data(); st.rerun()
    with t2:
        with st.form("e_man"):
            p, t, d = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            s, et, v = st.time_input("Start"), st.time_input("End"), st.text_input("Venue")
            if st.form_submit_button("Add Event"):
                st.session_state.data["events"].append({"project": p, "type": t, "date": d, "start_time": s, "end_time": et, "venue": v})
                save_data(); st.rerun()
        for i, ev in enumerate(st.session_state.data["events"]):
            if st.button(f"Cancel {ev['type']} ({ev['date']})", key=f"ce_{i}"): st.session_state.data["events"].pop(i); save_data(); st.rerun()
    with t3:
        st.subheader("System Accounts")
        accs = st.session_state.data.get("accounts", [])
        for i, acc in enumerate(accs):
            col_a, col_b = st.columns([4, 1])
            col_a.write(f"**{acc['name']}** ({acc['role']})")
            if col_b.button("Delete Account", key=f"del_acc_{i}"):
                st.session_state.data["accounts"].pop(i); save_data(); st.rerun()
