import streamlit as st
import os
import sys
import time
import json
import requests
from datetime import datetime

# Configuration (mirrored from rla2a.py)
CONFIG = {
    "VERSION": "4.0.0-COMBINED-WINDOWS-FINAL",
    "SYSTEM_NAME": "RL-A2A Combined Enhanced",
    "SERVER_HOST": os.getenv("A2A_HOST", "localhost"),
    "SERVER_PORT": int(os.getenv("A2A_PORT", "8000")),
    "DASHBOARD_PORT": int(os.getenv("DASHBOARD_PORT", "8501")),
    "ENABLE_AI": True,  # Assumed true for dashboard
    "DEBUG": os.getenv("DEBUG", "false").lower() == "true"
}

# Helper to check if server is running
def check_server_status():
    try:
        response = requests.get(f"http://{CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}/status", timeout=2)
        if response.status_code == 200:
            return True, response.json()
    except:
        pass
    return False, None

def main():
    st.set_page_config(
        page_title="RL-A2A Enhanced Dashboard",
        page_icon="[AI]",
        layout="wide"
    )
    
    st.title(f"[AI] {CONFIG['SYSTEM_NAME']}")
    st.markdown("**Advanced Agent-to-Agent Communication System**")
    
    # Check connection
    server_online, server_status = check_server_status()
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("System Version", CONFIG["VERSION"])
    with col2:
        st.metric("Server Status", "ONLINE" if server_online else "OFFLINE", 
                 delta="Connected" if server_online else "Disconnected",
                 delta_color="normal" if server_online else "inverse")
    with col3:
        if server_status:
            st.metric("Active Agents", server_status.get("agents_count", 0))
        else:
            st.metric("Active Agents", "N/A")
    with col4:
        if server_status:
            st.metric("AI Providers", len(server_status.get("ai_providers", [])))
        else:
            st.metric("AI Providers", "N/A")

    if not server_online:
        st.warning(f"⚠️ Server is not reachable at http://{CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}. Please start the server first.")
        st.code("python rla2a.py server")
        return

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Agents", "System Health", "Control Panel"])
    
    with tab1:
        st.subheader("Active Agents")
        try:
            response = requests.get(f"http://{CONFIG['SERVER_HOST']}:{CONFIG['SERVER_PORT']}/agents")
            if response.status_code == 200:
                agents = response.json().get("agents", [])
                if agents:
                    for agent in agents:
                        with st.expander(f"🤖 {agent['name']} ({agent['role']})"):
                            st.json(agent)
                else:
                    st.info("No agents currently active.")
        except Exception as e:
            st.error(f"Error fetching agents: {e}")

    with tab2:
        st.subheader("System Health")
        if server_status:
            st.json(server_status)
            
    with tab3:
        st.subheader("Quick Actions")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Create Demo Agents"):
                try:
                    # We can't easily trigger this via API unless we add an endpoint, 
                    # but for now we can just show the command.
                    # Or if we have an endpoint for it.
                    st.info("Run this command in terminal: python rla2a.py server --demo-agents 3")
                except:
                    pass
        with col_b:
            if st.button("Refresh Data"):
                st.rerun()

if __name__ == "__main__":
    main()
