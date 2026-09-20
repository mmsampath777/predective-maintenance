"""
Unit Tests for Fog Node Processor and ML Model.
"""

import pytest
import os
import sys

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.models.ml_model import predictor
from backend.fog.fog_processor import fog_processor
from backend.fog.anomaly_detector import local_anomaly_detector

def test_ml_model_prediction_normal():
    """Test ML model outputs low failure probability for normal values."""
    normal_payload = {
        "temperature": 45.0,
        "vibration": 2.2,
        "current": 8.5,
        "rpm": 2200,
        "pressure": 100,
        "coolant_level": 85,
        "operating_hours": 1000
    }
    prob = predictor.predict_failure_probability(normal_payload)
    assert 0.0 <= prob <= 0.40, f"Expected low failure prob, got {prob}"
    assert predictor.classify_health(prob) == "HEALTHY"

def test_ml_model_prediction_critical():
    """Test ML model outputs high failure probability for critical values."""
    critical_payload = {
        "temperature": 98.0,
        "vibration": 9.5,
        "current": 23.5,
        "rpm": 1200,
        "pressure": 200,
        "coolant_level": 12,
        "operating_hours": 8500
    }
    prob = predictor.predict_failure_probability(critical_payload)
    assert prob >= 0.70, f"Expected high failure prob, got {prob}"
    assert predictor.classify_health(prob) == "CRITICAL"

def test_local_anomaly_detection():
    """Test edge anomaly detector identifies threshold violations."""
    anom = local_anomaly_detector.detect_anomalies({
        "temperature": 99.0,
        "vibration": 9.0,
        "current": 22.0,
        "pressure": 100.0,
        "coolant_level": 80.0
    })
    assert anom["has_anomaly"] is True
    assert anom["severity"] == "CRITICAL"
    assert len(anom["anomalies"]) >= 2

def test_fog_processor_alert_generation():
    """Test Fog Processor generates critical alert and recommendation for severe state."""
    msg = {
        "slice_id": "CRITICAL",
        "priority": 1,
        "failure_probability": 0.92,
        "payload": {
            "machine_id": "M-001",
            "temperature": 97.0,
            "vibration": 9.2,
            "current": 22.5,
            "rpm": 1300,
            "pressure": 195,
            "coolant_level": 15,
            "operating_hours": 8000
        }
    }
    result = fog_processor.process(msg)
    assert result["fog_processed"] is True
    assert result["health_status"] == "CRITICAL"
    assert result["alert"] is not None
    assert result["alert"]["severity"] == "CRITICAL"
    assert "Stop machine" in result["recommendation"]
    assert result["send_to_cloud"] is True  # Critical synced to cloud
