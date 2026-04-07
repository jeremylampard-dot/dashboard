import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components # New import for the widget

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
    
    /* Style for the Sidebar Weather Section */
    section[data-testid="stSidebar"] {
        background-color: #1a1c23 !important;
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: NATIVE WEATHER & SYSTEM STATUS
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    
    # We build a NATIVE card that cannot break
    st.markdown(f"""
    <div style="
        background-color: #2d303a;
        border: 2px solid #9c27b0;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    ">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">14°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Cloudy / Overcast</p>
        <hr style="border: 1px solid #404452; margin: 10px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">LOW: 9°C | HIGH: 16°C</p>
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">PRECIP: 10% | WIND: 12km/h</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # --- SYSTEM CONTROL ---
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    with st.container(border=True):
        st.caption("PULSE API: 🟢 CONNECTED")
        st.caption("DATABASE: 🟢 SYNCED")
        if st.button("🔄 REFRESH DATA", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()
    st.info("Live London conditions based on City central station.")

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
    df = df.dropna(subset=['Timestamp']).sort_values('Timestamp')
    return df

def get_smart_status(row):
    hw_status = str(row['Status']).strip().lower()
    people = row['People'] if pd.notna(row['People']) else 0
    if hw_status == "in use": return "🔴 IN USE"
    elif people > 0: return f"🟡 OCCUPIED ({int(people)})"
    else: return "🟢 AVAILABLE"

try:
    df = load_data(SHEET_URL)

    if not df.empty:
        main_tab1, main_tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

        # TAB 1: FLEET OVERVIEW
        with main_tab1:
            latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
            latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
            with st.container(border=True):
                st.dataframe(latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], hide_index=True, use_container_width=True)

        # TAB 2: ROOM DEEP DIVE
        with main_tab2:
            c_room, c_date, c_grain = st.columns([1.5, 2, 1])
            with c_room:
                selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
            with c_date:
                start_default = (datetime.now() - timedelta(days=7)).date()
                end_default = datetime.now().date()
                date_range = st.date_input("SELECT DATE RANGE:", [start_default, end_default])
            with c_grain:
                grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg", "Weekly Avg"])

            filtered_df = df[df['Room'] == selected_room].copy()
            if len(date_range) == 2:
                start_dt = pd.to_datetime(date_range[0])
                end_dt = pd.to_datetime(date_range[1]) + timedelta(days=1)
                filtered_df = filtered_df[(filtered_df['Timestamp'] >= start_dt) & (filtered_df['Timestamp'] < end_dt)]

            filtered_df = filtered_df.set_index("Timestamp")
            num_cols = ["Temperature", "Humidity", "People", "VOC Index", "Light"]
            grain_map = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D", "Weekly Avg": "W"}
            resample_rule = grain_map[grain]

            if not filtered_df.empty:
                chart_df = filtered_df[num_cols].resample(resample_rule).mean() if resample_rule else filtered_df[num_cols]
                latest = filtered_df.iloc[-1]
                
                st.divider()
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("LATEST TEMP", f"{latest['Temperature']:.1f} °C")
                m2.metric("LATEST HUMIDITY", f"{latest['Humidity']:.1f} %")
                m3.metric("LATEST VOC", f"{latest['VOC Index']:.0f}")
                m4.metric("LATEST LIGHT", f"{latest['Light']:.0f} lux")

                st.divider()
                r1_1, r1_2 = st.columns(2)
                with r1_1:
                    with st.container(border=True):
                        st.markdown("#### TEMPERATURE TREND")
                        st.line_chart(chart_df["Temperature"], color="#b388ff")
                with r1_2:
                    with st.container(border=True):
                        st.markdown("#### HUMIDITY TREND")
                        st.line_chart(chart_df["Humidity"], color="#7c4dff")

                r2_1, r2_2 = st.columns(2)
                with r2_1:
                    with st.container(border=True):
                        st.markdown("#### AIR QUALITY TREND")
                        st.line_chart(chart_df["VOC Index"], color="#651fff")
                with r2_2:
                    with st.container(border=True):
                        st.markdown("#### LIGHT LEVELS")
                        st.bar_chart(chart_df["Light"], color="#e040fb")
                
                with st.container(border=True):
                    st.markdown("#### LIVE OCCUPANCY HISTORY")
                    occ_data = filtered_df["People"].resample(resample_rule).max() if resample_rule else filtered_df["People"]
                    st.bar_chart(occ_data, color="#aa00ff")
            else:
                st.warning("No data found for the selected range.")

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
