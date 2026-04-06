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

# --- HELPER FUNCTION FOR STATUS ---
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
        # --- MAIN NAVIGATION TABS ---
        main_tab1, main_tab2 = st.tabs(["🌐 Fleet Overview (Live)", "🔍 Room Deep Dive (History)"])

        # ==========================================
        # TAB 1: THE NEW SLICK OVERVIEW
        # ==========================================
        with main_tab1:
            st.subheader("Live Room Status")
            
            # Grab only the absolute newest row for each room
            latest_data = df.sort_values('Timestamp').drop_duplicates('Room', keep='last').copy()
            
            # Apply our smart status logic to the whole table
            latest_data['Live Status'] = latest_data.apply(get_smart_status, axis=1)
            
            # Select and reorder columns for the slick UI - swapped Timestamp for People
            display_df = latest_data[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']]
            
            # Draw the advanced dataframe
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
            
            # Move the selector inline instead of the sidebar to keep it clean
            selected_room = st.selectbox("Select a room to investigate:", room_list)
            filtered_df = df[df['Room'] == selected_room]

            if not filtered_df.empty:
                latest = filtered_df.iloc[-1]
                
                st.divider()
                
                # --- TOP METRICS ---
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

                # --- CHARTS ---
                chart_col1, chart_col2 = st.columns(2)
                
                with chart_col1:
                    st.markdown("#### 🌡️ Environment (Temp & Humidity)")
                    st.line_chart(filtered_df.set_index("Timestamp")[["Temperature", "Humidity"]])
                    
                    st.markdown("#### 💡 Light Levels")
                    st.area_chart(filtered_df.dropna(subset=['Light']).set_index("Timestamp")["Light"], color="#fcd303")

                with chart_col2:
                    st.markdown("#### 👥 Occupancy Trends")
                    st.area_chart(filtered_df.dropna(subset=['People']).set_index("Timestamp")["People"], color="#ffaa00")
                    
                    st.markdown("#### 🌬️ Air Quality (VOC Index)")
                    st.line_chart(filtered_df.dropna(subset=['VOC Index']).set_index("Timestamp")["VOC Index"], color="#29b09d")

            else:
                st.warning("No historical data found for this room.")

    else:
        st.warning("No data found in the spreadsheet yet.")

except Exception as e:
    st.error(f"Uh oh! Couldn't load the data. (Error: {e})")
