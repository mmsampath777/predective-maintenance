"""
Fog Computing API Routes.
"""

from fastapi import APIRouter
from backend.fog.fog_node import fog_node
from backend.fog.fog_metrics import fog_metrics

router = APIRouter(prefix="/api/fog", tags=["Fog Computing"])

@router.get("/status")
def get_fog_status():
    """Return high-level Fog node metrics and status."""
    metrics = fog_metrics.get_metrics()
    return {
        "status": metrics["status"],
        "messages_processed": metrics["messages_processed"],
        "processing_rate": metrics["processing_rate"],
        "critical_messages": metrics["critical_messages"],
        "monitoring_messages": metrics["monitoring_messages"],
        "analytics_messages": metrics["analytics_messages"],
        "avg_processing_time_ms": metrics["avg_processing_time_ms"],
        "uptime_seconds": metrics["uptime_seconds"],
        "last_heartbeat": metrics["last_heartbeat"]
    }

@router.get("/metrics")
def get_fog_metrics():
    """Return detailed Fog node operational metrics."""
    return fog_metrics.get_metrics()

@router.get("/health")
def get_fog_health():
    """Return health check of Fog node layer."""
    metrics = fog_metrics.get_metrics()
    return {
        "status": "HEALTHY" if metrics["status"] == "ONLINE" else "DEGRADED",
        "cpu_usage": "28%",
        "memory_usage": "145MB",
        "fog_node_active": fog_node.running,
        "uptime_seconds": metrics["uptime_seconds"]
    }

@router.get("/recent")
def get_recent_results(limit: int = 20):
    """Return recent processed inference results from Fog node."""
    return fog_node.get_recent_results(limit=limit)
