import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="VIA Project Portal", layout="wide")

# --- DATA PERSISTENCE HELPERS ---
DATA_FILE = "via_data.json"

def save_data():
    """Saves the current session state data to a JSON file."""
    data_to_save = {
        "members": st.session_state.data["members"].to_dict(orient="records"),
        "logs": st.session_state.data["logs"],
        "contributions": st.session_state.data["contributions"],
        "rsvp": st.session_state.data["rsvp"],
        "events": []
    }
    for e in st.session_state.data["events"]:
        event_copy = e.copy()
        event_copy["date"] = e["date"].isoformat()
        event_copy["start_time"] = e["start_time"].strftime("%H:%M:%S")
        event_copy["end_time"] = e["end_time"].strftime("%H:%M:%S")
        data_to_save["events"].append(event_copy)
        
    with open(DATA_FILE, "w") as f:
        json.dump(data_to_save, f)

def load_data():
    """Loads data from the JSON file and restores types."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                raw = json.load(f)
                
                # --- SELF-HEALING: Check for missing keys to prevent KeyError ---
                if "rsvp" not in raw: raw["rsvp"] = []
                if "members" not in raw: raw["members"] = []
                if "logs" not in raw: raw["logs"] = []
                if "contributions" not in raw: raw["contributions"] = []
                if "events" not in raw: raw["events"] = []

                raw["members"] = pd.DataFrame(raw["members"])
                for e in raw["events"]:
                    e["date"] = datetime.strptime(e["date"], "%Y-%m-%d").date()
                    e["start_time"] = datetime.strptime(e["start_time"], "%H:%M:%S").time()
                    e["end_time"] = datetime.strptime(e["end_time"], "%H:%M:%S").time()
                return raw
        except Exception as e:
            return None
    return None

# --- INITIALIZE SESSION STATE ---
if 'data' not in st.session_state:
    saved = load_data()
    if saved:
        st.session_state.data = saved
    else:
        st.session_state.data = {
            "members": pd.DataFrame(columns=["Name", "Project", "Role", "SubRole"]),
            "logs": [],
            "contributions": [],
            "events": [],
            "rsvp": []
        }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- PASSWORDS ---
USER_CREDENTIALS = {
    "Teacher": "teach2026", "Chairman": "chair2026", "VIA Committee": "comm2026",
    "Representative": "rep2026", "VIA members": "member2026", "Classmates": "class2026"
}

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 VIA Project Portal Login")
    role_choice = st.selectbox("Select Role", list(USER_CREDENTIALS.keys()))
    pw_choice = st.text_input("Password", type="password")
    if st.button("Login"):
        if pw_choice == USER_CREDENTIALS[role_choice]:
            st.session_state.logged_in = True
            st.session_state.user_role = role_choice
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()

# --- GLOBALS ---
u_role = st.session_state.user_role
is_chairman = (u_role == "Chairman")
is_rep = (u_role == "Representative")
is_teacher = (u_role == "Teacher")
can_edit = u_role in ["Chairman", "Representative"]

if st.sidebar.button("🔓 Logout"):
    st.session_state.logged_in = False
    st.rerun()

st.sidebar.write("---")
view_proj = st.sidebar.radio("Project View", ["SKIT", "BROCHURE"])
page = st.sidebar.radio("Navigation", ["Dashboard", "Activity Log", "Contribution Tracker", "Management Center"])

# --- DASHBOARD ---
if page == "Dashboard":
    st.title(f"🚀 {view_proj} Dashboard")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📅 Events & Attendance")
        p_events = [e for e in st.session_state.data["events"] if e['project'] == view_proj]
        
        if not p_events:
            st.info("No events scheduled yet.")
        else:
            for i, e in enumerate(p_events):
                # We use a safer ID for RSVPs
                event_id = f"{view_proj}_{e['date']}_{e['start_time']}"
                event_dt = datetime.combine(e['date'], e['start_time'])
                is_past = event_dt < datetime.now()
                
                with st.expander(f"{'🔴' if is_past else '🟢'} {e['type']} - {e['date']} ({e['venue']})"):
                    st.write(f"**Time:** {e['start_time'].strftime('%H:%M')} - {e['end_time'].strftime('%H:%M')}")
                    
                    if not is_past and not is_teacher:
                        with st.form(key=f"f_rsvp_{i}"):
                            m_names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
                            res_name = st.selectbox("Name", m_names) if not m_names.empty else None
                            res_status = st.radio("Status", ["Attending", "Not Attending", "Late"])
                            res_reason = st.text_input("Reason (N/A if Attending)")
                            if st.form_submit_button("Submit RSVP") and res_name:
                                # Remove old RSVP if exists and add new
                                st.session_state.data["rsvp"] = [r for r in st.session_state.data["rsvp"] if not (r['name'] == res_name and r['event_id'] == event_id)]
                                st.session_state.data["rsvp"].append({
                                    "event_id": event_id, "name": res_name, "status": res_status, "reason": res_reason
                                })
                                save_data()
                                st.success("RSVP Submitted!")
                                st.rerun()

                    # Responses Section
                    st.write("**Responses:**")
                    # Safe retrieval of RSVP list
                    rsvp_list = st.session_state.data.get("rsvp", [])
                    resps = [r for r in rsvp_list if r.get("event_id") == event_id]
                    if resps:
                        st.table(pd.DataFrame(resps)[["name", "status", "reason"]])
                    else:
                        st.caption("No responses yet.")

    with col2:
        st.subheader("👥 Team")
        proj_m = st.session_state.data["members"][st.session_state.data["members"]['Project'] == view_proj]
        if view_proj == "SKIT":
            for sr in ["Actors", "Prop makers", "Cameraman"]:
                names = proj_m[proj_m['SubRole'] == sr]['Name'].tolist()
                if names: st.write(f"**{sr}:** {', '.join(names)}")
        else:
            m_list = proj_m['Name'].tolist()
            if m_list: st.write(f"**Members:** {', '.join(m_list)}")

# --- LOGS & CONTRIBUTION (Omitted for brevity, but same as previous working version) ---
elif page == "Activity Log":
    st.title(f"📝 {view_proj} Logs")
    if can_edit:
        with st.form("log_entry"):
            l_date, l_type = st.date_input("Date"), st.selectbox("Type", ["Discussion", "Rehearsal"])
            l_desc = st.text_area("Progress Report")
            if st.form_submit_button("Save"):
                st.session_state.data["logs"].append({"Project": view_proj, "Date": str(l_date), "Type": l_type, "Desc": l_desc})
                save_data(); st.rerun()
    for l in reversed([l for l in st.session_state.data["logs"] if l["Project"] == view_proj]):
        with st.expander(f"{l['Date']} - {l['Type']}"): st.write(l["Desc"])

elif page == "Contribution Tracker":
    st.title(f"⏳ {view_proj} Time")
    if can_edit:
        with st.form("time_entry"):
            names = st.session_state.data["members"][st.session_state.data["members"]["Project"] == view_proj]["Name"]
            target = st.selectbox("Member", names) if not names.empty else None
            h, m = st.number_input("Hours", 0), st.number_input("Minutes", 0, 59)
            if st.form_submit_button("Record") and target:
                st.session_state.data["contributions"].append({"Project": view_proj, "Name": target, "Time": f"{h}h {m}m"})
                save_data(); st.rerun()
    c_list = [c for c in st.session_state.data["contributions"] if c["Project"] == view_proj]
    if c_list: st.table(pd.DataFrame(c_list))

# --- MANAGEMENT ---
elif page == "Management Center":
    if is_chairman:
        st.title("👑 Management")
        t1, t2 = st.tabs(["Roster", "Schedule"])
        with t1:
            with st.form("add_mem"):
                n, p, r = st.text_input("Name"), st.selectbox("Project", ["SKIT", "BROCHURE"]), st.selectbox("Role", ["Member", "Representative"])
                sr = st.selectbox("SKIT Role", ["Actors", "Prop makers", "Cameraman", "N/A"]) if p=="SKIT" else "N/A"
                if st.form_submit_button("Add"):
                    new_m = pd.DataFrame([{"Name": n, "Project": p, "Role": r, "SubRole": sr}])
                    st.session_state.data["members"] = pd.concat([st.session_state.data["members"], new_m], ignore_index=True)
                    save_data(); st.rerun()
            st.dataframe(st.session_state.data["members"])
        with t2:
            with st.form("event_sch"):
                ep, et, ed = st.selectbox("Project", ["SKIT", "BROCHURE"]), st.radio("Type", ["Discussion", "Rehearsal"]), st.date_input("Date")
                col1, col2 = st.columns(2)
                ts, te, ev = col1.time_input("Start"), col2.time_input("End"), st.text_input("Venue")
                if st.form_submit_button("Schedule") and ev:
                    st.session_state.data["events"].append({"project": ep, "type": et, "date": ed, "start_time": ts, "end_time": te, "venue": ev})
                    save_data(); st.rerun()
    else:
        st.error("Restricted to Chairman.")
