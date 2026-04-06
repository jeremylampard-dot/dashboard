import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Neat Intelligence Dashboard", layout="wide", page_icon="🏢")

st.title("🏢 Neat Room Intelligence")
st.markdown("Live environmental telemetry and occupancy tracking.")

# Your real CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    
    # Map to your exact 8 columns
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df['Status'] = df['Status'].astype(str)
        
    df = df.dropna(subset=['Timestamp'])
    df = df.sort_values('Timestamp')
    return df

try:
    with st.spinner('Pulling live telemetry...'):
        df = load_data(SHEET_URL)

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("⚙️ Select Location")
    room_list = sorted(df['Room'].dropna().unique().tolist())
    selected_room = st.sidebar.selectbox("Room Name", room_list)

    filtered_df = df[df['Room'] == selected_room]

    if not filtered_df.empty:
        latest = filtered_df.iloc[-1]
        
        # --- HARDWARE STATUS LOGIC ---
        # Reads directly from your new Google Sheet column
        hardware_status = str(latest['Status']).strip().lower()
        people_count = latest['People'] if pd.notna(latest['People']) else 0
        
        if hardware_status == "in use":
            st.error(f"**Room Status:** 🔴 IN USE (Active Call/Meeting)")
        elif people_count > 0:
            st.warning(f"**Room Status:** 🟡 OCCUPIED (Not in a call, but {int(people_count)} people detected)")
        else:
            st.success(f"**Room Status:** 🟢 AVAILABLE")

        st.divider()

        # --- TOP METRICS (Scorecards) ---
        c1, c2, c3, c4, c5 = st.columns(5)
        
        c1.metric("Temperature", f"{latest['Temperature']:.1f} °C" if pd.notna(latest['Temperature']) else "N/A")
        c2.metric("Humidity", f"{latest['Humidity']:.1f} %" if pd.notna(latest['Humidity']) else "N/A")
        
        # VOC Index Logic (100 is normal baseline)
        voc = latest['VOC Index']
        if pd.notna(voc):
            if voc > 150:
                c3.metric("Air Quality (VOC)", f"{voc:.0f}", delta="Poor Air", delta_color="inverse")
            else:
                c3.metric("Air Quality (VOC)", f"{voc:.0f}", delta="Good", delta_color="normal")
        else:
            c3.metric("Air Quality (VOC)", "N/A")
            
        c4.metric("Light Level", f"{latest['Light']:.0f} lux" if pd.notna(latest['Light']) else "N/A")
        c5.metric("People Count", f"{people_count:.0f}")

        st.divider()

        # --- TABS FOR CHARTS ---
        tab1, tab2 = st.tabs(["👥 Occupancy & Environment", "🌬️ Air Quality & Light Deep Dive"])

        with tab1:
            st.markdown("### 👥 Occupancy Trends")
            ppl_df = filtered_df.dropna(subset=['People']).set_index("Timestamp")["People"]
            if not ppl_df.empty:
                st.area_chart(ppl_df, color="#ffaa00") 
            
            st.markdown("### 🌡️ Temperature & Humidity")
            chart_col1, chart_col2 = st.columns(2)
            with chart_col1:
                temp_df = filtered_df.dropna(subset=['Temperature']).set_index("Timestamp")["Temperature"]
                st.line_chart(temp_df, color="#ff4b4b")
            with chart_col2:
                hum_df = filtered_df.dropna(subset=['Humidity']).set_index("Timestamp")["Humidity"]
                st.line_chart(hum_df, color="#0068c9")

        with tab2:
            st.markdown("### 🌬️ VOC Index (Air Quality)")
            st.caption("A VOC Index of 100 represents the average baseline environment. Values above 150 indicate a decline in air quality.")
            voc_df = filtered_df.dropna(subset=['VOC Index']).set_index("Timestamp")["VOC Index"]
            if not voc_df.empty:
                st.line_chart(voc_df, color="#29b09d")
            else:
                st.info("No VOC data recorded yet.")

            st.markdown("### 💡 Light Levels (Illumination)")
            light_df = filtered_df.dropna(subset=['Light']).set_index("Timestamp")["Light"]
            if not light_df.empty:
                st.area_chart(light_df, color="#fcd303")
            else:
                st.info("No light data recorded yet.")

    else:
        st.warning("No data found for this room. Waiting for sensor update...")

except Exception as e:
    st.error(f"Uh oh! Couldn't load the data. (Error: {e})")
