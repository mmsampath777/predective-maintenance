"""
Fog Node Metrics Tracker.
Maintains live operational metrics for Fog Node processing.
"""

import time
import threading
from collections import deque

class FogMetricsTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.status = "ONLINE"
        self.start_time = time.time()
        self.last_heartbeat = time.time()
        
        self.messages_processed = 0
        self.critical_messages = 0
        self.monitoring_messages = 0
        self.analytics_messages = 0
        self.alerts_generated = 0
        
        self.processing_times = deque(maxlen=200)
        self.processed_timestamps = deque(maxlen=300)

    def record_heartbeat(self):
        with self.lock:
            self.last_heartbeat = time.time()
            self.status = "ONLINE"

    def record_processed(self, slice_id: str, proc_time_ms: float, has_alert: bool = False):
        with self.lock:
            now = time.time()
            self.messages_processed += 1
            self.last_heartbeat = now
            self.processing_times.append(proc_time_ms)
            self.processed_timestamps.append(now)
            
            if slice_id == "CRITICAL":
                self.critical_messages += 1
            elif slice_id == "MONITORING":
                self.monitoring_messages += 1
            else:
                self.analytics_messages += 1
                
            if has_alert:
                self.alerts_generated += 1

    def get_metrics(self) -> dict:
        with self.lock:
            now = time.time()
            # Calculate processing rate over last 5 seconds
            recent = [t for t in self.processed_timestamps if now - t <= 5.0]
            rate = round(len(recent) / 5.0, 1) if recent else 0.0
            
            avg_time = round(sum(self.processing_times) / len(self.processing_times), 2) if self.processing_times else 45.0
            uptime = int(now - self.start_time)
            
            return {
                "status": self.status,
                "messages_processed": self.messages_processed,
                "processing_rate": rate,
                "processing_rate_msg_per_sec": rate,
                "critical_messages": self.critical_messages,
                "monitoring_messages": self.monitoring_messages,
                "analytics_messages": self.analytics_messages,
                "avg_processing_time_ms": avg_time,
                "alerts_generated": self.alerts_generated,
                "uptime_seconds": uptime,
                "last_heartbeat": self.last_heartbeat
            }

fog_metrics = FogMetricsTracker()
