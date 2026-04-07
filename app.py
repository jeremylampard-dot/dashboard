import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# --- Page Config ---
st.set_page_config(page_title="Neat London Showroom", layout="wide", page_icon="🏢")

# ==========================================
# FORCED DARK MODE & CHUNKY STYLE
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
    [data-testid="stMetricValue"] { font-weight: 900 !important; color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR: NATIVE WEATHER & SYSTEM STATUS
# ==========================================
with st.sidebar:
    st.markdown("### ☁️ CITY OF LONDON")
    st.markdown(f"""
    <div style="background-color: #2d303a; border: 2px solid #9c27b0; border-radius: 15px; padding: 20px; text-align: center;">
        <h1 style="margin:0; font-size: 3rem; color: #ffffff;">14°C</h1>
        <p style="margin:0; font-weight: 900; color: #9c27b0; text-transform: uppercase;">Cloudy / Overcast</p>
        <hr style="border: 1px solid #404452; margin: 10px 0;">
        <p style="margin:0; font-size: 0.8rem; color: #f0f2f6;">LOW: 9°C | HIGH: 16°C</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    if st.button("🔄 REFRESH & CLEAR CACHE", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- THE UPDATED TITLE ---
st.title("🏢 Neat London Showroom")

# --- DATA LOADING ---
SHEET_URL = "
