import os
# Forces Streamlit to bypass the unstable PyArrow engine entirely
os.environ["STREAMLIT_DATA_FRAME_SERIALIZATION"] = "legacy"

import streamlit as st
import pandas as pd
import altair as alt
import requests
import time
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Neat London Showroom", layout="wide", page_icon="🏢")

# --- Initialize Kiosk State ---
if 'kiosk_idx' not in st.session_state:
    st.session_state.kiosk_idx = 0

# ==========================================
# 1. STYLING & GLASSMORPHISM
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700;900&display=swap');
    html, body, [class*="ViewContainer"], h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        font-family: 'Outfit', sans-serif !important;
        color: #f0f2f6;
    }
    .stApp {
        background: linear-gradient(-45deg, #0e1117, #1a1025, #0f172a, #0e1117);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    h1, h2, h3, h4, h5, h6 { font-weight: 900 !important; color: #ffffff !important; letter-spacing: 1px; }
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    div[data-baseweb="tab-list"] { gap: 15px; padding-top: 20px !important; padding-bottom: 25px !important; }
    button[data-baseweb="tab"] {
        background: rgba(45, 48, 58, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important; padding: 12px 25px !important; color: #a0a5b5 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] { background: rgba(156, 39, 176, 0.8) !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. API LOGIC
# ==========================================
PULSE_ORG_ID = "YOUR_ORGANIZATION_ID"
PULSE_API_KEY = "YOUR_API_KEY"

ENDPOINT_MAP = {
    "Boardroom": "paste-endpoint-id-here",
    "Front Booth": "paste-endpoint-id-here",
    "Huddle Space": "paste-endpoint-id-here",
    "Harris": "6e0f6d6b-97a5-4c2d-8c8d-286e71ea02cc"
}

def send_pulse_reboot(room_name):
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id: return False, "No Endpoint ID mapped."
    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/reboot"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Content-Type": "application/json"}
    try:
        requests.post(api_url, headers=headers).raise_for_status() 
        return True, f"Rebooted {room_name}."
    except Exception as e: return False, str(e)

def apply_neat_config(room_name, config_payload):
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id: return False, "No Endpoint ID mapped."
    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/config"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Content-Type": "application/json"}
    try:
        requests.post(api_url, headers=headers, json={"deviceConfig": config_payload}).raise_for_status() 
        return True, f"Config applied to {room_name}."
    except Exception as e: return False, str(e)

# ==========================================
# 3. DATA LOADING & HELPERS
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url, skipinitialspace=True)
    if len(df.columns) >= 8: df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]: df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    return df.dropna(subset=['Timestamp']).sort_values('Timestamp')

@st.cache_data(ttl=900) 
def get_live_weather():
    try:
        data = requests.get("https://api.open-meteo.com/v1/forecast?latitude=51.5074&longitude=-0.1278&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FLondon", timeout=5).json()
        w_map = {0: "Clear Sky ☀️", 1: "Mainly Clear 🌤️", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️", 61: "Light Rain ☔", 63: "Rain ☔", 65: "Heavy Rain ☔"}
        return round(data['current']['temperature_2m']), w_map.get(data['current']['weather_code'], "Cloudy ☁️"), round(data['daily']['temperature_2m_max'][0]), round(data['daily']['temperature_2m_min'][0])
    except: return 18, "Cloudy ☁️", 20, 5

def get_smart_status(row):
    if str(row['Status']) == "in use": return "🔴 IN USE"
    if pd.notna(row['People']) and row['People'] > 0: return f"🟡 OCCUPIED ({int(row['People'])})"
    return "🟢 AVAILABLE"

def render_smart_card(label, value, color="#9c27b0"):
    return f'<div style="background: rgba(45,48,58,0.4); border-left: 4px solid {color}; border-radius: 15px; padding: 20px; margin-bottom: 15px;"><p style="margin:0; font-size: 0.85rem; color: #a0a5b5;">{label}</p><h2 style="margin:0; color: {color};">{value}</h2></div>'

def create_interactive_chart(data, y_col, color, chart_type='line', y_scale_zero=False):
    base = alt.Chart(data).encode(
        x=alt.X('Timestamp:T', title=''),
        y=alt.Y(f'{y_col}:Q', title='', scale=alt.Scale(zero=y_scale_zero)),
        tooltip=['Timestamp:T', f'{y_col}:Q']
    )
    chart = (base.mark_area(opacity=0.3, color=color) + base.mark_line(color=color)) if chart_type == 'line' else base.mark_area(color=color, opacity=0.8, interpolate='step-after')
    return chart.interactive().configure_view(strokeWidth=0)

global_df = load_data(SHEET_URL)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    curr_t, w_desc, high_t, low_t = get_live_weather()
    st.markdown(f'<div style="background: rgba(45,48,58,0.4); border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;"><h1 style="margin:0;">{curr_t}°C</h1><p style="color:#9c27b0; font-weight:700;">{w_desc}</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    st.toggle("▶️ ENABLE AUTO-PILOT (Kiosk Mode)", key="autopilot")
    if st.button("🔄 FORCE FULL REFRESH", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. DASHBOARD ENGINE
# ==========================================
st.title("🏢 Neat London Showroom")
if not global_df.empty:
    tab1, tab2, tab3 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE", "🤖 AI ASSISTANT"])

    with tab1:
        latest = global_df.sort_values('Timestamp', ascending=False).drop_duplicates('Room').copy()
        latest['Live Status'] = latest.apply(get_smart_status, axis=1)
        h1, h2, h3 = st.columns(3)
        h1.markdown(render_smart_card("TOTAL PEOPLE", f"{int(latest['People'].sum())} 👥"), unsafe_allow_html=True)
        h2.markdown(render_smart_card("AVAILABLE ROOMS", f"{(latest['Live Status'] == '🟢 AVAILABLE').sum()} 🟢"), unsafe_allow_html=True)
        h3.markdown(render_smart_card("AVG VOC", f"{latest['VOC Index'].mean():.0f} 🌬️", "#ff4b4b" if latest['VOC Index'].mean() > 250 else "#9c27b0"), unsafe_allow_html=True)

    with tab2:
        all_rooms = sorted(global_df['Room'].unique())
        c_room, c_date, c_grain = st.columns([1.5, 2, 1])
        with c_room: selected_room = st.selectbox("ROOM:", all_rooms, index=st.session_state.kiosk_idx, disabled=st.session_state.get('autopilot', False))
        with c_date: date_range = st.date_input("DATE:", [datetime.now().date() - timedelta(days=7), datetime.now().date()])
        with c_grain: grain = st.selectbox("RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg"])

        f_df = global_df[global_df['Room'] == selected_room].copy()
        if len(date_range) == 2 and not f_df.empty:
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
            f_df = f_df[(f_df['Timestamp'] >= start) & (f_df['Timestamp'] < end)].set_index("Timestamp")
            
            rule = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D"}[grain]
            env_chart_df = (f_df.resample(rule).mean(numeric_only=True) if rule else f_df).reset_index()
            
            latest_val = f_df.iloc[-1]
            st.divider()
            r1_1, r1_2 = st.columns(2)
            with r1_1:
                st.markdown("#### TEMPERATURE (°C)")
                st.altair_chart(create_interactive_chart(env_chart_df, 'Temperature', '#b388ff', 'line').properties(height=220), use_container_width=True)
            with r1_2:
                st.markdown("#### AIR QUALITY (VOC)")
                st.altair_chart(create_interactive_chart(env_chart_df, 'VOC Index', '#651fff', 'line', y_scale_zero=True).properties(height=220), use_container_width=True)

    with tab3:
        st.markdown("### 💬 Chat with the Showroom")
        if "messages" not in st.session_state: st.session_state.messages = [{"role": "assistant", "content": "Ask me about room utilization or air quality!"}]
        for msg in st.session_state.messages: st.chat_message(msg["role"]).markdown(msg["content"])
        if prompt := st.chat_input("Ask a question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.chat_message("user").markdown(prompt)
            response = "I'm a simple AI! Try asking about 'utilization' or 'air'."
            if "utiliz" in prompt.lower(): response = f"Most used room is **{global_df.groupby('Room')['People'].sum().idxmax()}**."
            st.chat_message("assistant").markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# ==========================================
# 6. AUTO-PILOT LOOP
# ==========================================
if st.session_state.get('autopilot', False):
    time.sleep(10)
    all_rms = sorted(global_df['Room'].unique()) if not global_df.empty else []
    if all_rms: st.session_state.kiosk_idx = (st.session_state.kiosk_idx + 1) % len(all_rms)
    st.rerun()
