"""
Main FastAPI Application.
Orchestrates IoT Simulation, MQTT Middleware, Network Slicing, Fog Computing,
Cloud Layer, and Real-Time WebSocket Streaming.
"""

import os
import sys
import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure workspace is on python path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.middleware.embedded_broker import EmbeddedMQTTBroker
from backend.fog.fog_node import fog_node
from backend.cloud.cloud_processor import cloud_processor
from backend.simulation.iot_simulator import iot_simulator
from backend.simulation.demo_scenario import demo_controller
from backend.middleware.mqtt_metrics import mqtt_metrics
from backend.network_slicing.slice_manager import slice_manager

# API Routers
from backend.api.fog_routes import router as fog_router
from backend.api.middleware_routes import router as middleware_router
from backend.api.slicing_routes import router as slicing_router
from backend.api.analytics_routes import router as analytics_router
from backend.api.simulation_routes import router as simulation_router

embedded_broker = EmbeddedMQTTBroker(host="0.0.0.0", port=1883)
connected_websockets = set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Start Embedded MQTT Broker (falls back gracefully if external Mosquitto is running)
    embedded_broker.start()
    await asyncio.sleep(0.5)
    
    # 2. Wire Fog Node with Cloud Processor
    fog_node.set_cloud_forwarder(cloud_processor)
    
    # 3. Start Fog Node and MQTT Subscriber
    fog_node.start()
    await asyncio.sleep(0.5)
    
    # 4. Start IoT Sensor Simulator
    iot_simulator.start()
    print("[App] System components started successfully.")
    
    # 5. Start background WebSocket broadcast task
    broadcast_task = asyncio.create_task(websocket_broadcast_loop())
    
    yield
    
    # Shutdown
    broadcast_task.cancel()
    iot_simulator.stop()
    fog_node.stop()
    embedded_broker.stop()
    print("[App] System shutdown complete.")

app = FastAPI(
    title="IoT Predictive Maintenance with Fog Computing & Network Slicing",
    description="Real-time 3-layer architecture with MQTT middleware and prioritized virtual network slices.",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(fog_router)
app.include_router(middleware_router)
app.include_router(slicing_router)
app.include_router(analytics_router)
app.include_router(simulation_router)

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            # Keep-alive receive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
    except Exception:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

async def websocket_broadcast_loop():
    """Broadcast real-time system metrics to all connected dashboard clients every second."""
    while True:
        try:
            if connected_websockets:
                payload = {
                    "timestamp": time.time(),
                    "fog": fog_node.get_status(),
                    "middleware": mqtt_metrics.get_metrics(),
                    "slices": slice_manager.get_all_slice_metrics(),
                    "latency_breakdown": slice_manager.get_latency_breakdown(),
                    "comparison": cloud_processor.get_comparison_metrics(),
                    "demo": demo_controller.get_status(),
                    "recent_events": fog_node.get_recent_results(limit=15)
                }
                
                # Send to all connected websockets
                dead_sockets = set()
                for ws in list(connected_websockets):
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        dead_sockets.add(ws)
                for ws in dead_sockets:
                    connected_websockets.discard(ws)
                    
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[WebSocket] Broadcast error: {e}")
            await asyncio.sleep(1.0)

# Serve Frontend static files if directory exists
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=False)
