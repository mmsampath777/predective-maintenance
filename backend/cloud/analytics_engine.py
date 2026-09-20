"""
Historical Analytics Engine.
Provides aggregate metrics and historical queries for cloud reporting.
"""

from backend.cloud.cloud_storage import cloud_storage

class AnalyticsEngine:
    def __init__(self):
        self.storage = cloud_storage

    def get_summary_report(self) -> dict:
        alerts = self.storage.get_recent_alerts(limit=50)
        critical_count = sum(1 for a in alerts if a.get("severity") == "CRITICAL")
        warning_count = sum(1 for a in alerts if a.get("severity") == "WARNING")
        
        return {
            "total_alerts_recorded": len(alerts),
            "critical_alerts_recorded": critical_count,
            "warning_alerts_recorded": warning_count,
            "recent_alerts": alerts[:10]
        }

analytics_engine = AnalyticsEngine()
