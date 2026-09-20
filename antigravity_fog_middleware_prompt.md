# ANTIGRAVITY PROMPT: IoT Predictive Maintenance + Fog Computing + MQTT + Network Slicing

## PROJECT OVERVIEW

**Extend the existing IoT Predictive Maintenance System** by adding:
1. **Fog Computing Layer** (intermediate processing between IoT and Cloud)
2. **MQTT Middleware** (communication between IoT devices and Fog)
3. **Network Slicing Simulation** (3 virtual slices with priority queues)
4. **Real-time monitoring dashboard** for Fog, MQTT, and Network metrics

**CRITICAL:** Do NOT remove or replace any existing functionality. This is an extension, not a rebuild.

---

## PRESERVE ALL EXISTING FEATURES

Keep the complete existing system:
- ✅ IoT sensor simulation engine
- ✅ Synthetic dataset generation (10,000+ samples)
- ✅ ML pipeline (Random Forest, Gradient Boosting, XGBoost)
- ✅ Failure prediction and classification
- ✅ Maintenance recommendations engine
- ✅ REST APIs and WebSocket connections
- ✅ React dashboard and all UI components
- ✅ Database (PostgreSQL/SQLite)
- ✅ Historical sensor data storage
- ✅ Alert system
- ✅ Docker configuration

---

## ARCHITECTURE: THREE-LAYER MODEL

```
SIMULATED IoT DEVICES (Layer 1)
         ↓ (MQTT Publish)
MQTT MIDDLEWARE BROKER (Communication)
         ↓ (Subscribe)
NETWORK SLICE MANAGER (Traffic Classification)
         ↓ (3 Priority Queues)
FOG NODE PROCESSING (Layer 2)
         ↓ (Aggregated/Non-Critical Data)
CLOUD BACKEND (Layer 3)
         ↓
DATABASE & HISTORICAL STORAGE
```

---

# PART 1: FOG COMPUTING LAYER

## 1.1 IoT Layer (Existing Simulation)

The existing sensor simulation engine continues to generate:
- Temperature (°C): 20-100°C with trend patterns
- Vibration (m/s²): 0-10 with anomaly spikes
- Current (A): 5-15A normal, 20-25A during stress
- Rotational Speed (RPM): 1000-3000 with degradation
- Pressure (PSI): 50-200 with variance
- Operating Hours: cumulative counter
- Coolant Level: percentage

**Change:** Instead of directly calling APIs, IoT simulators publish to MQTT broker.

## 1.2 Fog Node Implementation

Create a Python-based Fog Node (`fog/fog_node.py`) with these responsibilities:

### Fog Node Functions:
1. **Receive** sensor data from MQTT topics
2. **Preprocess** sensor data locally
   - Validate data ranges
   - Remove outliers
   - Normalize values
3. **Detect** local anomalies (before ML)
   - Statistical anomaly detection
   - Threshold-based alerts
4. **Run ML Prediction Locally**
   - Load existing trained ML model
   - Calculate failure probability
   - Classify machine state (HEALTHY/WARNING/CRITICAL)
5. **Generate Critical Alerts** immediately
   - No need to wait for cloud response
   - Failure probability > 70% triggers immediate alert
6. **Aggregate Non-Critical Data**
   - Combine normal readings
   - Reduce payload size
   - Send summary to cloud
7. **Forward Data to Cloud**
   - Send critical events immediately
   - Send aggregated data at intervals (e.g., every 5 minutes)

### Fog Node Metrics to Capture:
```python
fog_metrics = {
    "messages_processed": int,
    "avg_processing_time_ms": float,
    "critical_messages": int,
    "monitoring_messages": int,
    "analytics_messages": int,
    "processing_rate_msg_per_sec": float,
    "uptime_seconds": int,
    "last_heartbeat": timestamp,
    "status": "ONLINE/OFFLINE"
}
```

---

# PART 2: MQTT MIDDLEWARE

## 2.1 MQTT Broker Setup

Use **Mosquitto MQTT Broker** (lightweight, open-source).

Include in `docker-compose.yml`:
```yaml
mqtt_broker:
  image: eclipse-mosquitto:latest
  ports:
    - "1883:1883"
    - "9001:9001"
  volumes:
    - ./mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf
```

Configuration:
- Listener port: 1883 (MQTT), 9001 (WebSocket)
- Allow anonymous connections (for simulation)
- Enable QoS levels 0, 1, 2

## 2.2 MQTT Publisher (IoT Simulators)

Modify existing sensor simulator to publish via MQTT (`middleware/mqtt_publisher.py`):

```python
class MQTTPublisher:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(client_id=f"IoT_Machine_{uuid()}")
        self.client.connect(broker_host, broker_port, keepalive=60)
        self.client.loop_start()
    
    def publish_sensor_data(self, machine_id, sensor_payload):
        """
        Publishes sensor data to MQTT broker
        Topic: machine/{machine_id}/sensors
        QoS: 1 (At least once delivery)
        """
        topic = f"machine/{machine_id}/sensors"
        self.client.publish(topic, json.dumps(sensor_payload), qos=1)
        # Log: timestamp, machine_id, topic, payload
```

### MQTT Topics

Create hierarchical topics:
```
machine/{machine_id}/temperature
machine/{machine_id}/vibration
machine/{machine_id}/current
machine/{machine_id}/rpm
machine/{machine_id}/pressure
machine/{machine_id}/coolant
machine/{machine_id}/sensors  (combined payload)
```

### MQTT Payload Format

```json
{
  "machine_id": "M-001",
  "timestamp": "2026-09-20T10:30:00.123Z",
  "temperature": 82.5,
  "vibration": 6.4,
  "current": 8.7,
  "rpm": 1380,
  "pressure": 145,
  "coolant_level": 62,
  "operating_hours": 2840
}
```

## 2.3 MQTT Subscriber (Fog Node)

Create MQTT subscriber for Fog Node (`middleware/mqtt_subscriber.py`):

```python
class MQTTSubscriber:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(client_id=f"Fog_Node_{uuid()}")
        self.client.on_message = self.on_message
        self.client.connect(broker_host, broker_port, keepalive=60)
        self.client.subscribe("machine/+/sensors", qos=1)
        self.client.loop_start()
        self.message_buffer = []
    
    def on_message(self, client, userdata, msg):
        """
        Callback when message received from MQTT broker
        Pass to Slice Manager for classification
        """
        payload = json.loads(msg.payload.decode())
        timestamp = time.time()
        
        message = {
            "mqtt_topic": msg.topic,
            "mqtt_qos": msg.qos,
            "payload": payload,
            "received_at": timestamp,
            "mqtt_latency": calculate_latency(payload["timestamp"], timestamp)
        }
        
        self.message_buffer.append(message)
        # Forward to Slice Manager
        slice_manager.classify_and_queue(message)
```

## 2.4 MQTT Middleware Metrics

Track and expose:
```python
mqtt_metrics = {
    "broker_status": "CONNECTED/DISCONNECTED",
    "published_messages_total": int,
    "received_messages_total": int,
    "active_topics": int,
    "messages_per_second": float,
    "avg_mqtt_latency_ms": float,
    "connection_uptime": int,
    "qos_distribution": {
        "qos_0": int,
        "qos_1": int,
        "qos_2": int
    }
}
```

---

# PART 3: NETWORK SLICING SIMULATION

## 3.1 Network Slices Definition

### Slice 1: CRITICAL (Priority = HIGH)

**Trigger Condition:**
- Failure Probability > 70%
- Temperature anomaly (>95°C or <10°C)
- Severe vibration (>8 m/s²)
- Current spike (>20A)
- Imminent equipment failure detected

**Behavior:**
- Highest priority processing
- Minimum queue wait time
- Immediate Fog processing
- Instant alert generation
- No batching/aggregation

**Example:**
```json
{
  "slice_id": "CRITICAL",
  "priority": "HIGH",
  "assigned_messages": 142,
  "queue_length": 3,
  "avg_latency_ms": 45,
  "message": {
    "machine_id": "M-001",
    "temperature": 98,
    "failure_probability": 0.92,
    "alert": "CRITICAL: Machine M-001 will fail in next 30 minutes"
  }
}
```

### Slice 2: MONITORING (Priority = MEDIUM)

**Trigger Condition:**
- Failure Probability between 40-70%
- Normal operational monitoring
- Regular sensor readings
- Preventive alerts
- Warning-level anomalies

**Behavior:**
- Medium priority
- Moderate queue wait acceptable
- Fog processing after critical
- Alerts generated with warning severity
- Minor data aggregation allowed

**Example:**
```json
{
  "slice_id": "MONITORING",
  "priority": "MEDIUM",
  "assigned_messages": 856,
  "queue_length": 12,
  "avg_latency_ms": 120,
  "message": {
    "machine_id": "M-002",
    "temperature": 78,
    "failure_probability": 0.55,
    "status": "WARNING: Monitor this machine closely"
  }
}
```

### Slice 3: ANALYTICS (Priority = LOW)

**Trigger Condition:**
- Failure Probability < 40%
- Healthy machine operation
- Historical data
- Bulk analytics
- Model training data
- Reports and statistics

**Behavior:**
- Lowest priority
- Highest queue wait acceptable
- Processed after critical and monitoring
- Sent to cloud for long-term storage
- Heavy batching and aggregation

**Example:**
```json
{
  "slice_id": "ANALYTICS",
  "priority": "LOW",
  "assigned_messages": 3240,
  "queue_length": 145,
  "avg_latency_ms": 850,
  "message": {
    "machine_id": "M-003",
    "temperature": 45,
    "failure_probability": 0.18,
    "status": "HEALTHY: Normal operation"
  }
}
```

---

## 3.2 Network Slice Manager

Create `network_slicing/slice_manager.py`:

```python
class NetworkSliceManager:
    def __init__(self):
        self.critical_queue = PriorityQueue()      # High priority
        self.monitoring_queue = PriorityQueue()    # Medium priority
        self.analytics_queue = PriorityQueue()     # Low priority
        
        self.slice_metrics = {
            "CRITICAL": {"messages": 0, "total_latency": 0, "queue_len": 0},
            "MONITORING": {"messages": 0, "total_latency": 0, "queue_len": 0},
            "ANALYTICS": {"messages": 0, "total_latency": 0, "queue_len": 0}
        }
    
    def classify_message(self, mqtt_message):
        """
        Analyze message and assign to appropriate slice
        based on failure probability and sensor anomalies
        """
        payload = mqtt_message["payload"]
        failure_prob = self.predict_failure(payload)
        
        if failure_prob > 0.70:
            slice_id = "CRITICAL"
            priority = 1
        elif failure_prob > 0.40:
            slice_id = "MONITORING"
            priority = 2
        else:
            slice_id = "ANALYTICS"
            priority = 3
        
        message_with_slice = {
            **mqtt_message,
            "slice_id": slice_id,
            "priority": priority,
            "failure_probability": failure_prob,
            "classified_at": time.time()
        }
        
        return message_with_slice
    
    def queue_message(self, classified_message):
        """
        Place message in appropriate priority queue
        """
        slice_id = classified_message["slice_id"]
        priority = classified_message["priority"]
        
        if slice_id == "CRITICAL":
            self.critical_queue.put((priority, time.time(), classified_message))
        elif slice_id == "MONITORING":
            self.monitoring_queue.put((priority, time.time(), classified_message))
        else:
            self.analytics_queue.put((priority, time.time(), classified_message))
        
        self.slice_metrics[slice_id]["messages"] += 1
        self.slice_metrics[slice_id]["queue_len"] = self._get_queue_length(slice_id)
    
    def process_queues(self):
        """
        Process messages in priority order:
        1. All CRITICAL messages
        2. All MONITORING messages
        3. All ANALYTICS messages
        """
        critical_processed = self._process_queue(self.critical_queue, "CRITICAL")
        monitoring_processed = self._process_queue(self.monitoring_queue, "MONITORING")
        analytics_processed = self._process_queue(self.analytics_queue, "ANALYTICS")
        
        return {
            "critical": critical_processed,
            "monitoring": monitoring_processed,
            "analytics": analytics_processed
        }
    
    def _process_queue(self, queue, slice_id):
        """
        Process all messages in a queue
        Record latency metrics
        """
        processed = []
        while not queue.empty():
            priority, enqueue_time, message = queue.get()
            processing_time = time.time()
            latency = (processing_time - enqueue_time) * 1000  # ms
            
            message["processed_at"] = processing_time
            message["queue_latency_ms"] = latency
            
            # Send to Fog processor
            fog_result = self.fog_processor.process(message)
            message["fog_result"] = fog_result
            
            self.slice_metrics[slice_id]["total_latency"] += latency
            processed.append(message)
        
        return processed
```

---

# PART 4: FOG NODE PROCESSING

Create `fog/fog_processor.py`:

```python
class FogProcessor:
    def __init__(self, ml_model_path):
        self.ml_model = load_model(ml_model_path)
        self.scaler = load_scaler()
        self.metrics = {
            "processed": 0,
            "avg_processing_time": 0,
            "alerts_generated": 0
        }
    
    def process(self, classified_message):
        """
        Fog-level processing:
        1. Validate sensor data
        2. Feature engineering
        3. ML prediction
        4. Generate alerts
        5. Decide: Cloud or Local
        """
        start_time = time.time()
        
        # Step 1: Data Validation
        if not self.validate_sensor_data(classified_message):
            return {"status": "INVALID", "reason": "Sensor data out of range"}
        
        # Step 2: Feature Engineering
        features = self.extract_features(classified_message["payload"])
        features_scaled = self.scaler.transform([features])
        
        # Step 3: ML Prediction
        failure_probability = self.ml_model.predict_proba(features_scaled)[0][1]
        health_status = self.classify_health(failure_probability)
        
        # Step 4: Alert Generation
        alert = None
        if failure_probability > 0.70:
            alert = {
                "severity": "CRITICAL",
                "message": f"Machine {classified_message['payload']['machine_id']} failure predicted",
                "generated_at": time.time(),
                "failure_probability": failure_probability
            }
            self.metrics["alerts_generated"] += 1
        elif failure_probability > 0.40:
            alert = {
                "severity": "WARNING",
                "message": f"Monitor machine {classified_message['payload']['machine_id']}",
                "generated_at": time.time(),
                "failure_probability": failure_probability
            }
        
        # Step 5: Generate Maintenance Recommendation
        recommendation = self.generate_recommendation(features, failure_probability)
        
        processing_time = (time.time() - start_time) * 1000  # ms
        self.metrics["processed"] += 1
        self.metrics["avg_processing_time"] = \
            (self.metrics["avg_processing_time"] + processing_time) / 2
        
        result = {
            "machine_id": classified_message["payload"]["machine_id"],
            "failure_probability": failure_probability,
            "health_status": health_status,
            "alert": alert,
            "recommendation": recommendation,
            "processed_at": time.time(),
            "processing_time_ms": processing_time,
            "fog_processed": True  # Mark as locally processed
        }
        
        # Step 6: Decide destination
        if classified_message["slice_id"] == "CRITICAL":
            result["send_to_cloud"] = True  # Always sync critical
        else:
            result["send_to_cloud"] = False  # Aggregate non-critical
        
        return result
```

---

# PART 5: PRIORITY QUEUE SIMULATION

Create `network_slicing/slice_queue.py`:

```python
from queue import PriorityQueue
import time

class SliceQueue:
    def __init__(self, slice_id, priority_level):
        self.slice_id = slice_id
        self.priority_level = priority_level
        self.queue = PriorityQueue()
        self.metrics = {
            "enqueued": 0,
            "dequeued": 0,
            "total_wait_time": 0,
            "max_queue_length": 0,
            "avg_latency_ms": 0
        }
    
    def enqueue(self, message):
        """Add message to queue with timestamp"""
        enqueue_time = time.time()
        self.queue.put({
            "message": message,
            "enqueue_time": enqueue_time,
            "priority": self.priority_level
        })
        self.metrics["enqueued"] += 1
        current_length = self.queue.qsize()
        if current_length > self.metrics["max_queue_length"]:
            self.metrics["max_queue_length"] = current_length
    
    def dequeue_all(self):
        """Process all messages in queue, track latency"""
        processed = []
        while not self.queue.empty():
            item = self.queue.get()
            dequeue_time = time.time()
            wait_time = (dequeue_time - item["enqueue_time"]) * 1000  # ms
            
            item["message"]["queue_wait_time_ms"] = wait_time
            item["message"]["dequeue_time"] = dequeue_time
            
            self.metrics["dequeued"] += 1
            self.metrics["total_wait_time"] += wait_time
            processed.append(item["message"])
        
        if self.metrics["dequeued"] > 0:
            self.metrics["avg_latency_ms"] = \
                self.metrics["total_wait_time"] / self.metrics["dequeued"]
        
        return processed
    
    def get_metrics(self):
        """Return slice queue metrics"""
        return {
            "slice_id": self.slice_id,
            "priority": self.priority_level,
            "enqueued": self.metrics["enqueued"],
            "dequeued": self.metrics["dequeued"],
            "current_queue_length": self.queue.qsize(),
            "max_queue_length": self.metrics["max_queue_length"],
            "avg_wait_time_ms": self.metrics["avg_latency_ms"],
            "total_wait_time": self.metrics["total_wait_time"]
        }
```

---

# PART 6: FOG VS CLOUD COMPARISON

Create `cloud/cloud_processor.py` and implement experimental modes:

### Mode A: Cloud-Only Processing
```
IoT → MQTT → Cloud → ML Prediction → Alert
```

### Mode B: Fog Processing (Default)
```
IoT → MQTT → Network Slice → Fog → ML Prediction → Alert
```

Create API endpoints to simulate both modes:

```python
class ProcessingModeComparator:
    def __init__(self):
        self.fog_metrics = {
            "messages_processed": 0,
            "total_latency": 0,
            "critical_alerts": 0,
            "avg_processing_time_ms": 0,
            "cloud_messages_sent": 0,
            "local_messages_processed": 0
        }
        
        self.cloud_metrics = {
            "messages_received": 0,
            "total_latency": 0,
            "processing_time_ms": 0,
            "storage_messages": 0
        }
    
    def compare_latency(self):
        """
        Compare response times:
        - Fog processing (includes MQTT + Slice + Processing)
        - Cloud processing (MQTT + Network + Cloud Processing)
        """
        return {
            "fog_avg_latency_ms": self.fog_metrics["avg_processing_time_ms"],
            "cloud_avg_latency_ms": self.cloud_metrics["processing_time_ms"],
            "latency_reduction_percent": \
                ((self.cloud_metrics["processing_time_ms"] - 
                  self.fog_metrics["avg_processing_time_ms"]) / 
                 self.cloud_metrics["processing_time_ms"]) * 100
        }
    
    def compare_traffic(self):
        """
        Compare bandwidth usage:
        - Fog: Only aggregated + critical data sent to cloud
        - Cloud: All data sent to cloud
        """
        return {
            "fog_messages_sent_to_cloud": self.fog_metrics["cloud_messages_sent"],
            "cloud_total_messages": self.cloud_metrics["messages_received"],
            "traffic_reduction_percent": \
                ((self.cloud_metrics["messages_received"] - 
                  self.fog_metrics["cloud_messages_sent"]) / 
                 self.cloud_metrics["messages_received"]) * 100
        }
    
    def compare_critical_response_time(self):
        """
        Measure critical alert response time
        - Fog: Immediate (processed locally)
        - Cloud: Slower (network + processing)
        """
        return {
            "fog_critical_response_time_ms": self._measure_critical_latency_fog(),
            "cloud_critical_response_time_ms": self._measure_critical_latency_cloud(),
            "improvement_percent": 0  # Calculate based on measurements
        }
```

---

# PART 7: DASHBOARD EXTENSIONS

## 7.1 New Dashboard Section: "Fog & Network"

Add React component `FogNetworkDashboard.jsx`:

### Subsection 1: Fog Node Status

Display live metrics:
```
┌─────────────────────────────────┐
│ FOG NODE STATUS                 │
├─────────────────────────────────┤
│ Status: 🟢 ONLINE               │
│ Messages Processed: 5,842       │
│ Processing Rate: 23 msg/sec     │
│ Avg Processing Time: 48 ms      │
│ Critical Messages: 187          │
│ Monitoring Messages: 1,203      │
│ Analytics Messages: 4,452       │
│ Uptime: 2h 35m                  │
│ Last Heartbeat: 2 sec ago       │
└─────────────────────────────────┘
```

### Subsection 2: MQTT Middleware Status

```
┌─────────────────────────────────┐
│ MQTT MIDDLEWARE                 │
├─────────────────────────────────┤
│ Broker Status: 🟢 CONNECTED     │
│ Published Messages: 8,234       │
│ Received Messages: 8,234        │
│ Active Topics: 12               │
│ Message Rate: 28 msg/sec        │
│ Avg Latency: 12 ms              │
│ Connection: STABLE              │
│ QoS-0: 0 | QoS-1: 8234 | QoS-2: 0 │
└─────────────────────────────────┘
```

### Subsection 3: Network Slice Status

Display 3 slices side-by-side:

```
┌──────────────────┬──────────────────┬──────────────────┐
│ CRITICAL SLICE   │ MONITORING SLICE │ ANALYTICS SLICE  │
│ Priority: HIGH   │ Priority: MEDIUM │ Priority: LOW    │
├──────────────────┼──────────────────┼──────────────────┤
│ Messages: 187    │ Messages: 1,203  │ Messages: 4,452  │
│ Queue Length: 2  │ Queue Length: 8  │ Queue Length: 45 │
│ Avg Latency: 45ms│ Avg Latency:120ms│ Avg Latency:850ms│
│ Status: ACTIVE   │ Status: ACTIVE   │ Status: ACTIVE   │
└──────────────────┴──────────────────┴──────────────────┘
```

### Subsection 4: Fog vs Cloud Comparison

```
┌───────────────────────────────────────────────┐
│ FOG vs CLOUD PROCESSING COMPARISON            │
├──────────────────────┬────────────────────────┤
│ Fog Avg Latency      │ 48 ms      🟢 FASTER   │
│ Cloud Avg Latency    │ 320 ms                 │
│ Latency Reduction    │ 85%                    │
├──────────────────────┼────────────────────────┤
│ Cloud Traffic Sent   │ 312 / 8,234 (3.8%)     │
│ Local Processing     │ 7,922 / 8,234 (96.2%)  │
├──────────────────────┼────────────────────────┤
│ Critical Alert Time  │ 45 ms (Fog)            │
│ (Cloud Method)       │ 320 ms (Cloud)         │
│ Improvement          │ 85% faster             │
└──────────────────────┴────────────────────────┘
```

---

## 7.2 Network Visualization Component

Add animated network architecture diagram showing data flow:

```
       Simulated IoT Devices
              │ (Publish)
              ↓
       ┌─────────────────┐
       │ MQTT MIDDLEWARE │
       │ 28 msg/sec      │
       └────────┬────────┘
                │ (Subscribe)
                ↓
       ┌─────────────────────────────┐
       │   SLICE MANAGER             │
       │ Classify & Route Traffic    │
       └────┬────────┬───────────────┘
            │        │
      ┌─────▼──┐  ┌──▼──────┐  ┌────────┐
      │ CRIT   │  │ MON     │  │ ANALYT │
      │ HIGH   │  │ MEDIUM  │  │ LOW    │
      │ 187msg │  │ 1.2kmsg │  │ 4.4kmsg
      └─────┬──┘  └──┬──────┘  └───┬────┘
            │        │             │
            └────────┼─────────────┘
                     ↓
           ┌─────────────────────┐
           │    FOG NODE         │
           │ ML Prediction       │
           │ Alert Generation    │
           │ 5,842 processed     │
           └──────────┬──────────┘
                      ↓
           ┌─────────────────────┐
           │  CLOUD BACKEND      │
           │ Historical Storage  │
           │ 312 msgs → Cloud    │
           └─────────────────────┘
```

The diagram should animate/update in real-time showing message counters and data flow.

---

## 7.3 Network Performance Charts

Add chart components showing:

**Chart 1: Messages by Network Slice (Real-time)**
- Line chart showing cumulative messages over time
- 3 lines: Critical, Monitoring, Analytics
- X-axis: Time, Y-axis: Cumulative messages

**Chart 2: Average Latency by Slice**
- Bar chart comparing:
  - MQTT latency
  - Queue wait time
  - Fog processing time
  - Total end-to-end latency

**Chart 3: Queue Length Over Time**
- Area chart showing queue depth for each slice
- Visualization of how queue length changes with load

**Chart 4: MQTT Message Rate**
- Line chart showing messages/second
- Updates every 5 seconds

**Chart 5: Fog Processing Time Distribution**
- Histogram or box plot
- Shows min/max/avg processing times

**Chart 6: Fog vs Cloud Latency Comparison**
- Side-by-side bar chart or line chart
- Shows latency reduction benefit

**Chart 7: Cloud Traffic Reduction**
- Pie chart showing:
  - Messages processed locally (%) 
  - Messages sent to cloud (%)

---

# PART 8: DEMONSTRATION SCENARIO

Create a built-in scenario that showcases the entire system. Implement `simulation/demo_scenario.py`:

## Stage 1: Normal Operation (0-60 seconds)

```
Machine M-001 Normal State
├─ Temperature: 45°C (Normal)
├─ Vibration: 2.1 m/s² (Normal)
├─ Current: 8.5A (Normal)
├─ Failure Risk: 12%
└─ Slice Assignment: ANALYTICS (Priority: LOW)
   └─ Queue: Fast processing, sent to cloud for storage

MQTT Traffic: ~5 msg/sec
Fog Processing: Minimal
Network Slice: Analytics dominant
```

### Metrics Snapshot:
```
Critical Messages: 0
Monitoring Messages: 0
Analytics Messages: 287
Avg Latency: 850ms
```

---

## Stage 2: Warning State (60-120 seconds)

```
Machine M-001 Warning State
├─ Temperature: 72°C (Elevated)
├─ Vibration: 5.8 m/s² (Elevated)
├─ Current: 12.3A (Elevated)
├─ Failure Risk: 58%
└─ Slice Assignment: MONITORING (Priority: MEDIUM)
   └─ Queue: Medium priority processing, some cloud sync

Alert Generated:
⚠️  WARNING: Machine M-001 shows signs of degradation
    Recommendation: Schedule maintenance inspection

MQTT Traffic: ~6 msg/sec
Fog Processing: Active
Network Slice: Monitoring active
```

### Metrics Snapshot:
```
Critical Messages: 0
Monitoring Messages: 156
Analytics Messages: 542
Avg Latency: 120ms (faster due to medium priority)
```

---

## Stage 3: Critical State (120-180 seconds)

```
Machine M-001 Critical State
├─ Temperature: 96°C (CRITICAL)
├─ Vibration: 9.2 m/s² (CRITICAL)
├─ Current: 22.1A (CRITICAL)
├─ Failure Risk: 92%
└─ Slice Assignment: CRITICAL (Priority: HIGH)
   └─ Queue: Highest priority, immediate processing

🚨 CRITICAL ALERT Generated:
   Machine M-001 FAILURE IMMINENT
   Predicted Failure in: 8 minutes
   Immediate Actions Required:
   ✓ Stop machine operation
   ✓ Shut down equipment
   ✓ Inspect motor windings
   ✓ Check lubrication systems

MQTT Traffic: ~8 msg/sec
Fog Processing: Maximum priority
Network Slice: Critical slice activated
Response Time: 45ms (Fog local processing advantage)
```

### Metrics Snapshot:
```
Critical Messages: 43
Monitoring Messages: 156
Analytics Messages: 542
Avg Critical Latency: 45ms
Total Messages Processed: 741
```

---

## Dashboard Visualization During Demo

The dashboard should show real-time transitions:

```
Stage 1 (Normal)          Stage 2 (Warning)           Stage 3 (Critical)
Machine Health: GOOD  →   Machine Health: WARNING →   Machine Health: CRITICAL
Health Score: 88%     →   Health Score: 42%      →   Health Score: 8%
Color: 🟢 Green        →   Color: 🟡 Yellow       →   Color: 🔴 Red
Slice: Analytics      →   Slice: Monitoring      →   Slice: Critical
```

---

# PART 9: API ENDPOINTS

## New Fog Computing Endpoints

```
GET /api/fog/status
  Response: {
    "status": "ONLINE",
    "messages_processed": 5842,
    "processing_rate": 23,
    "critical_messages": 187,
    "monitoring_messages": 1203,
    "analytics_messages": 4452,
    "avg_processing_time_ms": 48,
    "uptime_seconds": 9300
  }

GET /api/fog/metrics
  Response: Detailed fog node metrics

GET /api/fog/health
  Response: {"status": "HEALTHY", "cpu_usage": "35%", ...}
```

## MQTT Middleware Endpoints

```
GET /api/middleware/status
  Response: {
    "broker_connected": true,
    "published_messages": 8234,
    "received_messages": 8234,
    "active_topics": 12,
    "messages_per_second": 28,
    "avg_latency_ms": 12
  }

GET /api/middleware/topics
  Response: [{
    "topic": "machine/M-001/sensors",
    "message_count": 687,
    "last_message_time": "2026-09-20T10:35:12Z"
  }, ...]

GET /api/middleware/qos-stats
  Response: {"qos_0": 0, "qos_1": 8234, "qos_2": 0}
```

## Network Slicing Endpoints

```
GET /api/network/slices
  Response: [{
    "slice_id": "CRITICAL",
    "priority": "HIGH",
    "messages": 187,
    "queue_length": 2,
    "avg_latency_ms": 45
  }, ...]

GET /api/network/slices/{slice_id}/metrics
  Response: Detailed metrics for specific slice

GET /api/network/traffic
  Response: {
    "critical_traffic": 187,
    "monitoring_traffic": 1203,
    "analytics_traffic": 4452,
    "total_traffic": 5842
  }

GET /api/network/latency
  Response: {
    "mqtt_latency_ms": 12,
    "slice_latency_ms": 8,
    "fog_processing_ms": 48,
    "total_latency_ms": 68
  }
```

## Fog vs Cloud Comparison

```
GET /api/analytics/fog-vs-cloud
  Response: {
    "fog_avg_latency_ms": 48,
    "cloud_avg_latency_ms": 320,
    "latency_reduction_percent": 85,
    "cloud_traffic_reduction_percent": 96.2,
    "critical_alert_time_fog_ms": 45,
    "critical_alert_time_cloud_ms": 320,
    "local_processing_percent": 96.2
  }

GET /api/analytics/network-slice-performance
  Response: Detailed performance metrics per slice

GET /api/analytics/mqtt-performance
  Response: MQTT throughput, latency, reliability metrics
```

## Real-time WebSocket Events

If WebSockets already exist, push real-time updates:

```
Event: fog:metrics
Payload: {
  "messages_processed": 5842,
  "processing_rate": 23,
  "avg_latency_ms": 48
}

Event: middleware:message
Payload: {
  "topic": "machine/M-001/sensors",
  "payload": {...},
  "latency_ms": 12
}

Event: slice:status
Payload: {
  "slice_id": "CRITICAL",
  "queue_length": 2,
  "avg_latency": 45
}

Event: network:traffic
Payload: {
  "critical": 187,
  "monitoring": 1203,
  "analytics": 4452
}
```

---

# PART 10: SOURCE CODE ORGANIZATION

Extend existing backend with new directories:

```
backend/
│
├── fog/
│   ├── fog_node.py                 # Main Fog Node class
│   ├── fog_processor.py            # Processing logic
│   ├── fog_metrics.py              # Metrics collection
│   └── anomaly_detector.py         # Local anomaly detection
│
├── middleware/
│   ├── mqtt_client.py              # MQTT client wrapper
│   ├── mqtt_publisher.py           # IoT device publisher
│   ├── mqtt_subscriber.py          # Fog node subscriber
│   ├── mqtt_config.py              # Configuration
│   └── mqtt_metrics.py             # Middleware metrics
│
├── network_slicing/
│   ├── slice_manager.py            # Main slice manager
│   ├── slice_queue.py              # Priority queue implementation
│   ├── traffic_classifier.py       # Message classification logic
│   ├── slice_metrics.py            # Metrics per slice
│   └── slice_config.py             # Configurable thresholds
│
├── cloud/
│   ├── cloud_processor.py          # Cloud-side processing
│   ├── cloud_storage.py            # Long-term storage
│   └── analytics_engine.py         # Historical analytics
│
├── simulation/
│   ├── iot_simulator.py            # Existing simulator (MODIFIED)
│   └── demo_scenario.py            # Demo scenario implementation
│
├── api/
│   ├── fog_routes.py               # Fog API endpoints
│   ├── middleware_routes.py        # Middleware API endpoints
│   ├── slicing_routes.py           # Network slicing API endpoints
│   └── analytics_routes.py         # Analytics endpoints
│
├── models/
│   └── [existing ML files unchanged]
│
├── database/
│   └── [existing database files unchanged]
│
├── app.py                          # Main Flask/FastAPI app (MODIFIED)
└── docker-compose.yml              # Docker Compose (MODIFIED for MQTT)
```

---

# PART 11: DOCKER CONFIGURATION

Modify existing `docker-compose.yml`:

```yaml
version: '3.8'

services:
  
  # Existing Database
  postgres:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: iot_user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: iot_maintenance
  
  # MQTT Broker (NEW)
  mqtt_broker:
    image: eclipse-mosquitto:latest
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - ./mosquitto/config/mosquitto.conf:/mosquitto/config/mosquitto.conf
      - mosquitto_data:/mosquitto/data
    command: mosquitto -c /mosquitto/config/mosquitto.conf
  
  # Backend (MODIFIED to include Fog, Middleware, Slicing)
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      MQTT_BROKER: mqtt_broker
      MQTT_PORT: 1883
      DATABASE_URL: postgresql://iot_user:password@postgres:5432/iot_maintenance
      FLASK_ENV: development
    depends_on:
      - postgres
      - mqtt_broker
    volumes:
      - ./backend:/app
  
  # Frontend (Existing)
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  mosquitto_data:
```

---

# PART 12: REQUIREMENTS AND CONSTRAINTS

## Must Be Implemented (Not Faked)

✅ **Actual MQTT Communication**
- Real MQTT broker running
- Real message publishing and subscribing
- Actual QoS levels
- Real latency measurements (not hard-coded)

✅ **Real Network Slicing**
- Messages actually classified by failure probability
- Messages actually queued in priority queues
- Critical messages actually processed first
- Queue metrics actually measured

✅ **Real Fog Processing**
- ML model actually loaded and running on Fog
- Predictions actually calculated locally
- Alerts actually generated from Fog results
- Processing time actually measured

✅ **Real Performance Metrics**
- All latency measurements from actual execution
- All throughput from actual message counts
- All queue statistics from actual queue operations
- No hard-coded or fabricated values

✅ **Real Demonstrations**
- Demo scenario shows actual system behavior transitions
- Dashboard metrics update from real data
- All visualizations based on actual calculations

---

## Do NOT Include

❌ Static architecture diagrams (make them dynamic/interactive)
❌ Hard-coded MQTT status values
❌ Fabricated latency numbers
❌ Fake network-slice statistics
❌ Non-functional demo scenario
❌ Disconnected visualizations
❌ Documentation that doesn't match implementation

---

# PART 13: DELIVERABLES

Upon completion, provide:

1. **Full Source Code**
   - All Python files (Fog, Middleware, Slicing, Cloud)
   - Modified React dashboard with new sections
   - API endpoints for new features
   - Docker Compose configuration

2. **Working System**
   - Deployable via single `docker-compose up` command
   - MQTT broker automatically running
   - Fog node automatically processing
   - Network slicing automatically routing
   - Dashboard automatically updating

3. **Documentation**
   - Architecture overview with diagrams
   - API documentation for new endpoints
   - Setup and running instructions
   - Performance measurement methodology
   - Demo scenario explanation

4. **Performance Reports**
   - ML model accuracy (existing)
   - Fog processing latency
   - MQTT middleware performance
   - Network slicing effectiveness
   - Fog vs Cloud comparison results
   - Dashboard performance metrics

5. **Test Results**
   - Unit tests for Fog processor
   - Integration tests for MQTT middleware
   - Performance benchmarks
   - Demo scenario execution log
   - System stability under load

---

# PART 14: ACCEPTANCE CRITERIA

✅ MQTT middleware deployed and functional
   - Mosquitto broker running
   - Sensors publishing to MQTT topics
   - Fog node subscribing to topics
   - Message throughput > 20 msg/sec

✅ Network slicing implemented and working
   - Messages classified into 3 slices
   - Critical messages processed within 100ms
   - Monitoring messages processed within 500ms
   - Analytics messages sent to cloud

✅ Fog node processing functional
   - ML predictions run locally
   - Critical alerts generated in <100ms
   - Local anomaly detection working
   - Data aggregation for cloud working

✅ Dashboard extensions complete
   - Fog node status displayed
   - MQTT middleware status displayed
   - Network slice metrics visible
   - Fog vs Cloud comparison charts
   - Real-time network visualization
   - All metrics from live system

✅ Demo scenario working
   - Stage 1 (Normal) → Analytics slice
   - Stage 2 (Warning) → Monitoring slice
   - Stage 3 (Critical) → Critical slice
   - Visible transitions on dashboard
   - Alerts generated at appropriate stages

✅ API endpoints functional
   - All new endpoints responding
   - WebSocket events streaming
   - Real metrics returned
   - Performance data available

✅ Docker deployment working
   - `docker-compose up` starts all services
   - MQTT broker ready within 5 seconds
   - Backend running within 10 seconds
   - Frontend accessible within 15 seconds
   - System fully operational after <1 minute

✅ Performance requirements met
   - Fog avg latency <100ms
   - MQTT latency <50ms
   - Dashboard updates every 1-2 seconds
   - Support 10+ simultaneous machines
   - Process >20 messages/second

✅ Code quality
   - All code documented
   - Follows Python/React best practices
   - No hard-coded values
   - Modular and maintainable
   - No fake implementations

---

# PART 15: SUMMARY

Build a complete, working IoT Predictive Maintenance System with:

1. **Existing Features** (Preserved)
   - Sensor simulation
   - ML-based prediction
   - Real-time dashboard
   - Database storage
   - Alert system

2. **New Fog Computing Features** (Added)
   - Three-layer architecture (IoT → Fog → Cloud)
   - Local ML prediction at Fog layer
   - Critical alert generation at edge
   - Data aggregation for cloud

3. **New MQTT Middleware** (Added)
   - Real MQTT broker
   - Publisher/subscriber pattern
   - QoS configuration
   - Latency measurement

4. **New Network Slicing** (Added)
   - 3 virtual network slices (Critical, Monitoring, Analytics)
   - Priority-based message routing
   - Queue management
   - Traffic classification

5. **Dashboard Extensions** (Added)
   - Fog node status
   - MQTT middleware status
   - Network slice metrics
   - Performance comparison charts
   - Interactive network visualization

The final system demonstrates a complete Industrial IoT architecture with edge computing, middleware communication, network optimization, and real-time predictive maintenance—all integrated as a working, deployable application.
