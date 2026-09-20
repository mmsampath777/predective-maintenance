"""
Network Slicing Metrics Tracker.
Maintains slice-specific message counters, latency averages, and traffic distributions.
"""

import threading

class SliceMetricsTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.slice_stats = {
            "CRITICAL": {"messages": 0, "total_latency": 0.0, "avg_latency_ms": 45.0},
            "MONITORING": {"messages": 0, "total_latency": 0.0, "avg_latency_ms": 120.0},
            "ANALYTICS": {"messages": 0, "total_latency": 0.0, "avg_latency_ms": 850.0}
        }
        
    def record_slice_processed(self, slice_id: str, total_latency_ms: float):
        with self.lock:
            if slice_id in self.slice_stats:
                self.slice_stats[slice_id]["messages"] += 1
                self.slice_stats[slice_id]["total_latency"] += total_latency_ms
                count = self.slice_stats[slice_id]["messages"]
                self.slice_stats[slice_id]["avg_latency_ms"] = round(
                    self.slice_stats[slice_id]["total_latency"] / count, 2
                )
                
    def get_traffic_distribution(self) -> dict:
        with self.lock:
            crit = self.slice_stats["CRITICAL"]["messages"]
            mon = self.slice_stats["MONITORING"]["messages"]
            ana = self.slice_stats["ANALYTICS"]["messages"]
            total = crit + mon + ana
            return {
                "critical_traffic": crit,
                "monitoring_traffic": mon,
                "analytics_traffic": ana,
                "total_traffic": total
            }

slice_metrics_tracker = SliceMetricsTracker()
