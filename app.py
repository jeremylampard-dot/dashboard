import streamlit as st
import pandas as pd
import altair as alt
import requests
import time
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

@st.cache_data(ttl=300) 
def get_neat_raw_data(room_name):
    """Fetches the raw JSON payload from the Neat Pulse API."""
    endpoint_id = ENDPOINT_MAP.get(room_name)
    if not endpoint_id or endpoint_id == "paste-endpoint-id-here": 
        return {"Status": "Error", "Message": f"No valid Endpoint ID mapped for '{room_name}' in the script."}
        
    api_url = f"https://api.pulse.neat.no/v1/orgs/{PULSE_ORG_ID}/endpoints/{endpoint_id}"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}", "Accept": "application/json"}
    
    try:
        response = requests.get(api_url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"Status": "Offline / Error", "Details": str(e)}

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
    html += "</
