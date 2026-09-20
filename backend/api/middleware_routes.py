"""
MQTT Middleware API Routes.
"""

from fastapi import APIRouter
from backend.middleware.mqtt_metrics import mqtt_metrics

router = APIRouter(prefix="/api/middleware", tags=["MQTT Middleware"])

@router.get("/status")
def get_middleware_status():
    """Return MQTT broker connection and message throughput stats."""
    return mqtt_metrics.get_metrics()

@router.get("/topics")
def get_topic_stats():
    """Return list of active topics and message counts."""
    return mqtt_metrics.get_topic_stats()

@router.get("/qos-stats")
def get_qos_stats():
    """Return QoS distribution metrics (QoS 0, 1, 2)."""
    metrics = mqtt_metrics.get_metrics()
    return metrics.get("qos_distribution", {"qos_0": 0, "qos_1": 0, "qos_2": 0})
