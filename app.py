import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

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
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url, skipinitialspace=True)
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Clean status values strictly
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    return df.dropna(subset=['Timestamp']).sort_values('Timestamp')

def get_smart_status(row):
    # Strict check: Only "in use" gets a Red dot.
    if str(row['Status']) == "in use":
        return "🔴 IN USE"
    # Otherwise, check occupancy
    people = row['People'] if pd.notna(row['People']) else 0
    if people > 0:
        return f"🟡 OCCUPIED ({int(people)})"
    return "🟢 AVAILABLE"

# ==========================================
# MAIN APP ENGINE (EVERYTHING INSIDE FRAGMENT)
# ==========================================
@st.fragment(run_every="2m")
def sync_dashboard():
    df = load_data(SHEET_URL)
    
    # --- Sidebar (Now inside the fragment so it updates!) ---
    with st.sidebar:
        st.markdown("### ☁️ CITY OF LONDON")
        st.markdown(f"""
        <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center;">
            <h1 style="margin:0; font-size: 3rem; color: #ffffff;">18°C</h1>
            <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Cloudy</p>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown("### 🛠️ DASHBOARD CONTROL")
        st.info(f"Last Sync: {datetime.now().strftime('%H:%M:%S')}")
        st.success("Auto-Refresh: ACTIVE (2m)")
        if st.button("🔄 FORCE REFRESH", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # --- Main Content ---
    st.title("🏢 Neat London Showroom")
    
    tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

    with tab1:
        st.subheader("LIVE FLEET STATUS")
        latest = df.sort_values('Timestamp', ascending=False).drop_duplicates('Room').copy()
        latest['Live Status'] = latest.apply(get_smart_status, axis=1)
        st.dataframe(latest[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], 
                     column_config={"Humidity": st.column_config.ProgressColumn("Humidity", format="%d%%", min_value=0, max_value=100)},
                     hide_index=True, use_container_width=True)

    with tab2:
        c_room, c_date, c_grain = st.columns([1.5, 2, 1])
        with c_room: selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
        with c_date: date_range = st.date_input("SELECT DATE RANGE:", [datetime.now().date() - timedelta(days=7), datetime.now().date()])
        with c_grain: grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg"])

        f_df = df[df['Room'] == selected_room].copy()
        if len(date_range) == 2:
            start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
            f_df = f_df[(f_df['Timestamp'] >= start) & (f_df['Timestamp'] < end)]
        
        if not f_df.empty:
            f_df = f_df.set_index("Timestamp")
            rule = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D"}[grain]
            resampled = f_df.resample(rule).mean(numeric_only=True) if rule else f_df
            
            st.markdown("#### 👥 OCCUPANCY HISTORY")
            st.bar_chart(f_df["People"].resample(rule).max() if rule else f_df["People"], color="#aa00ff", height=180)
            
            r1_1, r1_2 = st.columns(2)
            with r1_1: st.line_chart(resampled["Temperature"], color="#b388ff")
            with r1_2: st.line_chart(resampled["Humidity"], color="#7c4dff")

# Start the app
sync_dashboard()
