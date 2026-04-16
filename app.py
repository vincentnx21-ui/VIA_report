import streamlit as st
import pandas as pd
from datetime import datetime, time
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Management", layout="wide")

# --- DATA PERSISTENCE ---
DATA_FILE = "via_report_data.json"

def save_data():
    data = st.session_state.data
    serializable = {
        "members": data["members"].to_dict(orient="records"),
        "logs": data["logs"],
        "contributions": data["contributions"],
        "rsvp": data["rsvp"],
        "events": []
    }
    for e in data["events"]:
        e_copy = e.copy()
        e_copy["date"] = e["date"].isoformat()
        e_copy["start_time"] = e["start_time"].strftime("%H:%M")
        e_copy["end_time"] = e["end_time"].strftime("%H:%M")
        serializable["events"].append(e_copy)
    with open(DATA_FILE, "w") as f:
        json.dump(serializable, f)

def load_data():
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

# --- INITIALIZATION ---
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
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Representative": "rep2026", "VIA members": "member2026", "Classmates": "class2026"
}

# --- AUTHENTICATION ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    role = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pw = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw == USER_CREDENTIALS[role]:
            st.session_state.logged_in, st.session_state.user_role = True, role
            st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()

# --- SIDEBAR ---
u_role = st.session_state.user_role
if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
nav = ["Dashboard", "Activity Log", "Contribution Tracker"]
if u_role == "Chairman": nav.append("Management Center")
page = st.sidebar.radio("Navigation", nav)

can_edit_reports = u_role in ["Chairman", "Representative"]

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📅 Events & Attendance")
        events = [e for e in st.session_state.data["events"] if e['project'] == view_proj]
        if not events: st.info("No events scheduled.")
        
        for idx, e in enumerate(events):
            e_id = f"{view_proj}_{e['date']}_{e['start_time']}"
            is_past = datetime.combine(e['date'], e['start_time']) < datetime.now()
            
            with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} @ {e['venue']}"):
                st.write(f"**Duration:** {e['start_time']} to {e['end_time']}")
                
                # RSVP Logic (Teachers and Members)
                if not is_past:
                    with st.form(f"rsvp_f_{idx}"):
                        m_list = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"].tolist()
                        if u_role == "Teacher": m_list.insert(0, "Teacher (Assigned)")
                        
                        r_name = st.selectbox("Select Your Name", m_list) if m_list else None
                        r_status = st.radio("Attendance", ["Attending", "Not Attending", "Late"])
                        r_reason = st.text_input("Reason (N/A if Attending)")
                        if st.form_submit_button("Submit RSVP") and r_name:
                            st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name'] == r_name and r['event_id'] == e_id)]
                            st.session_state.data["rsvp"].append({"event_id": e_id, "name": r_name, "status": r_status, "reason": r_reason})
                            save_data(); st.success("RSVP Saved!"); st.rerun()

                # Display Responses
                resps = [r for r in st.session_state.data.get("rsvp", []) if r.get("event_id") == e_id]
                if resps: st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                else: st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Team")
        proj_m = st.session_state.data["members"][st.session_state.data["members"]['Project'] == view_proj]
        if view_proj == "SKIT":
            for sr in ["Actors", "Prop makers", "Cameraman"]:
                names = proj_m[proj_m['SubRole'] == sr]['Name'].tolist()
                if names: st.write(f"**{sr}:** {', '.join(names)}")
        else:
            names = proj_m['Name'].tolist()
            if names: st.write(f"**Members:** {', '.join(names)}")

# --- ACTIVITY LOG & CONTRIBUTIONS ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Activity Log")
    if can_edit_reports:
        with st.form("log_entry"):
            l_date, l_type = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("Progress Report")
            if st.form_submit_button("Save"):
                st.session_state.data["logs"].append({"Project": view_proj, "Date": str(l_date), "Type": l_type, "Desc": l_desc})
                save_data(); st.rerun()
    for l in reversed([l for l in st.session_state.data["logs"] if l["Project"] == view_proj]):
        with st.expander(f"{l['Date']} - {l['Type']}"): st.write(l["Desc"])

elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time Tracker")
    if can_edit_reports:
        with st.form("time_f"):
            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
            target = st.selectbox("Member", names) if not names.empty else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record") and target:
                st.session_state.data["contributions"].append({"Project": view_proj, "Name": target, "Time": f"{h}h {m}m"})
                save_data(); st.rerun()
    c_list = [c for c in st.session_state.data["contributions"] if c["Project"] == view_proj]
    if c_list: st.table(pd.DataFrame(c_list))

# --- MANAGEMENT CENTER (CHAIRMAN ONLY) ---
elif page == "Management Center":
    st.title("👑 Chairman Management Center")
    t1, t2 = st.tabs(["Member Management", "Event Management"])

    with t1:
        st.subheader("Add/Edit Members")
        with st.form("add_mem"):
            n, p, r = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Role", ["Member", "Representative"])
            sr = st.selectbox("Sub-Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if p=="SKIT" else "N/A"
            if st.form_submit_button("Add Member"):
                new_m = pd.DataFrame([{"Name": n, "Project": p, "Role": r, "SubRole": sr}])
                st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                save_data(); st.rerun()

        st.write("---")
        # Edit/Delete Members
        df = st.session_state.data["members"]
        if not df.empty:
            for i, row in df.iterrows():
                cols = st.columns([3, 2, 2, 2, 1])
                new_name = cols[0].text_input("Name", row['Name'], key=f"mn_{i}")
                cols[1].write(row['Project'])
                cols[2].write(row['Role'])
                if cols[4].button("🗑️", key=f"mdel_{i}"):
                    st.session_state.data["members"] = df.drop(i)
                    save_data(); st.rerun()
                if new_name != row['Name']:
                    st.session_state.data["members"].at[i, 'Name'] = new_name
                    save_data(); st.toast("Name updated!")

    with t2:
        st.subheader("Schedule/Modify Events")
        with st.form("ev_sch"):
            ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.radio("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
            c1, c2, c3 = st.columns(3)
            ts, te, ev = c1.time_input("Start"), c2.time_input("End"), c3.text_input("Venue")
            if st.form_submit_button("Create Event") and ev:
                st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": ts, "end_time": te, "venue": ev})
                save_data(); st.rerun()

        st.write("---")
        for i, ev in enumerate(st.session_state.data["events"]):
            c = st.columns([2, 2, 2, 2, 2, 1])
            c[0].write(ev['project'])
            c[1].write(ev['date'])
            c[2].write(ev['type'])
            new_venue = c[3].text_input("Venue", ev['venue'], key=f"ev_v_{i}")
            if c[5].button("❌", key=f"ev_del_{i}"):
                st.session_state.data["events"].pop(i)
                save_data(); st.rerun()
            if new_venue != ev['venue']:
                st.session_state.data["events"][i]['venue'] = new_venue
                save_data(); st.toast("Venue Updated!")
