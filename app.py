import streamlit as st
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Neat Dashboard", layout="wide", page_icon="📊")

st.title("🌡️ Neat Sensor Dashboard")
st.markdown("Live environmental & occupancy data.")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    
    # Ensure column names match perfectly
    if len(df.columns) >= 6:
        df.columns = ["Timestamp", "Room", "Temperature", "CO2", "Humidity", "People"]
    
    # Convert data formats
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "CO2", "Humidity", "People"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df.dropna(subset=['Timestamp'])
    df = df.sort_values('Timestamp')
    return df

try:
    with st.spinner('Pulling live data from Google Sheets...'):
        df = load_data(SHEET_URL)

    # --- SIDEBAR FILTERS ---
    st.sidebar.header("⚙️ Filter")
    
    # "All Rooms" is gone. It just pulls the exact list of rooms.
    room_list = sorted(df['Room'].dropna().unique().tolist())
    selected_room = st.sidebar.selectbox("Select a Room", room_list)

    # Filter down to just the chosen room
    filtered_df = df[df['Room'] == selected_room]

    if not filtered_df.empty:
        latest = filtered_df.iloc[-1]
        
        # --- TOP METRICS (Scorecards) ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperature", f"{latest['Temperature']:.1f} °C" if pd.notna(latest['Temperature']) else "N/A")
        
        # Clean CO2 Error Handling
        if pd.notna(latest['CO2']) and latest['CO2'] > 0:
            c2.metric("CO2 Level", f"{latest['CO2']:.0f} ppm")
        else:
            c2.metric("CO2 Level", "No Sensor")
            
        c3.metric("Humidity", f"{latest['Humidity']:.1f} %" if pd.notna(latest['Humidity']) else "N/A")
        c4.metric("People Count", f"{latest['People']:.0f}" if pd.notna(latest['People']) else "0")

        st.divider()

        # --- THE STAR OF THE SHOW: PEOPLE COUNT ---
        st.markdown("### 👥 Occupancy (People Count)")
        ppl_df = filtered_df.dropna(subset=['People']).set_index("Timestamp")["People"]
        if not ppl_df.empty:
            # Using an area chart so it creates a highly visual "mountain" of peak busy times
            st.area_chart(ppl_df, color="#ffaa00") 
        else:
            st.info("No people count data available for this room.")
            
        st.divider()
            
        # --- CLEAN ENVIRONMENTAL CHARTS ---
        st.markdown("### 🌡️ Environment")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Temperature Over Time**")
            temp_df = filtered_df.dropna(subset=['Temperature']).set_index("Timestamp")["Temperature"]
            st.line_chart(temp_df, color="#ff4b4b")
            
            st.markdown("**Humidity Over Time**")
            hum_df = filtered_df.dropna(subset=['Humidity']).set_index("Timestamp")["Humidity"]
            st.line_chart(hum_df, color="#0068c9")

        with chart_col2:
            st.markdown("**CO2 Levels Over Time**")
            # This logic strips out all the empty data from rooms without CO2 sensors
            co2_df = filtered_df.dropna(subset=['CO2'])
            
            # If the room actually has CO2 data, draw the chart. If not, politely tell the user.
            if not co2_df.empty and co2_df["CO2"].sum() > 0:
                st.line_chart(co2_df.set_index("Timestamp")["CO2"], color="#29b09d")
            else:
                st.info(f"No CO2 sensor equipped in {selected_room}.")

    else:
        st.warning("No data found for this room.")

except Exception as e:
    st.error(f"Uh oh! Couldn't load the data. (Error: {e})")
