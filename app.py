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
# 🛑 1. PASTE YOUR REAL KEYS HERE 🛑
PULSE_ORG_ID = "YOUR_ORGANIZATION_ID"
PULSE_API_KEY = "YOUR_API_KEY"

# 🛑 2. MAP YOUR FRIENDLY ROOM NAMES TO EXACT NEAT ENDPOINT IDs 🛑
ENDPOINT_MAP = {
    "Boardroom": "paste-endpoint-id-here",
    "Front Booth": "paste-endpoint-id-here",
    "Huddle Space": "paste-endpoint-id-here",
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

# Helper to generate interactive Altair charts
def create_interactive_chart(data, y_col, color, chart_type='line', title='', y_scale_zero=False):
    base = alt.Chart(data).encode(
        x=alt.X('Timestamp:T', title=''),
        y=alt.Y(f'{y_col}:Q', title=title, scale=alt.Scale(zero=y_scale_zero)),
        tooltip=[
            alt.Tooltip('Timestamp:T', format='%Y-%m-%d %H:%M', title='Time'), 
            alt.Tooltip(f'{y_col}:Q', format='.1f', title=y_col)
        ]
    )
    if chart_type == 'line':
        return base.mark_line(color=color, strokeWidth=3).interactive()
    else:
        return base.mark_bar(color=color).interactive()

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
            if pd.notna(row['Temperature']) and row['Temperature'] > 26: alerts.append(f"
