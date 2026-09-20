"""
Fog Node Coordinator.
Integrates MQTT Subscriber, Slice Manager, Fog Processor, and Cloud Forwarding.
"""

import time
import threading
from backend.middleware.mqtt_subscriber import MQTTSubscriber
from backend.network_slicing.slice_manager import slice_manager
from backend.fog.fog_processor import fog_processor
from backend.fog.fog_metrics import fog_metrics

class FogNode:
    def __init__(self):
        self.fog_processor = fog_processor
        self.slice_manager = slice_manager
        self.slice_manager.set_fog_processor(self.fog_processor)
        
        self.mqtt_subscriber = MQTTSubscriber(on_message_callback=self._on_mqtt_message)
        self.metrics = fog_metrics
        
        self.running = False
        self.worker_thread = None
        self.cloud_forwarder = None  # Injected or connected to cloud processor
        self.recent_results = []
        self.lock = threading.Lock()

    def set_cloud_forwarder(self, forwarder):
        self.cloud_forwarder = forwarder

    def _on_mqtt_message(self, message: dict):
        """Callback from MQTT subscriber when sensor telemetry arrives."""
        # 1. Forward to Slice Manager for classification and priority queuing
        self.slice_manager.classify_and_queue(message)

    def start(self):
        """Start Fog Node processing loop and MQTT subscriber."""
        if self.running:
            return
            
        self.running = True
        self.mqtt_subscriber.start()
        
        self.worker_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.worker_thread.start()
        print("[FogNode] Fog Node started and listening for telemetry.")

    def stop(self):
        self.running = False
        self.mqtt_subscriber.stop()
        print("[FogNode] Fog Node stopped.")

    def _processing_loop(self):
        """Continuous prioritized queue processing loop."""
        while self.running:
            try:
                # Process priority queues: CRITICAL -> MONITORING -> ANALYTICS
                processed_items = self.slice_manager.process_queues()
                
                for item in processed_items:
                    fog_res = item.get("fog_result", {})
                    
                    with self.lock:
                        self.recent_results.append({
                            "timestamp": time.time(),
                            "machine_id": item.get("payload", {}).get("machine_id", "M-001"),
                            "slice_id": item.get("slice_id", "ANALYTICS"),
                            "priority": item.get("priority_name", "LOW"),
                            "failure_probability": item.get("failure_probability", 0.1),
                            "health_status": fog_res.get("health_status", "HEALTHY"),
                            "total_latency_ms": item.get("total_latency_ms", 45.0),
                            "alert": fog_res.get("alert"),
                            "recommendation": fog_res.get("recommendation")
                        })
                        if len(self.recent_results) > 100:
                            self.recent_results.pop(0)

                    # Forward to cloud if designated
                    if self.cloud_forwarder and fog_res.get("send_to_cloud", False):
                        self.cloud_forwarder.forward_critical(item)
                    elif self.cloud_forwarder:
                        self.cloud_forwarder.aggregate(item)
                        
                # Small sleep to yield CPU
                time.sleep(0.02)
            except Exception as e:
                print(f"[FogNode] Error in processing loop: {e}")
                time.sleep(0.1)

    def get_status(self) -> dict:
        return self.metrics.get_metrics()

    def get_recent_results(self, limit: int = 20) -> list:
        with self.lock:
            return list(reversed(self.recent_results[-limit:]))

fog_node = FogNode()
