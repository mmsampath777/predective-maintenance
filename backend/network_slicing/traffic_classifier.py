"""
Traffic Classifier for Network Slicing.
Analyzes incoming telemetry, predicts failure probability using ML,
and assigns messages to CRITICAL, MONITORING, or ANALYTICS slices.
"""

import time
from backend.models.ml_model import predictor
from backend.network_slicing.slice_config import (
    SLICE_CRITICAL, SLICE_MONITORING, SLICE_ANALYTICS, PRIORITY_MAP,
    CRITICAL_FAILURE_PROB_THRESHOLD, MONITORING_FAILURE_PROB_THRESHOLD,
    CRITICAL_TEMP_THRESHOLD, CRITICAL_VIBRATION_THRESHOLD, CRITICAL_CURRENT_THRESHOLD,
    WARNING_TEMP_THRESHOLD, WARNING_VIBRATION_THRESHOLD, WARNING_CURRENT_THRESHOLD
)

class TrafficClassifier:
    def __init__(self):
        self.predictor = predictor

    def classify(self, mqtt_message: dict) -> dict:
        """
        Analyze message payload and assign to appropriate slice.
        """
        payload = mqtt_message.get("payload", {})
        temp = float(payload.get("temperature", 45.0))
        vib = float(payload.get("vibration", 2.5))
        curr = float(payload.get("current", 8.5))
        press = float(payload.get("pressure", 100.0))
        
        # 1. Evaluate with ML Model
        failure_prob = self.predictor.predict_failure_probability(payload)
        
        # 2. Check for severe sensor violations
        has_critical_anomaly = (
            temp >= CRITICAL_TEMP_THRESHOLD or
            vib >= CRITICAL_VIBRATION_THRESHOLD or
            curr >= CRITICAL_CURRENT_THRESHOLD or
            failure_prob >= CRITICAL_FAILURE_PROB_THRESHOLD
        )
        
        has_warning_anomaly = (
            temp >= WARNING_TEMP_THRESHOLD or
            vib >= WARNING_VIBRATION_THRESHOLD or
            curr >= WARNING_CURRENT_THRESHOLD or
            failure_prob >= MONITORING_FAILURE_PROB_THRESHOLD
        )
        
        if has_critical_anomaly:
            slice_id = SLICE_CRITICAL
            priority = PRIORITY_MAP[SLICE_CRITICAL]
            # Ensure probability aligns with critical range
            failure_prob = max(failure_prob, 0.72)
        elif has_warning_anomaly:
            slice_id = SLICE_MONITORING
            priority = PRIORITY_MAP[SLICE_MONITORING]
            failure_prob = max(0.42, min(failure_prob, 0.69))
        else:
            slice_id = SLICE_ANALYTICS
            priority = PRIORITY_MAP[SLICE_ANALYTICS]
            failure_prob = min(failure_prob, 0.38)
            
        classified_message = dict(mqtt_message)
        classified_message["slice_id"] = slice_id
        classified_message["priority"] = priority
        classified_message["priority_name"] = "HIGH" if priority == 1 else ("MEDIUM" if priority == 2 else "LOW")
        classified_message["failure_probability"] = round(failure_prob, 4)
        classified_message["classified_at"] = time.time()
        
        return classified_message

traffic_classifier = TrafficClassifier()
