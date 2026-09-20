"""
Integration Tests for MQTT Slicing, Priority Queues, and Pipeline.
"""

import pytest
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.network_slicing.slice_manager import slice_manager
from backend.network_slicing.traffic_classifier import traffic_classifier
from backend.fog.fog_processor import fog_processor

def test_traffic_classification():
    """Verify that messages are classified into correct slices based on conditions."""
    # 1. Normal message -> ANALYTICS (Priority 3)
    normal_msg = {
        "mqtt_topic": "machine/M-001/sensors",
        "mqtt_qos": 1,
        "payload": {
            "machine_id": "M-001",
            "temperature": 45.0,
            "vibration": 2.2,
            "current": 8.5,
            "rpm": 2200,
            "pressure": 100,
            "coolant_level": 85,
            "operating_hours": 500
        }
    }
    classified_norm = traffic_classifier.classify(normal_msg)
    assert classified_norm["slice_id"] == "ANALYTICS"
    assert classified_norm["priority"] == 3

    # 2. Critical message -> CRITICAL (Priority 1)
    crit_msg = {
        "mqtt_topic": "machine/M-001/sensors",
        "mqtt_qos": 1,
        "payload": {
            "machine_id": "M-001",
            "temperature": 98.0,
            "vibration": 9.2,
            "current": 23.0,
            "rpm": 1200,
            "pressure": 200,
            "coolant_level": 15,
            "operating_hours": 9000
        }
    }
    classified_crit = traffic_classifier.classify(crit_msg)
    assert classified_crit["slice_id"] == "CRITICAL"
    assert classified_crit["priority"] == 1

def test_priority_queue_dispatching():
    """Verify that critical slice messages are prioritized over monitoring and analytics."""
    slice_manager.set_fog_processor(fog_processor)
    
    # Enqueue Analytics first, then Monitoring, then Critical
    norm_msg = {
        "mqtt_topic": "machine/M-003/sensors", "mqtt_qos": 1, "mqtt_latency_ms": 10.0,
        "payload": {"machine_id": "M-003", "temperature": 40.0, "vibration": 2.0, "current": 8.0, "rpm": 2200, "pressure": 100, "coolant_level": 90, "operating_hours": 100}
    }
    warn_msg = {
        "mqtt_topic": "machine/M-002/sensors", "mqtt_qos": 1, "mqtt_latency_ms": 12.0,
        "payload": {"machine_id": "M-002", "temperature": 75.0, "vibration": 6.2, "current": 16.0, "rpm": 1800, "pressure": 150, "coolant_level": 45, "operating_hours": 4000}
    }
    crit_msg = {
        "mqtt_topic": "machine/M-001/sensors", "mqtt_qos": 1, "mqtt_latency_ms": 8.0,
        "payload": {"machine_id": "M-001", "temperature": 99.0, "vibration": 9.5, "current": 24.0, "rpm": 1100, "pressure": 210, "coolant_level": 10, "operating_hours": 9500}
    }
    
    slice_manager.classify_and_queue(norm_msg)
    slice_manager.classify_and_queue(warn_msg)
    slice_manager.classify_and_queue(crit_msg)
    
    # Process queues
    processed = slice_manager.process_queues()
    assert len(processed) == 3
    
    # Verify execution order: CRITICAL first, then MONITORING, then ANALYTICS
    assert processed[0]["slice_id"] == "CRITICAL"
    assert processed[1]["slice_id"] == "MONITORING"
    assert processed[2]["slice_id"] == "ANALYTICS"
    
    # Verify latency metrics were attached
    assert "total_latency_ms" in processed[0]
    assert processed[0]["total_latency_ms"] > 0
