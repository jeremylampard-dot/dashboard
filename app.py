import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Neat Intelligence Dashboard", layout="wide", page_icon="🏢")

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
# SIDEBAR: NATIVE WEATHER & SYSTEM STATUS
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    st.markdown(f"""
    <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center;">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">14°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Cloudy / Overcast</p>
        <hr style="border: 1px solid #404452; margin: 10px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">LOW: 9°C | HIGH: 16°C</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    if st.button("🔄 REFRESH DATA", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.title("🏢 Neat Room Intelligence")

# --- DATA LOADING ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Status'] = df['Status'].astype(str).str.strip()
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    return df

def get_smart_status(row):
    hw_status = str(row['Status']).lower()
    people = row['People'] if pd.notna(row['People']) else 0
    if "in use" in hw_status: return "🔴 IN USE"
    elif people > 0: return f"🟡 OCCUPIED ({int(people)})"
    else: return "🟢 AVAILABLE"

try:
    df = load_data(SHEET_URL)
    if not df.empty:
        tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

        with tab1:
            st.subheader("LIVE FLEET STATUS")
            latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
            latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
            with st.container(border=True):
                st.dataframe(
                    latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], 
                    column_config={
                        "Humidity": st.column_config.ProgressColumn("Humidity", format="%f%%", min_value=0, max_value=100),
                        "Temperature": st.column_config.NumberColumn("Temp (degC)", format="%.1f"),
                    },
                    hide_index=True, use_container_width=True
                )

        with tab2:
            # --- Deep Dive Header ---
            c_room, c_date, c_grain = st.columns([1.5, 2, 1])
            with c_room:
                selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
            with c_date:
                start_default = (datetime.now() - timedelta(days=7)).date()
                end_default = datetime.now().date()
                date_range = st.date_input("SELECT DATE RANGE:", [start_default, end_default])
            with c_grain:
                grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg", "Weekly Avg"])

            f_df = df[df['Room'] == selected_room].copy()
            if len(date_range) == 2:
                start_dt, end_dt = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
                f_df = f_df[(f_df['Timestamp'] >= start_dt) & (f_df['Timestamp'] < end_dt)]
            
            f_df = f_df.set_index("Timestamp")
            g_map = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D", "Weekly Avg": "W"}
            rule = g_map[grain]

            if not f_df.empty:
                resampled = f_df[["Temperature", "Humidity", "VOC Index", "Light", "People"]].resample(rule).mean() if rule else f_df
                
                # --- 1. SLIM OCCUPANCY AT TOP ---
                st.markdown("#### 👥 LIVE OCCUPANCY HISTORY")
                occ_data = f_df["People"].resample(rule).max() if rule else f_df["People"]
                st.bar_chart(occ_data, color="#aa00ff", height=180)

                st.divider()

                # --- 2. ENVIRONMENT GRID ---
                r1_1, r1_2 = st.columns(2)
                with r1_1:
                    with st.container(border=True):
                        st.markdown("#### TEMPERATURE")
                        st.line_chart(resampled["Temperature"], color="#b388ff")
                with r1_2:
                    with st.container(border=True):
                        st.markdown("#### HUMIDITY")
                        st.line_chart(resampled["Humidity"], color="#7c4dff")

                r2_1, r2_2 = st.columns(2)
                with r2_1:
                    with st.container(border=True):
                        st.markdown("#### AIR QUALITY")
                        st.line_chart(resampled["VOC Index"], color="#651fff")
                with r2_2:
                    with st.container(border=True):
                        st.markdown("#### LIGHT LEVELS")
                        st.bar_chart(resampled["Light"], color="#e040fb")
            else:
                st.warning("No data found for this selection.")

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
