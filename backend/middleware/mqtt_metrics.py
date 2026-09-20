"""
MQTT Middleware Metrics Tracker
Thread-safe metrics collection for MQTT broker and clients.
"""

import time
import threading
from collections import deque

class MQTTMetricsTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.broker_status = "DISCONNECTED"
        self.published_messages_total = 0
        self.received_messages_total = 0
        self.active_topics = {}  # topic -> {"count": int, "last_time": float}
        self.qos_distribution = {"qos_0": 0, "qos_1": 0, "qos_2": 0}
        
        self.latencies = deque(maxlen=200)
        self.publish_timestamps = deque(maxlen=300)
        self.start_time = time.time()
        self.last_connected_time = None
        
    def set_broker_status(self, connected: bool):
        with self.lock:
            self.broker_status = "CONNECTED" if connected else "DISCONNECTED"
            if connected and not self.last_connected_time:
                self.last_connected_time = time.time()
                
    def record_publish(self, topic: str, qos: int = 1):
        with self.lock:
            self.published_messages_total += 1
            now = time.time()
            self.publish_timestamps.append(now)
            
            qos_key = f"qos_{qos}"
            if qos_key in self.qos_distribution:
                self.qos_distribution[qos_key] += 1
            else:
                self.qos_distribution["qos_1"] += 1
                
            if topic not in self.active_topics:
                self.active_topics[topic] = {"count": 0, "last_time": now}
            self.active_topics[topic]["count"] += 1
            self.active_topics[topic]["last_time"] = now

    def record_receive(self, topic: str, qos: int, latency_ms: float):
        with self.lock:
            self.received_messages_total += 1
            self.latencies.append(latency_ms)
            now = time.time()
            if topic not in self.active_topics:
                self.active_topics[topic] = {"count": 0, "last_time": now}
            self.active_topics[topic]["count"] += 1
            self.active_topics[topic]["last_time"] = now

    def get_metrics(self) -> dict:
        with self.lock:
            now = time.time()
            # Calculate messages per second over last 5 seconds
            recent_publishes = [t for t in self.publish_timestamps if now - t <= 5.0]
            msg_rate = round(len(recent_publishes) / 5.0, 1) if recent_publishes else 0.0
            
            avg_lat = round(sum(self.latencies) / len(self.latencies), 2) if self.latencies else 12.0
            uptime = int(now - self.last_connected_time) if self.last_connected_time else 0
            
            return {
                "broker_status": self.broker_status,
                "broker_connected": (self.broker_status == "CONNECTED"),
                "published_messages": self.published_messages_total,
                "received_messages": self.received_messages_total,
                "active_topics": len(self.active_topics),
                "messages_per_second": msg_rate,
                "avg_latency_ms": avg_lat,
                "avg_mqtt_latency_ms": avg_lat,
                "connection_uptime": uptime,
                "qos_distribution": dict(self.qos_distribution)
            }

    def get_topic_stats(self) -> list:
        with self.lock:
            stats = []
            for t, data in self.active_topics.items():
                stats.append({
                    "topic": t,
                    "message_count": data["count"],
                    "last_message_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(data["last_time"]))
                })
            return sorted(stats, key=lambda x: x["message_count"], reverse=True)

mqtt_metrics = MQTTMetricsTracker()
