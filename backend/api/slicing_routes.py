"""
Network Slicing API Routes.
"""

from fastapi import APIRouter
from backend.network_slicing.slice_manager import slice_manager
from backend.network_slicing.slice_metrics import slice_metrics_tracker

router = APIRouter(prefix="/api/network", tags=["Network Slicing"])

@router.get("/slices")
def get_all_slices():
    """Return metrics for all 3 virtual network slices."""
    return slice_manager.get_all_slice_metrics()

@router.get("/slices/{slice_id}/metrics")
def get_slice_detail(slice_id: str):
    """Return detailed metrics for a specific slice (CRITICAL, MONITORING, or ANALYTICS)."""
    return slice_manager.get_slice_metrics(slice_id)

@router.get("/traffic")
def get_traffic_distribution():
    """Return traffic count per slice and total throughput."""
    return slice_metrics_tracker.get_traffic_distribution()

@router.get("/latency")
def get_latency_measurements():
    """Return breakdown of MQTT latency, slice queue latency, and Fog processing latency."""
    return slice_manager.get_latency_breakdown()
