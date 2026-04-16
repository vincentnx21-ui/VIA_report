import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Class Report Portal", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_database.json"

def save_data():
    """Converts session data to JSON and saves to disk."""
    data_to_save = {
        "members": st.session_state.data["members"].to_dict(orient="records"),
        "logs": st.session_state.data["logs"],
        "contributions": st.session_state.data["contributions"],
        "rsvp": st.session_state.data["rsvp"],
        "events": []
    }
    for e in st.session_state.data["events"]:
        e_copy = e.copy()
        e_copy["date"] = e["date"].isoformat()
        e_copy["start_time"] = e["start_time"].strftime("%H:%M")
        e_copy["end_time"] = e["end_time"].strftime("%H:%M")
        data_to_save["events"].append(e_copy)
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f)

def load_data():
    """Loads JSON data and heals missing keys."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                for key in ["members", "logs", "contributions", "rsvp", "events"]:
                    if key not in raw: raw[key] = []
                raw["members"] = pd.DataFrame(raw["members"])
                for e in raw["events"]:
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M").time()
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M").time()
                return raw
        except: return None
    return None

# --- SESSION INITIALIZATION ---
if 'data' not in st.session_state:
    loaded = load_data()
    st.session_state.data = loaded if loaded else {
        "members": pd.DataFrame(columns=["Name", "Project", "Role", "SubRole"]),
        "logs": [], "contributions": [], "events": [], "rsvp": []
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026",
    "Chairman": "chair2026",
    "VIA Committee": "comm2026",
    "Skit Representative": "skitrep2026",
    "Brochure Representative": "brochurerep2026",
    "VIA members": "member2026",
    "Classmates": "class2026"
}

# --- LOGIN / LOGOUT ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal")
    role = st.selectbox("Role", list(USER_CREDENTIALS.keys()))
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == USER_CREDENTIALS[role]:
            st.session_state.logged_in, st.session_state.user_role = True, role
            st.rerun()
        else: st.error("Wrong password.")
    st.stop()

# --- GLOBALS & PERMISSIONS ---
u_role = st.session_state.user_role
is_chairman = (u_role == "Chairman")
is_skit_rep = (u_role == "Skit Representative")
is_brochure_rep = (u_role == "Brochure Representative")
is_teacher = (u_role == "Teacher")

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])

# Navigation Logic
nav_options = ["Dashboard", "Activity Log", "Contribution Tracker"]
if is_chairman: nav_options.append("Management Center")
page = st.sidebar.radio("Navigation", nav_options)

# --- DASHBOARD (Events & RSVP) ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events & Attendance")
        # Brochure Rep doesn't see events as per instruction
        if is_brochure_rep:
            st.info("Brochure Representative view: Events are managed by Skit/Chairman.")
        else:
            events = [e for e in st.session_state.data["events"] if e['project'] == view_proj]
            for i, e in enumerate(events):
                e_id = f"{view_proj}_{e['date']}_{e['start_time']}"
                is_past = datetime.combine(e['date'], e['start_time']) < datetime.now()
                
                with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                    st.write(f"**Time:** {e['start_time']} to {e['end_time']}")
                    
                    # RSVP Logic (Teachers, Skit Reps, and Members can vote)
                    if not is_past:
                        with st.form(f"rsvp_{i}"):
                            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"].tolist()
                            if is_teacher: names.append("Teacher (Self)")
                            if is_skit_rep: names.append("Skit Rep (Self)")
                            
                            r_name = st.selectbox("Select Name", names) if names else None
                            r_status = st.radio("Attendance", ["Attending", "Not Attending", "Late"])
                            r_reason = st.text_input("Reason (N/A if Attending)")
                            if st.form_submit_button("Submit Vote") and r_name:
                                st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name'] == r_name and r['event_id'] == e_id)]
                                st.session_state.data["rsvp"].append({"event_id": e_id, "name": r_name, "status": r_status, "reason": r_reason})
                                save_data(); st.success("Vote Saved!"); st.rerun()

                    # Chairman Response View
                    if is_chairman:
                        st.write("**Responses (Visible to Chairman Only):**")
                        resps = [r for r in st.session_state.data["rsvp"] if r["event_id"] == e_id]
                        if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    
                    # Chairman Event Management
                    if is_chairman and not is_past:
                        if st.button(f"Cancel Event {i}", key=f"del_ev_{i}"):
                            st.session_state.data["events"].pop(i)
                            save_data(); st.rerun()

    with col2:
        st.subheader("👥 Project Members")
        m_df = st.session_state.data["members"]
        proj_m = m_df[m_df['Project'] == view_proj]
        if view_proj == "SKIT":
            for sr in ["Actors", "Prop makers", "Cameraman"]:
                names = proj_m[proj_m['SubRole'] == sr]['Name'].tolist()
                if names: st.write(f"**{sr}:** {', '.join(names)}")
        else:
            st.write("**Members:** " + ", ".join(proj_m['Name'].tolist()))

# --- ACTIVITY LOG ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    # Allowed to add reports: Chairman and both Reps
    if is_chairman or is_skit_rep or is_brochure_rep:
        with st.form("log_f"):
            l_date = st.date_input("Date")
            l_type = st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("What was accomplished?")
            if st.form_submit_button("Add Report"):
                st.session_state.data["logs"].append({"Project": view_proj, "Date": str(l_date), "Type": l_type, "Desc": l_desc})
                save_data(); st.rerun()
    
    for l in reversed([l for l in st.session_state.data["logs"] if l["Project"] == view_proj]):
        with st.expander(f"{l['Date']} - {l['Type']}"): st.write(l["Desc"])

# --- CONTRIBUTION TRACKER ---
elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    
    # Specific logic for Reps
    allow_contrib = False
    if is_chairman: allow_contrib = True
    if is_skit_rep and view_proj == "SKIT": allow_contrib = True
    if is_brochure_rep and view_proj == "BROCHURE": allow_contrib = True

    if allow_contrib:
        with st.form("contrib_f"):
            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
            target = st.selectbox("Select Member", names) if not names.empty else None
            h = st.number_input("Hours", 0, 24)
            m = st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Log Time") and target:
                st.session_state.data["contributions"].append({"Project": view_proj, "Name": target, "Time": f"{h}h {m}m"})
                save_data(); st.rerun()

    c_list = [c for c in st.session_state.data["contributions"] if c["Project"] == view_proj]
    if c_list: st.table(pd.DataFrame(c_list))

# --- MANAGEMENT CENTER (Chairman Only) ---
elif page == "Management Center" and is_chairman:
    st.title("👑 Chairman Management Center")
    t1, t2 = st.tabs(["Member Management", "Event Scheduler"])

    with t1:
        st.subheader("Add/Edit Members")
        with st.form("mem_f"):
            n = st.text_input("Name")
            p = st.selectbox("Project", ["SKIT", "BROCHURE"])
            r = st.selectbox("Role", ["Member", "Representative"])
            sr = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if p == "SKIT" else "N/A"
            if st.form_submit_button("Register Member"):
                new_m = pd.DataFrame([{"Name": n, "Project": p, "Role": r, "SubRole": sr}])
                st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                save_data(); st.rerun()
        
        st.write("---")
        # Edit/Delete logic
        for i, row in st.session_state.data["members"].iterrows():
            cols = st.columns([3, 2, 2, 1])
            new_name = cols[0].text_input(f"Name {i}", row['Name'], label_visibility="collapsed")
            cols[1].write(f"{row['Project']} - {row['Role']}")
            if cols[2].button("Update", key=f"upd_{i}"):
                st.session_state.data["members"].at[i, 'Name'] = new_name
                save_data(); st.rerun()
            if cols[3].button("🗑️", key=f"del_mem_{i}"):
                st.session_state.data["members"] = st.session_state.data["members"].drop(i)
                save_data(); st.rerun()

    with t2:
        st.subheader("Schedule Meeting/Rehearsal")
        with st.form("ev_f"):
            ep = st.selectbox("Target Project", ["SKIT", "BROCHURE"])
            et = st.radio("Event Type", ["Discussion", "Rehearsal"])
            ed = st.date_input("Date")
            col_t1, col_t2 = st.columns(2)
            ts = col_t1.time_input("Start Time")
            te = col_t2.time_input("End Time")
            ev = st.text_input("Venue")
            if st.form_submit_button("Post Event") and ev:
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": ts, "end_time": te, "venue": ev})
                save_data(); st.rerun()
