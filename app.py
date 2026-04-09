import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- Page Config ---
st.set_page_config(page_title="Neat London Showroom", layout="wide", page_icon="🏢")

# ==========================================
# FORCED DARK MODE & CHUNKY STYLE
# ==========================================
st.markdown("""
<style>
    html, body, [class*="ViewContainer"] { color: #f0f2f6 !important; }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial Black', 'Impact', sans-serif !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        text-transform: uppercase;
    }
    [data-testid="stMetric"] {
        background-color: #2d303a !important;
        border: 2px solid #9c27b0 !important;
        border-radius: 15px !important;
        padding: 15px !important;
    }
    [data-testid="stMetricValue"] { font-weight: 900 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING (Global) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url, skipinitialspace=True)
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Room'] = df['Room'].astype(str).str.strip()
    df['Status'] = df['Status'].astype(str).str.strip().str.lower()
    return df.dropna(subset=['Timestamp']).sort_values('Timestamp')

def get_smart_status(row):
    check_val = str(row['Status'])
    people = row['People'] if pd.notna(row['People']) else 0
    if "in use" in check_val: return "🔴 IN USE"
    elif people > 0: return f"🟡 OCCUPIED ({int(people)})"
    else: return "🟢 AVAILABLE"

# ==========================================
# SIDEBAR: LIVE WEATHER & AUTO-REFRESH STATUS
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    try:
        weather_df = pd.read_json("https://api.open-meteo.com/v1/forecast?latitude=51.5074&longitude=-0.1278&current_weather=true")
        temp = int(weather_df['current_weather']['temperature'])
    except: temp = 16

    st.markdown(f"""
    <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center;">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">{temp}°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Real-Time Feed</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    st.caption(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
    st.success("Auto-Refresh: ON (2min)")
    
    if st.button("🔄 FORCE REFRESH", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("🏢 Neat London Showroom")

# ==========================================
# THE AUTO-REFRESH FRAGMENT
# ==========================================
@st.fragment(run_every="2m") # This tells Streamlit to rerun this function every 2 minutes
def main_dashboard():
    try:
        df = load_data(SHEET_URL)
        if not df.empty:
            tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

            with tab1:
                latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
                latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
                with st.container(border=True):
                    st.dataframe(latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], 
                                 column_config={"Humidity": st.column_config.ProgressColumn("Humidity", format="%d%%", min_value=0, max_value=100)},
                                 hide_index=True, use_container_width=True)

            with tab2:
                c_room, c_date, c_grain = st.columns([1.5, 2, 1])
                with c_room: selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
                with c_date: date_range = st.date_input("SELECT DATE RANGE:", [datetime.now().date() - timedelta(days=7), datetime.now().date()])
                with c_grain: grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg", "Weekly Avg"])

                f_df = df[df['Room'] == selected_room].copy()
                if len(date_range) == 2:
                    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1
