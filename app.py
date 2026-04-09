import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Neat London Showroom", layout="wide", page_icon="🏢")

# ==========================================
# 1. FORCED DARK MODE, CHUNKY STYLE & ANIMATIONS
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
    
    @keyframes fadeSlideUp {
        0% { opacity: 0; transform: translateY(50px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    div[role="tabpanel"] {
        animation: fadeSlideUp 0.7s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }
    
    div[data-testid="stMarkdownContainer"] div[style*="border-radius: 15px"] {
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease !important;
    }
    div[data-testid="stMarkdownContainer"] div[style*="border-radius: 15px"]:hover {
        transform: translateY(-12px) scale(1.02) !important;
        box-shadow: 0 20px 40px rgba(156, 39, 176, 0.6) !important;
    }
    
    /* Style for the Danger/Reboot Button */
    button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: white !important;
        font-weight: 900 !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background-color: #ff2a2a !important;
        box-shadow: 0 0 15px rgba(255, 75, 75, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. NEAT PULSE API LOGIC (LIVE MODE)
# ==========================================
PULSE_ORG_ID = "wMjVWJM"
PULSE_API_KEY = "ea1fe7eyJDbGllbnRJZCI6OSwiVG9rZW4iOiIzNDBjNTQ1M2U5MTkyNDgyZGU3ZTBiZjExZTMxOTg3NSJ9"

# Ensure there is a comma at the end of every line EXCEPT the very last one!
ENDPOINT_MAP = {
    "Dalmore Microsoft": "47ae3b27-bb05-4c51-9de5-c2aa75ab998e",
    "Edradour": "aa7897d8-868f-4866-b3c1-b64039c10817",
    "Barra": "aebf0451-4ad6-44ef-aa59-ee2f26c0cc38",
    "Harris": "6e0f6d6b-97a5-4c2d-8c8d-286e71ea02cc"
}

def send_pulse_reboot(room_name):
    """Sends a direct reboot command to the target Endpoint."""
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id:
         return False, f"Setup Error: No Endpoint ID mapped for '{room_name}'."

    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/reboot"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Content-Type": "application/json"}
    
    try:
        response = requests.post(api_url, headers=headers)
        response.raise_for_status() 
        return True, f"Success: Reboot command dispatched to {room_name}."
    except requests.exceptions.HTTPError as http_err:
        return False, f"API Error ({response.status_code}): {response.text}"
    except Exception as e:
        return False, f"Connection Error: {str(e)}"

def apply_neat_config(room_name, config_payload):
    """Pushes a dynamic deviceConfig payload to the target Endpoint."""
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id:
         return False, f"Setup Error: No Endpoint ID mapped for '{room_name}'."

    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/config"
    headers = {
        "Authorization": f"Bearer {PULSE_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {"deviceConfig": config_payload}
    
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status() 
        return True, f"Success: Config applied to {room_name}."
    except requests.exceptions.HTTPError as http_err:
        return False, f"API Error ({response.status_code}): {response.text}"
    except Exception as e:
        return False, f"Connection Error: {str(e)}"

# ==========================================
# 3. DATA LOADING & HELPERS
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url, skipinitialspace=True)
    if len(df.columns) >= 8:
        df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    return df.dropna(subset=['Timestamp']).sort_values('Timestamp')

def get_smart_status(row):
    if str(row['Status']) == "in use":
        return "🔴 IN USE"
    people = row['People'] if pd.notna(row['People']) else 0
    if people > 0:
        return f"🟡 OCCUPIED ({int(people)})"
    return "🟢 AVAILABLE"

def render_smart_card(label, value, color="#9c27b0"):
    return f"""
    <div style="background-color: #2d303a; border: 2px solid {color}; border-radius: 15px; padding: 15px; margin-bottom: 15px;">
        <p style="margin:0; font-size: 0.9rem; font-weight: 900; color: #f0f2f6; text-transform: uppercase;">{label}</p>
        <h2 style="margin:0; font-size: 2.2rem; font-weight: 900; color: {color};">{value}</h2>
    </div>
    """

global_df = load_data(SHEET_URL)

# ==========================================
# 4. STATIC SIDEBAR (COMMAND CENTER)
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    st.markdown(f"""
    <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">18°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Cloudy</p>
        <hr style="border: 1px solid #404452; margin: 10px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">H: 20°C | L: 5°C</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not global_df.empty:
        latest_sb = global_df.sort_values('Timestamp', ascending=False).drop_duplicates('Room')
        
        # COMFORT RING
        avg_t = latest_sb['Temperature'].mean(skipna=True)
        avg_h = latest_sb['Humidity'].mean(skipna=True)
        avg_v = latest_sb['VOC Index'].mean(skipna=True)
        penalty = 0
        if pd.notna(avg_t): penalty += abs(avg_t - 21) * 3
        if pd.notna(avg_h): penalty += abs(avg_h - 45) * 0.5
        if pd.notna(avg_v): penalty += (avg_v * 0.1)
        comfort = max(0, min(100, int(100 - penalty)))
        ring_color = "#9c27b0" if comfort >= 80 else ("#ffb300" if comfort >= 60 else "#ff4b4b")
        
        st.markdown("### 🔋 BUILDING COMFORT")
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
            <div style="width: 120px; height: 120px; border-radius: 50%; background: conic-gradient({ring_color} {comfort}%, #2d303a 0); display: flex; justify-content: center; align-items: center; box-shadow: 0 0 15px rgba(0,0,0,0.5);">
                <div style="width: 90px; height: 90px; border-radius: 50%; background-color: #0e1117; display: flex; justify-content: center; align-items: center;">
                    <h2 style="margin:0; font-size: 1.8rem; color: {ring_color};">{comfort}%</h2>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # MVP ROOM
        today = pd.Timestamp.now().normalize()
        today_df = global_df[global_df['Timestamp'] >= today]
        if not today_df.empty and today_df['People'].sum() > 0:
            pop_room = today_df.groupby('Room')['People'].sum().idxmax()
            st.markdown("### 🏆 TODAY'S MVP")
            st.markdown(f"""
            <div style="background-color: #2d303a; border-left: 5px solid #00e5ff; border-radius: 5px; padding: 10px; margin-bottom: 20px;">
                <p style="margin:0; font-size: 0.8rem; color: #f0f2f6; text-transform: uppercase;">Highest Traffic Space</p>
                <h4 style="margin:0; color: #ffffff;">{pop_room}</h4>
            </div>
            """, unsafe_allow_html=True)

        # ALERTS
        st.markdown("### 🚨 SYSTEM ALERTS")
        alerts = []
        for _, row in latest_sb.iterrows():
            if pd.notna(row['VOC Index']) and row['VOC Index'] > 150: alerts.append(f"⚠️ <b>{row['Room']}:</b> High VOC")
            if pd.notna(row['Temperature']) and row['Temperature'] > 26: alerts.append(f"🔥 <b>{row['Room']}:</b> Too Hot")
        
        if not alerts:
            st.markdown("""
            <div style="background-color: #1e3a2f; border: 1px solid #00e676; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 20px;">
                <p style="margin:0; color: #00e676; font-weight: bold;">🟢 ALL SYSTEMS OPTIMAL</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            for alert in alerts:
                st.markdown(f"<div style='background-color: #4a1919; border: 1px solid #ff4b4b; border-radius: 8px; padding: 8px; margin-bottom: 8px;'><p style='margin:0; color: #ffca28; font-size: 0.85rem;'>{alert}</p></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    st.success("Auto-Refresh: ACTIVE (2m)")
    if st.button("🔄 FORCE FULL REFRESH", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. DASHBOARD ENGINE 
# ==========================================
@st.fragment(run_every="2m")
def render_main_dashboard():
    st.title("🏢 Neat London Showroom")
    df = load_data(SHEET_URL)
    
    if not df.empty:
        tab1, tab2 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE"])

        with tab1:
            latest = df.sort_values('Timestamp', ascending=False).drop_duplicates('Room').copy()
            latest['Live Status'] = latest.apply(get_smart_status, axis=1)
            
            total_people = int(latest['People'].sum(skipna=True))
            rooms_available = int((latest['Live Status'] == "🟢 AVAILABLE").sum())
            avg_voc = latest['VOC Index'].mean(skipna=True)
            b_voc_color = "#ff4b4b" if avg_voc > 250 else ("#ffb300" if avg_voc > 150 else "#9c27b0")
            
            h1, h2, h3 = st.columns(3)
            h1.markdown(render_smart_card("TOTAL PEOPLE IN SHOWROOM", f"{total_people} 👥"), unsafe_allow_html=True)
            h2.markdown(render_smart_card("ROOMS CURRENTLY AVAILABLE", f"{rooms_available} 🟢"), unsafe_allow_html=True)
            h3.markdown(render_smart_card("BUILDING AIR QUALITY (VOC)", f"{avg_voc:.0f} 🌬️", b_voc_color), unsafe_allow_html=True)
            
            st.divider()
            st.subheader("LIVE FLEET STATUS")
            dynamic_height = (len(latest) * 38) + 40 
            st.dataframe(
                latest[['Room', 'Live Status', 'Temperature', 'Humidity', 'VOC Index', 'Light', 'People']], 
                column_config={"Humidity": st.column_config.ProgressColumn("Humidity", format="%d%%", min_value=0, max_value=100)},
                hide_index=True, use_container_width=True, height=dynamic_height
            )

        with tab2:
            c_room, c_date, c_grain = st.columns([1.5, 2, 1])
            with c_room: selected_room = st.selectbox("CHOOSE A ROOM:", sorted(df['Room'].unique()))
            with c_date: date_range = st.date_input("SELECT DATE RANGE:", [datetime.now().date() - timedelta(days=7), datetime.now().date()])
            with c_grain: grain = st.selectbox("TIME RESOLUTION:", ["Minutes (Raw)", "Hourly Avg", "Daily Avg"])

            f_df = df[df['Room'] == selected_room].copy()
            if len(date_range) == 2:
                start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1]) + timedelta(days=1)
                f_df = f_df[(f_df['Timestamp'] >= start) & (f_df['Timestamp'] < end)]
            
            if not f_df.empty:
                f_df = f_df.set_index("Timestamp")
                rule = {"Minutes (Raw)": None, "Hourly Avg": "h", "Daily Avg": "D"}[grain]
                resampled = f_df.resample(rule).mean(numeric_only=True) if rule else f_df
                
                latest_val = f_df.iloc[-1]
                v_voc, v_tmp, v_hum = latest_val['VOC Index'], latest_val['Temperature'], latest_val['Humidity']
                voc_col = "#ff4b4b" if v_voc > 250 else ("#ffb300" if v_voc > 150 else "#9c27b0")
                tmp_col = "#ff4b4b" if v_tmp > 26 else ("#00e5ff" if v_tmp < 16 else "#9c27b0")
                hum_col = "#ffb300" if (v_hum < 30 or v_hum > 60) else "#9c27b0"

                m1, m2, m3, m4 = st.columns(4)
                m1.markdown(render_smart_card("LATEST TEMP", f"{v_tmp:.1f}°C", tmp_col), unsafe_allow_html=True)
                m2.markdown(render_smart_card("LATEST HUMIDITY", f"{v_hum:.0f}%", hum_col), unsafe_allow_html=True)
                m3.markdown(render_smart_card("LATEST VOC", f"{v_voc:.0f}", voc_col), unsafe_allow_html=True)
                m4.markdown(render_smart_card("LATEST LIGHT", f"{latest_val['Light']:.0f} lx"), unsafe_allow_html=True)
                
                st.divider()
                st.markdown("#### 👥 OCCUPANCY HISTORY")
                st.bar_chart(f_df["People"].resample(rule).max() if rule else f_df["People"], color="#aa00ff", height=180)
                
                st.divider()
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

                st.divider()
                st.markdown("#### 📅 PEAK UTILIZATION HEATMAP")
                h_data = f_df.copy().reset_index()
                h_data['Hour'] = h_data['Timestamp'].dt.hour
                h_data['Day'] = h_data['Timestamp'].dt.day_name()
                
                heatmap = alt.Chart(h_data).mark_rect().encode(
                    x=alt.X('Hour:O', title='Hour of Day'),
                    y=alt.Y('Day:O', title='', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
                    color=alt.Color('max(People):Q', scale=alt.Scale(scheme='purples')),
                    tooltip=['Day', 'Hour', 'max(People)']
                ).properties(height=280)
                st.altair_chart(heatmap, use_container_width=True)

                # --- CONTROL PANEL ---
                st.divider()
                st.markdown("#### ⚙️ REMOTE DEVICE MANAGEMENT")
                st.caption(f"Execute live management commands on the Neat hardware located in **{selected_room}**.")
                
                c_btn1, c_btn2, c_btn3 = st.columns(3)
                
                with c_btn1:
                    if st.button("☀️ WAKE DISPLAY", use_container_width=True):
                        with st.spinner("Waking device..."):
                            success, msg = apply_neat_config(selected_room, {"screenStayOn": True, "screenStandby": 120})
                            if success: st.success(msg)
                            else: st.error(msg)
                            
                with c_btn2:
                    if st.button("🌙 FORCE SLEEP", use_container_width=True):
                        with st.spinner("Putting device to sleep..."):
                            success, msg = apply_neat_config(selected_room, {"screenStayOn": False, "screenStandby": 0})
                            if success: st.success(msg)
                            else: st.error(msg)

                with c_btn3:
                    if st.button("🔄 REBOOT DEVICE", use_container_width=True, type="primary"):
                        with st.spinner("Sending reboot command..."):
                            success, msg = send_pulse_reboot(selected_room)
                            if success: st.success(msg)
                            else: st.error(msg)

            else:
                st.warning("Select a valid date range to see room data.")

render_main_dashboard()
