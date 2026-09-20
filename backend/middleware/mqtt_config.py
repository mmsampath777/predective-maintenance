"""
MQTT Middleware Configuration
"""
import os

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_KEEPALIVE = 60
MQTT_DEFAULT_QOS = 1

# Topics
TOPIC_ALL_SENSORS = "machine/+/sensors"
TOPIC_MACHINE_SENSORS = "machine/{machine_id}/sensors"
TOPIC_MACHINE_ALERTS = "machine/{machine_id}/alerts"
TOPIC_MACHINE_TEMPERATURE = "machine/{machine_id}/temperature"
TOPIC_MACHINE_VIBRATION = "machine/{machine_id}/vibration"
TOPIC_MACHINE_CURRENT = "machine/{machine_id}/current"
TOPIC_MACHINE_RPM = "machine/{machine_id}/rpm"
TOPIC_MACHINE_PRESSURE = "machine/{machine_id}/pressure"
TOPIC_MACHINE_COOLANT = "machine/{machine_id}/coolant"
