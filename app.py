import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Neat Intelligence Dashboard", layout="wide", page_icon="🏢")

# ==========================================
# CUSTOM CSS: THE CHUNKY DARK GREY THEME
# ==========================================
st.markdown("""
<style>
    /* 1. Force the Dark Grey Background */
    .stApp {
        background-color: #22242b !important;
    }

    /* 2. Make all Headings Bolder and Chunkier */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial Black', 'Impact', sans-serif !important;
        font-weight: 900 !important;
        letter-spacing: -0.05em;
        color: #f0f2f6 !important;
    }

    /* 3. Style the Metric Scorecards with Smooth Borders */
    [data-testid="stMetric"] {
        background-color: #2d303a;
        border: 2px solid #404452;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    
    /* 4. Chunky Metric Numbers */
    [data-testid="stMetricValue"] {
        font-weight: 900 !important;
        font-size: 2.2rem !important;
        color: #ffffff !important;
    }

    /* 5. Make regular text slightly bolder */
    p, span, div {
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Neat Room Intelligence")
st.markdown("Live environmental telemetry and occupancy tracking.")

# Your real CSV link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df['Status'] = df['Status'].astype(str)
    df = df.dropna(subset=['Timestamp'])
    df = df.sort_values('Timestamp')
    return df

def get_smart_status(row):
    hw_status = str(row['Status']).strip().lower()
    people = row['People'] if pd.notna(row['People']) else 0
    
    if hw_status == "in use":
        return "🔴 IN USE"
    elif people > 0:
        return f"🟡 OCCUPIED ({int(people)})"
    else:
        return "🟢 AVAILABLE"

try:
    with st.spinner('Pulling live telemetry...'):
        df = load_data(SHEET_URL)

    if not df.empty:
        main_tab1, main_tab2 = st.tabs(["🌐 Fleet Overview (Live)", "🔍 Room Deep Dive (History)"])

        # ==========================================
        # TAB 1: FLEET OVERVIEW
        # ==========================================
        with main_tab1:
            st.subheader("Live Room Status")
            
            latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
            latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
            display_df = latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']]
            
            # Wrap the table in a smooth bordered container!
            with st.container(border=True):
                st.dataframe(
                    display_df,
                    column_config={
                        "Room": st.column_config.TextColumn("Room Name", width="medium"),
                        "Live Status": st.column_config.TextColumn("Live Status", width="medium"),
                        "Temperature": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                        "Humidity": st.column_config.ProgressColumn("Humidity", format="%f%%", min_value=0, max_value=100),
                        "VOC Index": st.column_config.NumberColumn("Air Quality (VOC)", format="%d"),
                        "Light": st.column_config.NumberColumn("Light (lux)", format="%d"),
                        "People": st.column_config.NumberColumn("People Count", format="%d"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

        # ==========================================
        # TAB 2: THE HISTORICAL DEEP DIVE
        # ==========================================
        with main_tab2:
            room_list = sorted(df['Room'].dropna().unique().tolist())
            
            # Wrap the selector in a bordered container
            with st.container(border=True):
                selected_room = st.selectbox("Select a room to investigate:", room_list)
            
            filtered_df = df[df['Room'] == selected_room]

            if not filtered_df.empty:
                latest = filtered_df.iloc[-1]
                
                st.divider()
                
                # Metrics (These get automatically styled with borders from our CSS!)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Temperature", f"{latest['Temperature']:.1f} °C" if pd.notna(latest['Temperature']) else "N/A")
                c2.metric("Humidity", f"{latest['Humidity']:.1f} %" if pd.notna(latest['Humidity']) else "N/A")
                
                voc = latest['VOC Index']
                if pd.notna(voc):
                    c3.metric("Air Quality (VOC)", f"{voc:.0f}", delta="Poor Air" if voc > 150 else "Good", delta_color="inverse" if voc > 150 else "normal")
                else:
                    c3.metric("Air Quality (VOC)", "N/A")
                    
                c4.metric("Light Level", f"{latest['Light']:.0f} lux" if pd.notna(latest['Light']) else "N/A")

                st.divider()

                # --- CHARTS WRAPPED IN SMOOTH BORDERS ---
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    with st.container(border=True):
                        st.markdown("#### 🌡️ Temperature (°C)")
                        temp_df = filtered_df.dropna(subset=['Temperature']).set_index("Timestamp")["Temperature"]
                        if not temp_df.empty:
                            st.line_chart(temp_df, color="#ff4b4b")
                            
                with chart_col2:
                    with st.container(border=True):
                        st.markdown("#### 💧 Humidity (%)")
                        hum_df = filtered_df.dropna(subset=['Humidity']).set_index("Timestamp")["Humidity"]
                        if not hum_df.empty:
                            st.line_chart(hum_df, color="#0068c9")

                chart_col3, chart_col4 = st.columns(2)
                
                with chart_col3:
                    with st.container(border=True):
                        st.markdown("#### 🌬️ Air Quality (VOC Index)")
                        voc_df = filtered_df.dropna(subset=['VOC Index']).set_index("Timestamp")["VOC Index"]
                        if not voc_df.empty:
                            st.line_chart(voc_df, color="#29b09d")
                        else:
                            st.info("No VOC data recorded yet.")
                            
                with chart_col4:
                    with st.container(border=True):
                        st.markdown("#### 💡 Light Levels (lux)")
                        light_df = filtered_df.dropna(subset=['Light']).set_index("Timestamp")["Light"]
                        if not light_df.empty:
                            st.area_chart(light_df, color="#fcd303")
                        else:
                            st.info("No light data recorded yet.")
                
                with st.container(border=True):
                    st.markdown("#### 👥 Occupancy Trends (People Count)")
                    ppl_df = filtered_df.dropna(subset=['People']).set_index("Timestamp")["People"]
                    if not ppl_df.empty:
                        st.area_chart(ppl_df, color="#ffaa00")
                    else:
                        st.info("No occupancy data recorded yet.")

            else:
                st.warning("No historical data found for this room.")

    else:
        st.warning("No data found in the spreadsheet yet.")

except Exception as e:
    st.error(f"Uh oh! Couldn't load the data. (Error: {e})")
