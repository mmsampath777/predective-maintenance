"""
Local Anomaly Detector for Fog Computing.
Performs edge-level statistical anomaly and threshold checks before/alongside ML prediction.
"""

class LocalAnomalyDetector:
    def __init__(self):
        # Operational envelopes
        self.bounds = {
            "temperature": {"min": 10.0, "max": 110.0, "warn": 75.0, "crit": 95.0},
            "vibration": {"min": 0.0, "max": 15.0, "warn": 5.5, "crit": 8.0},
            "current": {"min": 2.0, "max": 30.0, "warn": 15.0, "crit": 20.0},
            "pressure": {"min": 20.0, "max": 240.0, "warn": 160.0, "crit": 200.0},
            "coolant_level": {"min": 0.0, "max": 100.0, "warn": 30.0, "crit": 15.0}  # Low is bad
        }

    def validate_ranges(self, payload: dict) -> bool:
        """Validate whether sensor readings fall within plausible physical bounds."""
        for param, limits in self.bounds.items():
            if param in payload:
                val = float(payload[param])
                if val < limits["min"] or val > limits["max"]:
                    return False
        return True

    def detect_anomalies(self, payload: dict) -> dict:
        """Detect local anomalies and return severity level and triggers."""
        anomalies = []
        severity = "NORMAL"
        
        temp = float(payload.get("temperature", 45.0))
        vib = float(payload.get("vibration", 2.5))
        curr = float(payload.get("current", 8.5))
        press = float(payload.get("pressure", 100.0))
        cool = float(payload.get("coolant_level", 85.0))
        
        # Check Critical triggers
        if temp >= self.bounds["temperature"]["crit"]:
            anomalies.append(f"Critical temperature: {temp:.1f}°C (Threshold: {self.bounds['temperature']['crit']}°C)")
            severity = "CRITICAL"
        if vib >= self.bounds["vibration"]["crit"]:
            anomalies.append(f"Severe vibration: {vib:.2f} m/s² (Threshold: {self.bounds['vibration']['crit']} m/s²)")
            severity = "CRITICAL"
        if curr >= self.bounds["current"]["crit"]:
            anomalies.append(f"Dangerous current spike: {curr:.1f}A (Threshold: {self.bounds['current']['crit']}A)")
            severity = "CRITICAL"
        if cool <= self.bounds["coolant_level"]["crit"]:
            anomalies.append(f"Critically low coolant: {cool:.1f}%")
            severity = "CRITICAL"

        # Check Warning triggers if not already critical
        if severity != "CRITICAL":
            if temp >= self.bounds["temperature"]["warn"]:
                anomalies.append(f"Elevated temperature: {temp:.1f}°C")
                severity = "WARNING"
            if vib >= self.bounds["vibration"]["warn"]:
                anomalies.append(f"Elevated vibration: {vib:.2f} m/s²")
                severity = "WARNING"
            if curr >= self.bounds["current"]["warn"]:
                anomalies.append(f"Elevated current: {curr:.1f}A")
                severity = "WARNING"
            if cool <= self.bounds["coolant_level"]["warn"]:
                anomalies.append(f"Low coolant level: {cool:.1f}%")
                severity = "WARNING"
                
        return {
            "has_anomaly": (severity != "NORMAL"),
            "severity": severity,
            "anomalies": anomalies
        }

local_anomaly_detector = LocalAnomalyDetector()
