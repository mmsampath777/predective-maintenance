"""
Network Slice Manager.
Coordinates classification, priority-based queuing (CRITICAL, MONITORING, ANALYTICS),
and prioritized queue dispatching.
"""

import time
from backend.network_slicing.slice_config import SLICE_CRITICAL, SLICE_MONITORING, SLICE_ANALYTICS
from backend.network_slicing.slice_queue import SliceQueue
from backend.network_slicing.traffic_classifier import traffic_classifier
from backend.network_slicing.slice_metrics import slice_metrics_tracker

class NetworkSliceManager:
    def __init__(self, fog_processor=None):
        self.fog_processor = fog_processor
        self.classifier = traffic_classifier
        self.metrics_tracker = slice_metrics_tracker
        
        # 3 Virtual Slices with Priority Queues
        self.critical_queue = SliceQueue(SLICE_CRITICAL, priority_level=1)
        self.monitoring_queue = SliceQueue(SLICE_MONITORING, priority_level=2)
        self.analytics_queue = SliceQueue(SLICE_ANALYTICS, priority_level=3)
        
        self.queues = {
            SLICE_CRITICAL: self.critical_queue,
            SLICE_MONITORING: self.monitoring_queue,
            SLICE_ANALYTICS: self.analytics_queue
        }
        
    def set_fog_processor(self, fog_processor):
        self.fog_processor = fog_processor

    def classify_and_queue(self, mqtt_message: dict) -> dict:
        """Classify message by failure probability and enqueue into the appropriate slice queue."""
        classified = self.classifier.classify(mqtt_message)
        slice_id = classified["slice_id"]
        
        if slice_id == SLICE_CRITICAL:
            self.critical_queue.enqueue(classified)
        elif slice_id == SLICE_MONITORING:
            self.monitoring_queue.enqueue(classified)
        else:
            self.analytics_queue.enqueue(classified)
            
        return classified

    def process_queues(self) -> list:
        """
        Process messages in strict priority order:
        1. All CRITICAL messages (High priority, immediate processing)
        2. All MONITORING messages (Medium priority)
        3. All ANALYTICS messages (Low priority)
        """
        processed_messages = []
        
        # Priority 1: CRITICAL
        critical_items = self.critical_queue.dequeue_all()
        for item in critical_items:
            res = self._process_item(item, SLICE_CRITICAL)
            if res:
                processed_messages.append(res)
                
        # Priority 2: MONITORING
        monitoring_items = self.monitoring_queue.dequeue_all()
        for item in monitoring_items:
            res = self._process_item(item, SLICE_MONITORING)
            if res:
                processed_messages.append(res)
                
        # Priority 3: ANALYTICS
        analytics_items = self.analytics_queue.dequeue_all()
        for item in analytics_items:
            res = self._process_item(item, SLICE_ANALYTICS)
            if res:
                processed_messages.append(res)
                
        return processed_messages

    def _process_item(self, message: dict, slice_id: str) -> dict:
        """Pass message to Fog Processor and compute end-to-end slice latency."""
        if not self.fog_processor:
            return message
            
        # Send to Fog Node processor
        fog_result = self.fog_processor.process(message)
        message["fog_result"] = fog_result
        
        # Calculate total latency
        mqtt_lat = message.get("mqtt_latency_ms", 12.0)
        queue_wait = message.get("queue_wait_time_ms", 2.0)
        proc_time = fog_result.get("processing_time_ms", 15.0)
        total_lat = round(mqtt_lat + queue_wait + proc_time, 2)
        
        message["total_latency_ms"] = total_lat
        self.metrics_tracker.record_slice_processed(slice_id, total_lat)
        return message

    def get_all_slice_metrics(self) -> list:
        """Return array of status and metrics for all 3 slices."""
        res = []
        for slice_id in [SLICE_CRITICAL, SLICE_MONITORING, SLICE_ANALYTICS]:
            q_metrics = self.queues[slice_id].get_metrics()
            t_metrics = self.metrics_tracker.slice_stats[slice_id]
            res.append({
                "slice_id": slice_id,
                "priority": q_metrics["priority"],
                "priority_level": q_metrics["priority_level"],
                "messages": t_metrics["messages"],
                "queue_length": q_metrics["current_queue_length"],
                "avg_latency_ms": t_metrics["avg_latency_ms"],
                "max_queue_length": q_metrics["max_queue_length"],
                "status": "ACTIVE"
            })
        return res

    def get_slice_metrics(self, slice_id: str) -> dict:
        slice_id = slice_id.upper()
        if slice_id in self.queues:
            q_metrics = self.queues[slice_id].get_metrics()
            t_metrics = self.metrics_tracker.slice_stats[slice_id]
            return {
                "slice_id": slice_id,
                "priority": q_metrics["priority"],
                "messages": t_metrics["messages"],
                "queue_length": q_metrics["current_queue_length"],
                "avg_latency_ms": t_metrics["avg_latency_ms"],
                "max_queue_length": q_metrics["max_queue_length"],
                "total_wait_time_ms": q_metrics["total_wait_time"]
            }
        return {}

    def get_latency_breakdown(self) -> dict:
        """Get average breakdown of latency components."""
        # Calculate from slice queues and fog processor
        crit_metrics = self.queues[SLICE_CRITICAL].get_metrics()
        fog_time = 45.0
        if self.fog_processor:
            fog_time = self.fog_processor.get_metrics().get("avg_processing_time_ms", 45.0)
            
        mqtt_lat = 12.0
        slice_lat = crit_metrics.get("avg_wait_time_ms", 8.0)
        total_lat = round(mqtt_lat + slice_lat + fog_time, 2)
        
        return {
            "mqtt_latency_ms": mqtt_lat,
            "slice_latency_ms": max(2.0, slice_lat),
            "fog_processing_ms": fog_time,
            "total_latency_ms": total_lat
        }

slice_manager = NetworkSliceManager()
