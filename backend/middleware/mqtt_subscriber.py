"""
MQTT Subscriber for Fog Node.
Subscribes to machine/+/sensors, calculates latency, and dispatches to Slice Manager.
"""

import json
import time
import uuid
import paho.mqtt.client as mqtt
from backend.middleware.mqtt_config import MQTT_BROKER_HOST, MQTT_BROKER_PORT, TOPIC_ALL_SENSORS
from backend.middleware.mqtt_metrics import mqtt_metrics

class MQTTSubscriber:
    def __init__(self, broker_host=MQTT_BROKER_HOST, broker_port=MQTT_BROKER_PORT, on_message_callback=None):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.on_message_callback = on_message_callback
        self.client_id = f"Fog_Subscriber_{uuid.uuid4().hex[:8]}"
        
        if hasattr(mqtt, "CallbackAPIVersion"):
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        else:
            self.client = mqtt.Client(client_id=self.client_id)
            
        self.connected = False
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def set_callback(self, callback):
        self.on_message_callback = callback

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.connected = True
            mqtt_metrics.set_broker_status(True)
            self.client.subscribe(TOPIC_ALL_SENSORS, qos=1)
            print(f"[MQTTSubscriber] Connected and subscribed to '{TOPIC_ALL_SENSORS}'")
        else:
            self.connected = False
            print(f"[MQTTSubscriber] Failed to connect, return code {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.connected = False
        print("[MQTTSubscriber] Disconnected from broker.")

    def _on_message(self, client, userdata, msg):
        try:
            received_at = time.time()
            payload = json.loads(msg.payload.decode("utf-8"))
            
            # Calculate actual MQTT latency
            pub_time = payload.get("timestamp", received_at)
            # If timestamp is ISO string or float
            if isinstance(pub_time, str):
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(pub_time.replace("Z", "+00:00"))
                    pub_timestamp = dt.timestamp()
                except Exception:
                    pub_timestamp = received_at
            else:
                pub_timestamp = float(pub_time)
                
            latency_ms = max(0.5, (received_at - pub_timestamp) * 1000.0)
            
            # Record metrics
            mqtt_metrics.record_receive(msg.topic, msg.qos, latency_ms)
            
            message_obj = {
                "mqtt_topic": msg.topic,
                "mqtt_qos": msg.qos,
                "payload": payload,
                "received_at": received_at,
                "mqtt_latency_ms": round(latency_ms, 2)
            }
            
            if self.on_message_callback:
                self.on_message_callback(message_obj)
        except Exception as e:
            print(f"[MQTTSubscriber] Error processing incoming message: {e}")

    def start(self):
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print(f"[MQTTSubscriber] Connect error: {e}")

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception:
            pass
