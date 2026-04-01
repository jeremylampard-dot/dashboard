import streamlit as st
import pandas as pd

# 1. Page Configuration (Makes it wide and modern)
st.set_page_config(page_title="Neat Pulse Dashboard", layout="wide", page_icon="📊")

st.title("🌡️ Neat Sensor Dashboard")
st.markdown("Live, interactive environmental data from your Neat devices.")

SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url)
    
    # Force the column names so Streamlit always knows exactly what to look for
    if len(df.columns) >= 6:
        df.columns = ["Timestamp", "Room", "Temperature", "CO2", "Humidity", "People"]
    
    # Convert data into strict numbers and dates so charts don't break on "N/A"
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
    st.sidebar.header("⚙️ Dashboard Filters")
    room_list = sorted(df['Room'].dropna().unique().tolist())
    selected_room = st.sidebar.selectbox("Select a Room", ["All Rooms"] + room_list)

    if selected_room != "All Rooms":
        filtered_df = df[df['Room'] == selected_room]
    else:
        filtered_df = df

    # --- TOP METRICS (Scorecards) ---
    st.subheader(f"Current Status: {selected_room}")
    if not filtered_df.empty:
        # Grab the absolute newest row of data
        latest = filtered_df.iloc[-1]
        
        # Create 4 horizontal columns for the big numbers
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Temperature", f"{latest['Temperature']:.1f} °C" if pd.notna(latest['Temperature']) else "N/A")
        c2.metric("CO2 Level", f"{latest['CO2']:.0f} ppm" if pd.notna(latest['CO2']) else "N/A")
        c3.metric("Humidity", f"{latest['Humidity']:.1f} %" if pd.notna(latest['Humidity']) else "N/A")
        c4.metric("People Count", f"{latest['People']:.0f}" if pd.notna(latest['People']) else "N/A")

        st.divider()

        # --- INTERACTIVE CHARTS ---
        st.markdown("### 📈 Historical Trends")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("**Temperature Over Time**")
            if selected_room == "All Rooms":
                st.line_chart(filtered_df.pivot_table(index="Timestamp", columns="Room", values="Temperature", aggfunc="mean"))
            else:
                st.line_chart(filtered_df.set_index("Timestamp")["Temperature"])

        with chart_col2:
            st.markdown("**CO2 Levels Over Time**")
            if selected_room == "All Rooms":
                st.line_chart(filtered_df.pivot_table(index="Timestamp", columns="Room", values="CO2", aggfunc="mean"))
            else:
                st.line_chart(filtered_df.set_index("Timestamp")["CO2"])

        # --- RAW DATA TOGGLE ---
        with st.expander("View Raw Spreadsheet Data"):
            st.dataframe(filtered_df, use_container_width=True)

    else:
        st.warning("No data found for this selection.")

except Exception as e:
    st.error(f"Uh oh! Couldn't load the data. (Error: {e})")
