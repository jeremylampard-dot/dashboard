import os
# NUKE THE SEGFAULT: Forces Streamlit to bypass the unstable PyArrow engine entirely
os.environ["STREAMLIT_DATA_FRAME_SERIALIZATION"] = "legacy"

import streamlit as st
import pandas as pd
import altair as alt
import requests
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Neat London Showroom", layout="wide", page_icon="🏢")

# --- Initialize Kiosk State ---
if 'kiosk_idx' not in st.session_state:
    st.session_state.kiosk_idx = 0

# ==========================================
# 1. FORCED DARK MODE, PREMIUM STYLING & GLASSMORPHISM
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;500;700;900&display=swap');
    
    html, body, [class*="ViewContainer"], h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        font-family: 'Outfit', sans-serif !important;
        color: #f0f2f6;
    }
    
    .material-symbols-rounded, .material-icons {
        font-family: 'Material Symbols Rounded', 'Material Icons' !important;
    }
    
    .stApp {
        background: linear-gradient(-45deg, #0e1117, #1a1025, #0f172a, #0e1117);
        background-size: 400% 400%;
        animation: gradientBG 20s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    h1, h2, h3, h4, h5, h6 {
        font-weight: 900 !important;
        color: #ffffff !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stStatusWidget"] { visibility: hidden !important; }
    
    @keyframes fadeSlideUp {
        0% { opacity: 0; transform: translateY(40px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    div[role="tabpanel"] {
        animation: fadeSlideUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }
    
    div[data-testid="stMarkdownContainer"] div[style*="border-radius: 15px"] {
        transition: transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.4s ease !important;
    }
    div[data-testid="stMarkdownContainer"] div[style*="border-radius: 15px"]:hover {
        transform: translateY(-8px) scale(1.02) !important;
        box-shadow: 0 20px 40px rgba(156, 39, 176, 0.3) !important;
    }
    
    div[data-baseweb="tab-list"] { gap: 15px; padding-top: 20px !important; padding-bottom: 25px !important; }
    button[data-baseweb="tab"] {
        background: rgba(45, 48, 58, 0.4) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px !important;
        padding: 12px 25px !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        color: #a0a5b5 !important;
        transition: all 0.3s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(156, 39, 176, 0.5) !important;
        box-shadow: 0 10px 20px rgba(156, 39, 176, 0.2) !important;
        color: #ffffff !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(156, 39, 176, 0.8) !important;
        border-color: #e040fb !important;
        color: #ffffff !important;
        box-shadow: 0 10px 25px rgba(156, 39, 176, 0.4) !important;
    }
    div[data-baseweb="tab-highlight"] { display: none !important; }
    
    button[kind="primary"] {
        background: rgba(255, 75, 75, 0.8) !important;
        backdrop-filter: blur(5px) !important;
        color: white !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 900 !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"]:hover { background: rgba(255, 42, 42, 1) !important; box-shadow: 0 0 20px rgba(255, 75, 75, 0.6) !important; transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. NEAT PULSE API LOGIC (LIVE MODE)
# ==========================================
PULSE_ORG_ID = "YOUR_ORGANIZATION_ID"
PULSE_API_KEY = "YOUR_API_KEY"

ENDPOINT_MAP = {
    "Boardroom": "paste-endpoint-id-here",
    "Front Booth": "paste-endpoint-id-here",
    "Huddle Space": "paste-endpoint-id-here",
    "Harris": "6e0f6d6b-97a5-4c2d-8c8d-286e71ea02cc"
}

def send_pulse_reboot(room_name):
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id: return False, f"Setup Error: No Endpoint ID mapped for '{room_name}'."
    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/reboot"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, headers=headers)
        response.raise_for_status() 
        return True, f"Success: Reboot command dispatched to {room_name}."
    except requests.exceptions.HTTPError as http_err: return False, f"API Error ({response.status_code}): {response.text}"
    except Exception as e: return False, f"Connection Error: {str(e)}"

def apply_neat_config(room_name, config_payload):
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id: return False, f"Setup Error: No Endpoint ID mapped for '{room_name}'."
    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}/config"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Accept": "application/json", "Content-Type": "application/json"}
    try:
        response = requests.post(api_url, headers=headers, json={"deviceConfig": config_payload})
        response.raise_for_status() 
        return True, f"Success: Config applied to {room_name}."
    except requests.exceptions.HTTPError as http_err: return False, f"API Error ({response.status_code}): {response.text}"
    except Exception as e: return False, f"Connection Error: {str(e)}"

# ==========================================
# 3. DATA LOADING & HELPERS
# ==========================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStJLmBoSixXlVRZCSExoE_gW3ntLFo8wa9Ip7dm4z8Yt6iRMTsRYG2mohx_3kFTeMAPxoHiczrx9Ly/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def load_data(url):
    df = pd.read_csv(url, skipinitialspace=True)
    if len(df.columns) >= 8: df.columns = ["Timestamp", "Room", "Temperature", "Humidity", "People", "VOC Index", "Light", "Status"]
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
    for col in ["Temperature", "Humidity", "People", "VOC Index", "Light"]: df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Status'] = df['Status'].fillna('available').astype(str).str.strip().str.lower()
    return df.dropna(subset=['Timestamp']).sort_values('Timestamp')

@st.cache_data(ttl=900) 
def get_live_weather():
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=51.5074&longitude=-0.1278&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min&timezone=Europe%2FLondon"
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        curr_temp = round(data['current']['temperature_2m'])
        w_code = data['current']['weather_code']
        max_temp = round(data['daily']['temperature_2m_max'][0])
        min_temp = round(data['daily']['temperature_2m_min'][0])
        w_map = {0: "Clear Sky ☀️", 1: "Mainly Clear 🌤️", 2: "Partly Cloudy ⛅", 3: "Overcast ☁️", 45: "Foggy 🌫️", 48: "Foggy 🌫️", 51: "Light Drizzle 🌧️", 53: "Drizzle 🌧️", 55: "Heavy Drizzle 🌧️", 61: "Light Rain ☔", 63: "Rain ☔", 65: "Heavy Rain ☔", 71: "Light Snow 🌨️", 73: "Snow 🌨️", 75: "Heavy Snow 🌨️", 95: "Thunderstorm ⛈️", 96: "Thunderstorm ⛈️", 99: "Thunderstorm ⛈️"}
        return curr_temp, w_map.get(w_code, "Cloudy ☁️"), max_temp, min_temp
    except Exception:
        return 18, "Cloudy ☁️", 20, 5

def get_smart_status(row):
    if str(row['Status']) == "in use": return "🔴 IN USE"
    people = row['People'] if pd.notna(row['People']) else 0
    if people > 0: return f"🟡 OCCUPIED ({int(people)})"
    return "🟢 AVAILABLE"

def render_smart_card(label, value, color="#9c27b0"):
    return f"""
    <div style="background: rgba(45, 48, 58, 0.4); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid {color}; border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);">
        <p style="margin:0; font-size: 0.85rem; font-weight: 700; color: #a0a5b5; text-transform: uppercase; letter-spacing: 1.5px;">{label}</p>
        <h2 style="margin:5px 0 0 0; font-size: 2.5rem; font-weight: 900; color: {color}; text-shadow: 0 0 20px {color}40;">{value}</h2>
    </div>
    """

def render_fleet_table(df):
    html = "<style>"
    html += ".fleet-table { width: 100%; border-collapse: separate; border-spacing: 0 12px; margin-top: 10px; }"
    html += ".fleet-th { color: #a0a5b5; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; padding: 0 20px 10px 20px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }"
    html += ".fleet-tr { background: rgba(45, 48, 58, 0.4); transition: all 0.3s ease; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }"
    html += ".fleet-tr:hover { background: rgba(156, 39, 176, 0.2); box-shadow: 0 8px 25px rgba(156, 39, 176, 0.3); transform: scale(1.01); }"
    html += ".fleet-td { padding: 20px; font-size: 1.2rem; font-weight: 500; color: #f0f2f6; border-top: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }"
    html += ".fleet-td:first-child { border-left: 4px solid #9c27b0; border-top-left-radius: 12px; border-bottom-left-radius: 12px; font-weight: 900; font-size: 1.3rem; letter-spacing: 0.5px; }"
    html += ".fleet-td:last-child { border-right: 1px solid rgba(255,255,255,0.05); border-top-right-radius: 12px; border-bottom-right-radius: 12px; }"
    html += ".badge { padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; font-weight: 900; letter-spacing: 1px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }"
    html += ".badge-avail { background: rgba(0, 230, 118, 0.2); color: #00e676; border: 1px solid rgba(0, 230, 118, 0.4); }"
    html += ".badge-occ { background: rgba(255, 179, 0, 0.2); color: #ffca28; border: 1px solid rgba(255, 179, 0, 0.4); }"
    html += ".badge-use { background: rgba(255, 75, 75, 0.2); color: #ff4b4b; border: 1px solid rgba(255, 75, 75, 0.4); }"
    html += ".metric-val { font-weight: 900; font-size: 1.4rem; }"
    html += ".metric-unit { font-size: 0.9rem; color: #a0a5b5; font-weight: 500; margin-left: 4px; }"
    html += "</style>"
    html += "<table class='fleet-table'><thead><tr>"
    html += "<th class='fleet-th'>Room</th><th class='fleet-th'>Status</th><th class='fleet-th'>Temp</th>"
    html += "<th class='fleet-th' style='width: 25%;'>Humidity</th><th class='fleet-th'>VOC</th>"
    html += "<th class='fleet-th'>Light</th><th class='fleet-th'>Occupancy</th></tr></thead><tbody>"
    
    for _, row in df.iterrows():
        room = row['Room']
        status = row['Live Status']
        if "AVAILABLE" in status: badge = f"<span class='badge badge-avail'>{status}</span>"
        elif "OCCUPIED" in status: badge = f"<span class='badge badge-occ'>{status}</span>"
        else: badge = f"<span class='badge badge-use'>{status}</span>"
            
        temp = f"<span class='metric-val'>{row['Temperature']:.1f}</span><span class='metric-unit'>°C</span>" if pd.notna(row['Temperature']) else "-"
        hum_val = int(row['Humidity']) if pd.notna(row['Humidity']) else 0
        hum_color = "#ffb300" if (hum_val < 30 or hum_val > 60) else "#7c4dff"
        hum = f"<div style='display: flex; align-items: center; gap: 15px;'><div style='flex-grow: 1; background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden;'><div style='width: {hum_val}%; background: {hum_color}; height: 100%; border-radius: 5px; box-shadow: 0 0 10px {hum_color}80;'></div></div><span style='font-weight: 900; font-size: 1.2rem; width: 50px;'>{hum_val}%</span></div>"
        
        voc = f"<span class='metric-val'>{row['VOC Index']:.0f}</span><span class='metric-unit'>idx</span>" if pd.notna(row['VOC Index']) else "-"
        light = f"<span class='metric-val'>{row['Light']:.0f}</span><span class='metric-unit'>lx</span>" if pd.notna(row['Light']) else "-"
        people = f"<span class='metric-val'>{int(row['People'])}</span><span class='metric-unit'>👥</span>" if pd.notna(row['People']) else "-"
        
        html += f"<tr class='fleet-tr'><td class='fleet-td'>{room}</td><td class='fleet-td'>{badge}</td><td class='fleet-td'>{temp}</td><td class='fleet-td'>{hum}</td><td class='fleet-td'>{voc}</td><td class='fleet-td'>{light}</td><td class='fleet-td'>{people}</td></tr>"
        
    html += "</tbody></table>"
    return html

def create_interactive_chart(data, y_col, color, chart_type='line', title='', y_scale_zero=False):
    base = alt.Chart(data).encode(
        x=alt.X('Timestamp:T', title='', axis=alt.Axis(grid=False, labelColor='#a0a5b5', tickCount=5)),
        y=alt.Y(f'{y_col}:Q', title=title, scale=alt.Scale(zero=y_scale_zero), axis=alt.Axis(gridColor='rgba(255,255,255,0.05)', labelColor='#a0a5b5')),
        tooltip=[alt.Tooltip('Timestamp:T', format='%Y-%m-%d %H:%M', title='Time'), alt.Tooltip(f'{y_col}:Q', format='.1f', title=y_col)]
    )
    if chart_type == 'line': 
        line = base.mark_line(color=color, strokeWidth=3)
        area = base.mark_area(
            opacity=0.3,
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color=color, offset=0), alt.GradientStop(color='rgba(0,0,0,0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        )
        chart = (area + line).interactive()
    else: 
        chart = base.mark_area(color=color, opacity=0.8, interpolate='step-after').interactive()
        
    return chart.configure_view(strokeWidth=0).configure_axis(domain=False)

global_df = load_data(SHEET_URL).copy()

# ==========================================
# 4. STATIC SIDEBAR (COMMAND CENTER)
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    
    curr_t, w_desc, high_t, low_t = get_live_weather()
    
    st.markdown(f"""
    <div style="background: rgba(45, 48, 58, 0.4); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.2);">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">{curr_t}°C</h1>
        <p style="margin:0; font-weight: 700; color: #9c27b0; text-transform: uppercase; letter-spacing: 2px;">{w_desc}</p>
        <hr style="border: 1px solid rgba(255,255,255,0.05); margin: 15px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #a0a5b5; font-weight: 500;">H: {high_t}°C | L: {low_t}°C</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not global_df.empty:
        latest_sb = global_df.sort_values('Timestamp', ascending=False).drop_duplicates('Room')
        
        avg_t, avg_h, avg_v = latest_sb['Temperature'].mean(skipna=True), latest_sb['Humidity'].mean(skipna=True), latest_sb['VOC Index'].mean(skipna=True)
        penalty = sum([abs(avg_t - 21) * 3 if pd.notna(avg_t) else 0, abs(avg_h - 45) * 0.5 if pd.notna(avg_h) else 0, (avg_v * 0.1) if pd.notna(avg_v) else 0])
        comfort = max(0, min(100, int(100 - penalty)))
        ring_color = "#9c27b0" if comfort >= 80 else ("#ffb300" if comfort >= 60 else "#ff4b4b")
        
        st.markdown("### 🔋 BUILDING COMFORT")
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 25px;">
            <div style="width: 130px; height: 130px; border-radius: 50%; background: conic-gradient({ring_color} {comfort}%, rgba(255,255,255,0.05) 0); display: flex; justify-content: center; align-items: center; box-shadow: 0 0 20px {ring_color}30;">
                <div style="width: 100px; height: 100px; border-radius: 50%; background-color: #0e1117; display: flex; justify-content: center; align-items: center;"><h2 style="margin:0; font-size: 1.8rem; color: {ring_color};">{comfort}%</h2></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        today_df = global_df[global_df['Timestamp'] >= pd.Timestamp.now().normalize()]
        if not today_df.empty and today_df['People'].sum() > 0:
            st.markdown("### 🏆 TODAY'S MVP")
            st.markdown(f"<div style='background: rgba(45, 48, 58, 0.4); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #00e5ff; border-radius: 10px; padding: 15px; margin-bottom: 25px;'><p style='margin:0; font-size: 0.75rem; color: #a0a5b5; text-transform: uppercase; letter-spacing: 1px; font-weight: 700;'>Highest Traffic Space</p><h4 style='margin:5px 0 0 0; color: #ffffff; letter-spacing: 0.5px;'>{today_df.groupby('Room')['People'].sum().idxmax()}</h4></div>", unsafe_allow_html=True)

        st.markdown("### 🚨 SYSTEM ALERTS")
        alerts = [f"⚠️ <b>{row['Room']}:</b> High VOC" for _, row in latest_sb.iterrows() if pd.notna(row['VOC Index']) and row['VOC Index'] > 250]
        alerts += [f"🔥 <b>{row['Room']}:</b> Too Hot" for _, row in latest_sb.iterrows() if pd.notna(row['Temperature']) and row['Temperature'] > 26]
        
        if not alerts: st.markdown("<div style='background: rgba(30, 58, 47, 0.4); backdrop-filter: blur(10px); border: 1px solid rgba(0, 230, 118, 0.3); border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 20px;'><p style='margin:0; color: #00e676; font-weight: 700; letter-spacing: 1px;'>🟢 ALL SYSTEMS OPTIMAL</p></div>", unsafe_allow_html=True)
        else:
            for alert in alerts: st.markdown(f"<div style='background: rgba(74, 25, 25, 0.4); backdrop-filter: blur(10px); border: 1px solid rgba(255, 75, 75, 0.3); border-left: 4px solid #ff4b4b; border-radius: 10px; padding: 12px; margin-bottom: 10px;'><p style='margin:0; color: #ffca28; font-size: 0.9rem;'>{alert}</p></div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🛠️ DASHBOARD CONTROL")
    st.toggle("▶️ ENABLE AUTO-PILOT (Kiosk Mode)", key="autopilot")
    if st.button("🔄 FORCE FULL REFRESH", width="stretch"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. DASHBOARD ENGINE 
# ==========================================
def render_main_dashboard():
    st.title("🏢 Neat London Showroom")
    df = global_df
    
    if not df.empty:
        tab1, tab2, tab3 = st.tabs(["🌐 FLEET OVERVIEW", "🔍 ROOM DEEP DIVE", "🤖 AI ASSISTANT"])

        with tab1:
            latest = df.sort_values('Timestamp', ascending=False).drop_duplicates('Room').copy()
            latest['Live Status'] = latest.apply(get_smart_status, axis=1)
            
            total_people, rooms_available, avg_voc = int(latest['People'].sum(skipna=True)), int((latest['Live Status'] == "🟢 AVAILABLE").sum()), latest['VOC Index'].mean(skipna=True)
            b_voc_color = "#ff4b4b" if avg_voc > 250 else ("#ffb300" if avg_voc > 150 else "#9c27b0")
            
            h1, h2, h3 = st.columns(3)
            h1.markdown(render_smart_card("TOTAL PEOPLE IN SHOWROOM", f"{total_people} 👥"), unsafe_allow_html=True)
            h2.markdown(render_smart_card("ROOMS CURRENTLY AVAILABLE", f"{rooms_available} 🟢"), unsafe_allow_html=True)
            h3.markdown(render_smart_card("BUILDING AIR QUALITY (VOC)", f"{avg_voc:.0f} 🌬️", b_voc_color), unsafe_allow_html=True)
            
            st.divider()
            st.subheader("LIVE FLEET STATUS")
            st.markdown(render_fleet_table(latest), unsafe_allow_html=True)

        with tab2:
            all_rooms = sorted(df['Room'].unique())
            if st.session_state.kiosk_idx >= len(all_rooms): st.session_state.kiosk_idx = 0

            c_room, c_date, c_grain = st.columns([1.5, 2, 1])
            with c_room: selected_room = st.selectbox("CHOOSE A ROOM:", all_rooms, index=st.session_state.kiosk_idx, disabled=st.session_state.get('autopilot', False))
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
                env_chart_df = resampled.reset_index()
                
                latest_val = f_df.iloc[-1]
                v_voc, v_tmp, v_hum = latest_val['VOC Index'], latest_val['Temperature'], latest_val['Humidity']
                voc_col, tmp_col, hum_col = ("#ff4b4b" if v_voc > 250 else ("#ffb300" if v_voc > 150 else "#9c27b0")), ("#ff4b4b" if v_tmp > 26 else ("#00e5ff" if v_tmp < 16 else "#9c27b0")), ("#ffb300" if (v_hum < 30 or v_hum > 60) else "#9c27b0")

                m1, m2, m3, m4 = st.columns(4)
                m1.markdown(render_smart_card("LATEST TEMP", f"{v_tmp:.1f}°C", tmp_col), unsafe_allow_html=True)
                m2.markdown(render_smart_card("LATEST HUMIDITY", f"{v_hum:.0f}%", hum_col), unsafe_allow_html=True)
                m3.markdown(render_smart_card("LATEST VOC", f"{v_voc:.0f}", voc_col), unsafe_allow_html=True)
                m4.markdown(render_smart_card("LATEST LIGHT", f"{latest_val['Light']:.0f} lx"), unsafe_allow_html=True)
                
                st.divider()
                st.markdown("#### 👥 OCCUPANCY HISTORY")
                occ_chart = create_interactive_chart((f_df["People"].resample(rule).max() if rule else f_df["People"]).reset_index(), 'People', '#aa00ff', 'bar', 'Max People', y_scale_zero=True)
                st.altair_chart(occ_chart.properties(height=180), width="stretch")
                
                st.divider()
                r1_1, r1_2 = st.columns(2)
                with r1_1:
                    st.markdown("#### TEMPERATURE (°C)")
                    st.altair_chart(create_interactive_chart(env_chart_df, 'Temperature', '#b388ff', 'line', '', y_scale_zero=False).properties(height=220), width="stretch")
                with r1_2:
                    st.markdown("#### HUMIDITY (%)")
                    st.altair_chart(create_interactive_chart(env_chart_df, 'Humidity', '#7c4dff', 'line', '', y_scale_zero=False).properties(height=220), width="stretch")

                r2_1, r2_2 = st.columns(2)
                with r2_1:
                    st.markdown("#### AIR QUALITY (VOC)")
                    st.altair_chart(create_interactive_chart(env_chart_df, 'VOC Index', '#651fff', 'line', '', y_scale_zero=True).properties(height=220), width="stretch")
                with r2_2:
                    st.markdown("#### LIGHT LEVELS (LUX)")
                    st.altair_chart(create_interactive_chart(env_chart_df, 'Light', '#e040fb', 'bar', '', y_scale_zero=True).properties(height=220), width="stretch")

                st.divider()
                st.markdown("#### 📅 PEAK UTILIZATION HEATMAP")
                h_data = f_df.copy().reset_index()
                h_data['Hour'], h_data['Day'] = h_data['Timestamp'].dt.hour, h_data['Timestamp'].dt.day_name()
                
                heatmap = alt.Chart(h_data).mark_rect().encode(
                    x=alt.X('Hour:O', title='Hour of Day', axis=alt.Axis(grid=False, labelColor='#a0a5b5')),
                    y=alt.Y('Day:O', title='', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], axis=alt.Axis(grid=False, labelColor='#a0a5b5')),
                    color=alt.Color('max(People):Q', scale=alt.Scale(scheme='purples')),
                    tooltip=['Day', 'Hour', 'max(People)']
                ).properties(height=280).configure_view(strokeWidth=0)
                
                st.altair_chart(heatmap, width="stretch")

            else: st.warning("Select a valid date range to see room data.")

        with tab3:
            st.markdown("### 💬 Chat with the Showroom")
            st.caption("Ask me about room utilization, air quality, or live availability.")
            
            if "messages" not in st.session_state:
                st.session_state.messages = [
                    {"role": "assistant", "content": "Hello! I am your Neat Showroom Assistant. Ask me things like: \n* *'Which is the most utilized room?'*\n* *'What rooms are available right now?'*\n* *'Which room has the worst air quality?'*"}
                ]

            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("Ask a question about the showroom..."):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    response = ""
                    query = prompt.lower()
                    
                    current_status_df = df.sort_values('Timestamp', ascending=False).drop_duplicates('Room')
                    current_status_df['Live Status'] = current_status_df.apply(get_smart_status, axis=1)

                    if "utiliz" in query or "busiest" in query or "popular" in query:
                        pop_room = df.groupby('Room')['People'].sum().idxmax()
                        total_visits = int(df.groupby('Room')['People'].sum().max())
                        response = f"Based on historical data, **{pop_room}** is your most utilized space, with a total detected occupancy count of {total_visits} across all logs."
                    
                    elif "available" in query or "free" in query or "empty" in query:
                        free_rooms = current_status_df[current_status_df['Live Status'] == "🟢 AVAILABLE"]['Room'].tolist()
                        if free_rooms:
                            response = f"Right now, there are {len(free_rooms)} rooms available: **{', '.join(free_rooms)}**."
                        else:
                            response = "It's a full house! All rooms are currently occupied or in use."

                    elif "air" in query or "stuffy" in query or "voc" in query:
                        worst_air = current_status_df.loc[current_status_df['VOC Index'].idxmax()]
                        if worst_air['VOC Index'] > 250:
                            response = f"The air quality in **{worst_air['Room']}** is currently dropping. The VOC index is at {worst_air['VOC Index']:.0f}. You might want to let some fresh air in!"
                        else:
                            response = f"Air quality looks great across the board. The highest VOC level right now is just {worst_air['VOC Index']:.0f} in {worst_air['Room']}."
                    
                    elif "hot" in query or "warm" in query or "temperature" in query:
                        hottest = current_status_df.loc[current_status_df['Temperature'].idxmax()]
                        response = f"The warmest room right now is **{hottest['Room']}** at {hottest['Temperature']:.1f}°C."

                    else:
                        response = "I'm still learning! Try asking me about **availability**, **utilization**, or **air quality**."

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

render_main_dashboard()

# ==========================================
# 6. NON-BLOCKING AUTO-PILOT HANDLER
# ==========================================
if st.session_state.get('autopilot', False):
    @st.fragment(run_every="10s")
    def autopilot_ticker():
        all_rms = sorted(global_df['Room'].unique()) if not global_df.empty else []
        if all_rms: 
            st.session_state.kiosk_idx = (st.session_state.kiosk_idx + 1) % len(all_rms)
            st.rerun()
    autopilot_ticker()
