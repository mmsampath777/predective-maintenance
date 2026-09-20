"""
Analytics and Fog vs Cloud Comparative Routes.
"""

from fastapi import APIRouter
from backend.cloud.cloud_processor import cloud_processor
from backend.cloud.cloud_storage import cloud_storage
from backend.network_slicing.slice_manager import slice_manager
from backend.middleware.mqtt_metrics import mqtt_metrics

router = APIRouter(prefix="/api/analytics", tags=["Analytics & Comparison"])

@router.get("/fog-vs-cloud")
def get_fog_vs_cloud_comparison():
    """Return Fog vs Cloud comparative latency and traffic reduction metrics."""
    return cloud_processor.get_comparison_metrics()

@router.get("/network-slice-performance")
def get_slice_performance():
    """Return slice performance metrics and queue characteristics."""
    return {
        "slices": slice_manager.get_all_slice_metrics(),
        "latency_breakdown": slice_manager.get_latency_breakdown()
    }

@router.get("/mqtt-performance")
def get_mqtt_performance():
    """Return MQTT throughput, latency, and reliability metrics."""
    return mqtt_metrics.get_metrics()

@router.get("/alerts")
def get_recent_alerts(limit: int = 20):
    """Return recent historical alerts from cloud database."""
    return cloud_storage.get_recent_alerts(limit=limit)
