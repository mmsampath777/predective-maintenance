"""
MQTT Publisher for IoT Simulators.
Publishes sensor telemetry with timestamp and QoS 1 to MQTT topics.
"""

import json
import time
import uuid
import paho.mqtt.client as mqtt
from backend.middleware.mqtt_config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_DEFAULT_QOS
from backend.middleware.mqtt_metrics import mqtt_metrics

class MQTTPublisher:
    def __init__(self, broker_host=MQTT_BROKER_HOST, broker_port=MQTT_BROKER_PORT):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = f"IoT_Publisher_{uuid.uuid4().hex[:8]}"
        
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        else:
            self.client = mqtt.Client(client_id=self.client_id)
            
        self.connected = False
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            mqtt_metrics.set_broker_status(True)
            print(f"[MQTTPublisher] Connected to broker at {self.broker_host}:{self.broker_port}")
        else:
            self.connected = False
            print(f"[MQTTPublisher] Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False
        print("[MQTTPublisher] Disconnected from broker.")

    def connect(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTTPublisher] Error connecting to broker: {e}")

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass

    def publish_sensor_data(self, machine_id: str, sensor_payload: dict, qos: int = MQTT_DEFAULT_QOS):
        """
        Publishes sensor data to MQTT broker
        Topic: machine/{machine_id}/sensors
        QoS: 1 (At least once delivery)
        """
        topic = f"machine/{machine_id}/sensors"
        
        # Ensure timestamp exists in payload
        if "timestamp" not in sensor_payload:
            sensor_payload["timestamp"] = time.time()
        sensor_payload["machine_id"] = machine_id
        
        payload_str = json.dumps(sensor_payload)
        self.client.publish(topic, payload_str, qos=qos)
        mqtt_metrics.record_publish(topic, qos=qos)
