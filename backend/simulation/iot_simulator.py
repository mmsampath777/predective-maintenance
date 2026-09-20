"""
IoT Telemetry Simulator.
Generates industrial sensor data for simulated machines and publishes via MQTT.
"""

import time
import random
import threading
from backend.middleware.mqtt_publisher import MQTTPublisher

class IoTSimulator:
    def __init__(self, machines=None):
        self.machines = machines or ["M-001", "M-002", "M-003", "M-004"]
        self.publisher = MQTTPublisher()
        self.running = False
        self.thread = None
        self.interval = 0.5  # Generate ~2-4 msg/sec per machine
        
        # Machine states dictionary: {machine_id: state_config}
        self.machine_states = {
            m: {
                "operating_hours": random.uniform(500, 4500),
                "temp_base": 45.0,
                "vib_base": 2.2,
                "curr_base": 8.5,
                "rpm_base": 2200,
                "press_base": 100.0,
                "coolant_base": 85.0,
                "health_override": None  # "NORMAL", "WARNING", "CRITICAL"
            } for m in self.machines
        }

    def set_machine_override(self, machine_id: str, state: str):
        """Override specific machine state: NORMAL, WARNING, or CRITICAL."""
        if machine_id in self.machine_states:
            self.machine_states[machine_id]["health_override"] = state

    def generate_reading(self, machine_id: str) -> dict:
        state = self.machine_states[machine_id]
        state["operating_hours"] += 0.01
        
        override = state["health_override"]
        
        if override == "CRITICAL":
            # Stage 3: Critical State
            temp = random.normalvariate(96.0, 3.0)
            vib = random.normalvariate(9.2, 0.8)
            curr = random.normalvariate(22.5, 1.5)
            rpm = random.normalvariate(1320, 150)
            press = random.normalvariate(195.0, 15.0)
            cool = max(5.0, random.normalvariate(16.0, 5.0))
        elif override == "WARNING":
            # Stage 2: Warning State
            temp = random.normalvariate(73.0, 3.5)
            vib = random.normalvariate(6.0, 0.6)
            curr = random.normalvariate(15.5, 1.2)
            rpm = random.normalvariate(1820, 120)
            press = random.normalvariate(152.0, 12.0)
            cool = max(25.0, random.normalvariate(48.0, 8.0))
        else:
            # Stage 1: Normal Operation
            temp = random.normalvariate(45.0, 4.0)
            vib = random.normalvariate(2.2, 0.5)
            curr = random.normalvariate(8.5, 1.0)
            rpm = random.normalvariate(2200, 80)
            press = random.normalvariate(100.0, 8.0)
            cool = min(100.0, random.normalvariate(85.0, 5.0))

        return {
            "machine_id": machine_id,
            "timestamp": time.time(),
            "temperature": round(temp, 2),
            "vibration": round(vib, 2),
            "current": round(curr, 2),
            "rpm": int(rpm),
            "pressure": round(press, 2),
            "coolant_level": round(cool, 1),
            "operating_hours": round(state["operating_hours"], 1)
        }

    def start(self):
        if self.running:
            return
        self.publisher.connect()
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print("[IoTSimulator] Sensor simulator started.")

    def stop(self):
        self.running = False
        self.publisher.disconnect()
        print("[IoTSimulator] Sensor simulator stopped.")

    def _run_loop(self):
        while self.running:
            try:
                for m_id in self.machines:
                    payload = self.generate_reading(m_id)
                    self.publisher.publish_sensor_data(m_id, payload)
                time.sleep(self.interval)
            except Exception as e:
                print(f"[IoTSimulator] Error in simulation loop: {e}")
                time.sleep(1.0)

iot_simulator = IoTSimulator()
