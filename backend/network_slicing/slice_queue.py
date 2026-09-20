"""
Network Slice Priority Queue.
Thread-safe priority queue implementation with precise wait-time and latency tracking.
"""

from queue import PriorityQueue
import time
import threading

class SliceQueue:
    def __init__(self, slice_id: str, priority_level: int):
        self.slice_id = slice_id
        self.priority_level = priority_level
        self.queue = PriorityQueue()
        self.lock = threading.Lock()
        
        self.metrics = {
            "enqueued": 0,
            "dequeued": 0,
            "total_wait_time": 0.0,
            "max_queue_length": 0,
            "avg_latency_ms": 0.0
        }
    
    def enqueue(self, message: dict):
        """Add message to queue with timestamp and priority."""
        with self.lock:
            enqueue_time = time.time()
            # Items stored as tuple: (priority, enqueue_time, item_dict)
            self.queue.put((self.priority_level, enqueue_time, message))
            self.metrics["enqueued"] += 1
            
            cur_len = self.queue.qsize()
            if cur_len > self.metrics["max_queue_length"]:
                self.metrics["max_queue_length"] = cur_len

    def dequeue(self):
        """Dequeue a single message and calculate queue wait latency."""
        try:
            priority, enqueue_time, message = self.queue.get_nowait()
            dequeue_time = time.time()
            wait_time_ms = max(0.1, (dequeue_time - enqueue_time) * 1000.0)
            
            with self.lock:
                self.metrics["dequeued"] += 1
                self.metrics["total_wait_time"] += wait_time_ms
                self.metrics["avg_latency_ms"] = round(
                    self.metrics["total_wait_time"] / self.metrics["dequeued"], 2
                )
                
            message["queue_wait_time_ms"] = round(wait_time_ms, 2)
            message["dequeued_at"] = dequeue_time
            return message
        except Exception:
            return None

    def dequeue_all(self) -> list:
        """Process all currently queued messages and record latency metrics."""
        items = []
        while not self.queue.empty():
            msg = self.dequeue()
            if msg:
                items.append(msg)
        return items

    def qsize(self) -> int:
        return self.queue.qsize()

    def get_metrics(self) -> dict:
        with self.lock:
            cur_len = self.queue.qsize()
            return {
                "slice_id": self.slice_id,
                "priority": "HIGH" if self.priority_level == 1 else ("MEDIUM" if self.priority_level == 2 else "LOW"),
                "priority_level": self.priority_level,
                "enqueued": self.metrics["enqueued"],
                "dequeued": self.metrics["dequeued"],
                "current_queue_length": cur_len,
                "queue_length": cur_len,
                "max_queue_length": self.metrics["max_queue_length"],
                "avg_wait_time_ms": self.metrics["avg_latency_ms"],
                "avg_latency_ms": self.metrics["avg_latency_ms"],
                "total_wait_time": round(self.metrics["total_wait_time"], 2)
            }
