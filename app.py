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
                            st.session_state.data["
