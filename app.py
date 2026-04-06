import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="Neat Intelligence Dashboard", layout="wide", page_icon="🏢")

# ==========================================
# FORCED DARK MODE & CHUNKY STYLE
# ==========================================
st.markdown("""
<style>
    /* Force white text globally for readability */
    html, body, [class*="ViewContainer"] {
        color: #f0f2f6 !important;
    }

    /* Bolder Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Arial Black', 'Impact', sans-serif !important;
        font-weight: 900 !important;
        color: #ffffff !important;
        text-transform: uppercase;
    }

    /* Metric Cards Styling */
    [data-testid="stMetric"] {
        background-color: #2d303a !important;
        border: 2px solid #9c27b0 !important; /* Purple Border */
        border-radius: 15px !important;
        padding: 15px !important;
    }

    [data-testid="stMetricValue"] {
        font-weight: 900 !important;
        color: #ffffff !important;
    }

    /* Make the Sidebar Darker */
    [data-testid="stSidebar"] {
        background-color: #1a1c23 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏢 Neat Room Intelligence")

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
    with st.spinner('Accessing secure data...'):
        df = load_data(SHEET_URL)

    if not df.empty:
        main_tab1, main_tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

        with main_tab1:
            latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
            latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
            display_df = latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']]
            
            with st.container(border=True):
                st.dataframe(
                    display_df,
                    column_config={
                        "Room": st.column_config.TextColumn("Room Name"),
                        "Live Status": st.column_config.TextColumn("Live Status"),
                        "Temperature": st.column_config.NumberColumn("Temp °C", format="%.1f"),
                        "Humidity": st.column_config.ProgressColumn("Humidity", format="%f%%", min_value=0, max_value=100),
                        "VOC Index": st.column_config.NumberColumn("VOC Index", format="%d"),
                        "Light": st.column_config.NumberColumn("Light (lux)", format="%d"),
                        "People": st.column_config.NumberColumn("Occupancy", format="%d"),
                    },
                    hide_index=True,
                    use_container_width=True,
                )

        with main_tab2:
            room_list = sorted(df['Room'].dropna().unique().tolist())
            selected_room = st.selectbox("CHOOSE A ROOM:", room_list)
            filtered_df = df[df['Room'] == selected_room]

            if not filtered_df.empty:
                latest = filtered_df.iloc[-1]
                st.divider()
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("TEMP", f"{latest['Temperature']:.1f} °C")
                c2.metric("HUMIDITY", f"{latest['Humidity']:.1f} %")
                c3.metric("VOC INDEX", f"{latest['VOC Index']:.0f}")
                c4.metric("LIGHT", f"{latest['Light']:.0f} lux")

                st.divider()

                # Purple Charts
                chart_col1, chart_col2 = st.columns(2)
                with chart_col1:
                    with st.container(border=True):
                        st.markdown("#### TEMPERATURE")
                        st.line_chart(filtered_df.set_index("Timestamp")["Temperature"], color="#b388ff")
                with chart_col2:
                    with st.container(border=True):
                        st.markdown("#### HUMIDITY")
                        st.line_chart(filtered_df.set_index("Timestamp")["Humidity"], color="#7c4dff")

                chart_col3, chart_col4 = st.columns(2)
                with chart_col3:
                    with st.container(border=True):
                        st.markdown("#### AIR QUALITY")
                        st.line_chart(filtered_df.set_index("Timestamp")["VOC Index"], color="#651fff")
                with chart_col4:
                    with st.container(border=True):
                        st.markdown("#### LIGHT LEVEL")
                        st.area_chart(filtered_df.set_index("Timestamp")["Light"], color="#e040fb")
                
                with st.container(border=True):
                    st.markdown("#### LIVE OCCUPANCY HISTORY")
                    st.area_chart(filtered_df.set_index("Timestamp")["People"], color="#aa00ff")

    else:
        st.warning("Awaiting initial data stream...")

except Exception as e:
    st.error(f"SYSTEM ERROR: {e}")
