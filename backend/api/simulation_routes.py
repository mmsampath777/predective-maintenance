"""
Simulation and Demo Scenario API Routes.
"""

from fastapi import APIRouter
from backend.simulation.iot_simulator import iot_simulator
from backend.simulation.demo_scenario import demo_controller

router = APIRouter(prefix="/api/simulation", tags=["Simulation & Demo"])

@router.post("/start")
def start_simulation():
    """Start IoT sensor telemetry simulation."""
    iot_simulator.start()
    return {"status": "Simulation running", "machines": iot_simulator.machines}

@router.post("/stop")
def stop_simulation():
    """Stop IoT sensor telemetry simulation."""
    iot_simulator.stop()
    return {"status": "Simulation stopped"}

@router.get("/status")
def get_simulation_status():
    """Get status of simulator and demo scenario controller."""
    sim_status = {
        "running": iot_simulator.running,
        "machines": iot_simulator.machines
    }
    demo_status = demo_controller.get_status()
    return {
        "simulator": sim_status,
        "demo": demo_status
    }

@router.post("/stage/{stage_id}")
def set_demo_stage(stage_id: int):
    """
    Set demo scenario stage:
    Stage 1: Normal Operation (Analytics Slice)
    Stage 2: Warning State (Monitoring Slice)
    Stage 3: Critical State (Critical Slice)
    """
    return demo_controller.set_stage(stage_id)

@router.post("/auto")
def toggle_auto_demo(enable: bool = True, duration: int = 20):
    """Enable or disable automated 3-stage cycling."""
    if enable:
        return demo_controller.start_auto_demo(stage_duration=duration)
    else:
        return demo_controller.stop_auto_demo()

@router.post("/inject")
def inject_custom_telemetry(data: dict):
    """
    Manually inject custom sensor readings to test ML prediction,
    network slicing classification, and alert generation.
    """
    machine_id = data.get("machine_id", "M-001")
    payload = {
        "machine_id": machine_id,
        "temperature": float(data.get("temperature", 45.0)),
        "vibration": float(data.get("vibration", 2.5)),
        "current": float(data.get("current", 8.5)),
        "rpm": int(data.get("rpm", 2200)),
        "pressure": float(data.get("pressure", 100.0)),
        "coolant_level": float(data.get("coolant_level", 85.0)),
        "operating_hours": float(data.get("operating_hours", 2500.0))
    }
    
    # 1. Publish directly to MQTT broker
    iot_simulator.publisher.publish_sensor_data(machine_id, payload)
    
    # 2. Return immediate classification preview
    from backend.network_slicing.traffic_classifier import traffic_classifier
    from backend.fog.fog_processor import fog_processor
    
    dummy_mqtt_msg = {
        "mqtt_topic": f"machine/{machine_id}/sensors",
        "mqtt_qos": 1,
        "payload": payload
    }
    classified = traffic_classifier.classify(dummy_mqtt_msg)
    fog_result = fog_processor.process(classified)
    
    return {
        "status": "Injected successfully to MQTT",
        "payload": payload,
        "assigned_slice": classified["slice_id"],
        "priority": classified["priority_name"],
        "failure_probability": classified["failure_probability"],
        "health_status": fog_result.get("health_status"),
        "alert": fog_result.get("alert"),
        "recommendation": fog_result.get("recommendation")
    }

