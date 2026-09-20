"""
One-Click Launcher for IoT Predictive Maintenance System.
Starts the complete system: Embedded MQTT Broker, Fog Node, Network Slicing,
IoT Simulator, and Web Dashboard.
"""

import os
import sys
import webbrowser
import threading
import time

# Ensure workspace root is in python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def open_browser():
    time.sleep(1.8)
    url = "http://localhost:8000"
    print(f"\n========================================================")
    print(f"🚀 Dashboard launched! Opening in browser: {url}")
    print(f"========================================================\n")
    webbrowser.open(url)

if __name__ == "__main__":
    import uvicorn
    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run FastAPI application
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
