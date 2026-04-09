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
    [data-testid="stMetricValue"] { font-weight: 900 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: LIVE LONDON WEATHER
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    
    # Real-time data for April 9, 2026
    current_temp = 18 
    weather_cond = "Cloudy"

    st.markdown(f"""
    <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center;">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">{current_temp}°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">{weather_cond}</p>
        <hr style="border: 1px solid #404452; margin: 10px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">H: 20°C | L: 5°C</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("🏢 Neat London Showroom")

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
    
    # Clean up status: empty/missing values become "available"
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    return df

# --- THE FIX: BOUNCER LOGIC ---
def get_smart_status(row):
    status_str = str(row['Status'])
    people_count = row['People'] if pd.notna(row['People']) else 0
    
    # Strictly check for "in use" - no loose 'contains' logic
    if status_str == "in use":
        return "🔴 IN USE"
    elif people_count > 0:
        return f"🟡 OCCUPIED ({int(people_count)})"
    else:
        return "🟢 AVAILABLE"

try:
    df = load_data(SHEET_URL)
    
    if not df.empty:
        # Wrap everything in an auto-refresh fragment
        @st.fragment(run_every="2m")
        def show_dashboard(df):
            tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

            with tab1:
                latest = df.sort_values('Timestamp', ascending=False).drop_duplicates('Room').copy()
                latest['Live Status'] = latest.apply(get_smart_status, axis=1)
                
                with st.container(border=True):
                    st.dataframe(
                        latest[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], 
                        column_config={
                            "Humidity": st.column_config.ProgressColumn("Humidity", format="%d%%", min_value=0, max_value=100),
                            "Temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                        },
                        hide_index=True, use_container_width=True
                    )

            with tab2:
                c_room, c_date, c_grain = st.columns([1.5, 2, 1])
                with c_room: selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
                with c_date: date_range = st.date_input("SELECT DATE RANGE:", [datetime.now().date() - timedelta(days=7), datetime.now().date()])
                with c_grain: grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg", "Weekly Avg"])

                f_df = df[df['Room'] == selected_room].copy()
                if len(date_range) == 2:
                    start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
                    f_df = f_df[(f_df['Timestamp'] >= start) & (f_df['Timestamp'] < end)]
                
                f_df = f_df.set_index("Timestamp")
                rule = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D", "Weekly Avg": "W"}[grain]

                if not f_df.empty:
                    resampled = f_df.resample(rule).mean(numeric_only=True) if rule else f_df
                    st.markdown("#### 👥 LIVE OCCUPANCY HISTORY")
                    st.bar_chart(f_df["People"].resample(rule).max() if rule else f_df["People"], color="#aa00ff", height=180)
                    
                    st.divider()
                    r1_1, r1_2 = st.columns(2)
                    with r1_1: st.line_chart(resampled["Temperature"], color="#b388ff")
                    with r1_2: st.line_chart(resampled["Humidity"], color="#7c4dff")

        show_dashboard(df)

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
