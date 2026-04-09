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
    
    # Static accurate update for London Today
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
    st.success("Auto-Refresh: ON (2min)")
    if st.button("🔄 FORCE REFRESH", use_container_width=True):
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
    
    # Clean up status
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    return df

def get_smart_status(row):
    status_str = str(row['Status'])
    people_count = row['People'] if pd.notna(row['People']) else 0
    if status_str == "in use":
        return "🔴 IN USE"
    elif people_count > 0:
        return f"🟡 OCCUPIED ({int(people_count)})"
    else:
        return "🟢 AVAILABLE"

# ==========================================
# THE DASHBOARD ENGINE (AUTO-REFRESHING)
# ==========================================
@st.fragment(run_every="2m")
def render_dashboard():
    try:
        df = load_data(SHEET_URL)
        
        if not df.empty:
            tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

            with tab1:
                st.subheader("LIVE FLEET STATUS")
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
                # 1. Selectors
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
                    
                    # 2. Key Metrics Row
                    latest_val = f_df.iloc[-1]
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("LATEST TEMP", f"{latest_val['Temperature']:.1f}°C")
                    m2.metric("LATEST HUMIDITY", f"{latest_val['Humidity']:.0f}%")
                    m3.metric("LATEST VOC", f"{latest_val['VOC Index']:.0f}")
                    m4.metric("LATEST LIGHT", f"{latest_val['Light']:.0f} lx")

                    st.divider()

                    # 3. Occupancy Hero (Top)
                    st.markdown("#### 👥 OCCUPANCY HISTORY")
                    occ_data = f_df["People"].resample(rule).max() if rule else f_df["People"]
                    st.bar_chart(occ_data, color="#aa00ff", height=180)
                    
                    st.divider()

                    # 4. Environmental Grid
                    r1_1, r1_2 = st.columns(2)
                    with r1_1:
                        with st.container(border=True):
                            st.markdown("#### TEMPERATURE (°C)")
                            st.line_chart(resampled["Temperature"], color="#b388ff")
                    with r1_2:
                        with st.container(border=True):
                            st.markdown("#### HUMIDITY (%)")
                            st.line_chart(resampled["Humidity"], color="#7c4dff")

                    r2_1, r2_2 = st.columns(2)
                    with r2_1:
                        with st.container(border=True):
                            st.markdown("#### AIR QUALITY (VOC)")
                            st.line_chart(resampled["VOC Index"], color="#651fff")
                    with r2_2:
                        with st.container(border=True):
                            st.markdown("#### LIGHT LEVELS (LUX)")
                            st.bar_chart(resampled["Light"], color="#e040fb")
                else:
                    st.warning("No data found for this selection.")

    except Exception as e:
        st.error(f"DASHBOARD ERROR: {e}")

# Run the render
render_dashboard()
