"""
Cloud Storage.
SQLite database storage for telemetry, historical records, and alerts.
"""

import sqlite3
import os
import json
import time
import threading

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "cloud_data.db")

class CloudStorage:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Telemetry table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT,
                    timestamp REAL,
                    slice_id TEXT,
                    temperature REAL,
                    vibration REAL,
                    current REAL,
                    rpm REAL,
                    pressure REAL,
                    coolant_level REAL,
                    failure_probability REAL,
                    health_status TEXT,
                    is_critical INTEGER
                )
            """)
            
            # Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT,
                    timestamp REAL,
                    severity TEXT,
                    title TEXT,
                    message TEXT,
                    failure_probability REAL,
                    recommendation TEXT
                )
            """)
            
            conn.commit()
            conn.close()

    def store_telemetry(self, item: dict):
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                payload = item.get("payload", {})
                fog_res = item.get("fog_result", {})
                
                cursor.execute("""
                    INSERT INTO telemetry (
                        machine_id, timestamp, slice_id, temperature, vibration,
                        current, rpm, pressure, coolant_level, failure_probability,
                        health_status, is_critical
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payload.get("machine_id", "M-001"),
                    item.get("received_at", time.time()),
                    item.get("slice_id", "ANALYTICS"),
                    float(payload.get("temperature", 45.0)),
                    float(payload.get("vibration", 2.5)),
                    float(payload.get("current", 8.5)),
                    float(payload.get("rpm", 2200.0)),
                    float(payload.get("pressure", 100.0)),
                    float(payload.get("coolant_level", 85.0)),
                    float(item.get("failure_probability", 0.1)),
                    fog_res.get("health_status", "HEALTHY"),
                    1 if item.get("slice_id") == "CRITICAL" else 0
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[CloudStorage] Error storing telemetry: {e}")

    def store_alert(self, alert: dict, machine_id: str, recommendation: str = ""):
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alerts (
                        machine_id, timestamp, severity, title, message, failure_probability, recommendation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    machine_id,
                    alert.get("generated_at", time.time()),
                    alert.get("severity", "WARNING"),
                    alert.get("title", ""),
                    alert.get("message", ""),
                    float(alert.get("failure_probability", 0.5)),
                    recommendation
                ))
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[CloudStorage] Error storing alert: {e}")

    def get_recent_alerts(self, limit: int = 20) -> list:
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
                rows = [dict(r) for r in cursor.fetchall()]
                conn.close()
                return rows
            except Exception:
                return []

cloud_storage = CloudStorage()
