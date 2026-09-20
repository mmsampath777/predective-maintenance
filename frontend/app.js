// Real-Time Industrial IoT Fog Computing & Network Slicing Dashboard Controller

let ws = null;
let autoDemoActive = false;
let alertsList = [];
let chartSliceTimeline = null;
let chartLatencyBreakdown = null;
let chartQueueDepth = null;
let chartTrafficDoughnut = null;

// Timeline data buffers (last 15 points)
const MAX_CHART_POINTS = 15;
const timelineLabels = [];
const dataCrit = [];
const dataMon = [];
const dataAna = [];
const queueCrit = [];
const queueMon = [];
const queueAna = [];

// Initialize Dashboard
document.addEventListener("DOMContentLoaded", () => {
    initClock();
    initCharts();
    connectWebSocket();
});

// Live Clock
function initClock() {
    const clockEl = document.getElementById("live-clock");
    setInterval(() => {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString();
    }, 1000);
}

// Initialize Chart.js charts
function initCharts() {
    Chart.defaults.color = "#9CA3AF";
    Chart.defaults.font.family = "'Inter', sans-serif";

    // 1. Slice Timeline Chart
    const ctxTimeline = document.getElementById("chart-slice-timeline").getContext("2d");
    chartSliceTimeline = new Chart(ctxTimeline, {
        type: "line",
        data: {
            labels: timelineLabels,
            datasets: [
                {
                    label: "Critical",
                    data: dataCrit,
                    borderColor: "#EF4444",
                    backgroundColor: "rgba(239, 68, 68, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: "Monitoring",
                    data: dataMon,
                    borderColor: "#F59E0B",
                    backgroundColor: "rgba(245, 158, 11, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: "Analytics",
                    data: dataAna,
                    borderColor: "#06B6D4",
                    backgroundColor: "rgba(6, 182, 212, 0.1)",
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: { grid: { color: "rgba(255, 255, 255, 0.05)" } },
                y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, beginAtZero: true }
            }
        }
    });

    // 2. Latency Breakdown Chart
    const ctxLatency = document.getElementById("chart-latency-breakdown").getContext("2d");
    chartLatencyBreakdown = new Chart(ctxLatency, {
        type: "bar",
        data: {
            labels: ["Critical Slice", "Monitoring Slice", "Analytics Slice"],
            datasets: [
                {
                    label: "MQTT Latency",
                    data: [12, 12, 12],
                    backgroundColor: "#06B6D4"
                },
                {
                    label: "Queue Wait",
                    data: [2, 18, 120],
                    backgroundColor: "#8B5CF6"
                },
                {
                    label: "Fog ML Processing",
                    data: [31, 35, 38],
                    backgroundColor: "#10B981"
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: { stacked: true, grid: { color: "rgba(255, 255, 255, 0.05)" } },
                y: { stacked: true, grid: { color: "rgba(255, 255, 255, 0.05)" }, beginAtZero: true }
            }
        }
    });

    // 3. Queue Depth Over Time
    const ctxQueue = document.getElementById("chart-queue-depth").getContext("2d");
    chartQueueDepth = new Chart(ctxQueue, {
        type: "line",
        data: {
            labels: timelineLabels,
            datasets: [
                {
                    label: "Critical Q",
                    data: queueCrit,
                    borderColor: "#EF4444",
                    borderWidth: 2,
                    tension: 0.2
                },
                {
                    label: "Monitoring Q",
                    data: queueMon,
                    borderColor: "#F59E0B",
                    borderWidth: 2,
                    tension: 0.2
                },
                {
                    label: "Analytics Q",
                    data: queueAna,
                    borderColor: "#06B6D4",
                    borderWidth: 2,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } }
            },
            scales: {
                x: { grid: { color: "rgba(255, 255, 255, 0.05)" } },
                y: { grid: { color: "rgba(255, 255, 255, 0.05)" }, beginAtZero: true }
            }
        }
    });

    // 4. Traffic Reduction Doughnut
    const ctxTraffic = document.getElementById("chart-traffic-doughnut").getContext("2d");
    chartTrafficDoughnut = new Chart(ctxTraffic, {
        type: "doughnut",
        data: {
            labels: ["Fog Edge Processed", "Cloud Forwarded"],
            datasets: [{
                data: [96.2, 3.8],
                backgroundColor: ["#10B981", "#3B82F6"],
                borderColor: "#111827",
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom", labels: { font: { size: 11 } } }
            },
            cutout: "70%"
        }
    });
}

// WebSocket Connection & Real-Time Sync with Polling Fallback
let isWsConnected = false;
let pollingTimer = null;

function connectWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    const wsStatusEl = document.getElementById("ws-status");
    const wsTextEl = document.getElementById("ws-text");

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            isWsConnected = true;
            stopPollingFallback();
            wsStatusEl.querySelector(".status-indicator").style.backgroundColor = "var(--color-emerald)";
            wsTextEl.textContent = "CONNECTED (WS)";
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        ws.onclose = () => {
            isWsConnected = false;
            startPollingFallback();
            setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
            ws.close();
        };
    } catch (e) {
        console.warn("WebSocket error:", e);
        startPollingFallback();
        setTimeout(connectWebSocket, 4000);
    }
}

function startPollingFallback() {
    if (pollingTimer) return;
    const wsStatusEl = document.getElementById("ws-status");
    const wsTextEl = document.getElementById("ws-text");
    
    const poll = async () => {
        if (isWsConnected) return;
        try {
            const [fog, middleware, slices, comparison, recent_events, simStatus] = await Promise.all([
                fetch('/api/fog/status').then(r => r.json()),
                fetch('/api/middleware/status').then(r => r.json()),
                fetch('/api/network/slices').then(r => r.json()),
                fetch('/api/analytics/fog-vs-cloud').then(r => r.json()),
                fetch('/api/fog/recent').then(r => r.json()),
                fetch('/api/simulation/status').then(r => r.json()).catch(() => ({ demo: { current_stage: 1, auto_cycle: false } }))
            ]);
            
            updateDashboard({
                fog,
                middleware,
                slices,
                comparison,
                recent_events,
                demo: simStatus.demo || { current_stage: 1, auto_cycle: false }
            });
            
            if (wsStatusEl && wsStatusEl.querySelector(".status-indicator")) {
                wsStatusEl.querySelector(".status-indicator").style.backgroundColor = "var(--color-emerald)";
            }
            if (wsTextEl) wsTextEl.textContent = "CONNECTED (POLL)";
        } catch (err) {
            if (wsStatusEl && wsStatusEl.querySelector(".status-indicator")) {
                wsStatusEl.querySelector(".status-indicator").style.backgroundColor = "var(--color-rose)";
            }
            if (wsTextEl) wsTextEl.textContent = "RECONNECTING...";
        }
    };
    
    poll();
    pollingTimer = setInterval(poll, 1200);
}

function stopPollingFallback() {
    if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
    }
}

// Update all components on live event
function updateDashboard(data) {
    if (!data) return;

    // 1. Fog Node Card
    if (data.fog) {
        document.getElementById("fog-processed").textContent = Number(data.fog.messages_processed || 0).toLocaleString();
        document.getElementById("fog-rate").textContent = `${data.fog.processing_rate || 0} msg/s`;
        document.getElementById("fog-time").textContent = `${data.fog.avg_processing_time_ms || 48} ms`;
        document.getElementById("fog-critical-count").textContent = data.fog.critical_messages || 0;
        document.getElementById("fog-uptime").textContent = `${data.fog.uptime_seconds || 0}s`;
        
        const badge = document.getElementById("fog-status-badge");
        badge.textContent = data.fog.status || "ONLINE";
    }

    // 2. MQTT Middleware Card
    if (data.middleware) {
        document.getElementById("mqtt-published").textContent = Number(data.middleware.published_messages || 0).toLocaleString();
        document.getElementById("mqtt-rate").textContent = `${data.middleware.messages_per_second || 0} msg/s`;
        document.getElementById("mqtt-latency").textContent = `${data.middleware.avg_latency_ms || 12} ms`;
        document.getElementById("mqtt-topics").textContent = data.middleware.active_topics || 4;
        
        document.getElementById("vis-mqtt-latency").textContent = `~${data.middleware.avg_latency_ms || 12}ms lat`;
        document.getElementById("vis-iot-rate").textContent = `${data.middleware.messages_per_second || 28} msg/s`;
    }

    // 3. Network Slices
    let critMsg = 0, monMsg = 0, anaMsg = 0;
    let critQueue = 0, monQueue = 0, anaQueue = 0;
    let critLat = 45, monLat = 120, anaLat = 850;

    if (data.slices && Array.isArray(data.slices)) {
        data.slices.forEach(s => {
            if (s.slice_id === "CRITICAL") {
                critMsg = s.messages;
                critQueue = s.queue_length;
                critLat = s.avg_latency_ms;
                document.getElementById("slice-crit-msgs").textContent = s.messages;
                document.getElementById("slice-crit-queue").textContent = s.queue_length;
                document.getElementById("slice-crit-lat").textContent = `${s.avg_latency_ms}ms`;
                document.getElementById("vis-q-crit").style.height = `${Math.min(24, Math.max(4, s.queue_length * 3))}px`;
            } else if (s.slice_id === "MONITORING") {
                monMsg = s.messages;
                monQueue = s.queue_length;
                monLat = s.avg_latency_ms;
                document.getElementById("slice-mon-msgs").textContent = s.messages;
                document.getElementById("slice-mon-queue").textContent = s.queue_length;
                document.getElementById("slice-mon-lat").textContent = `${s.avg_latency_ms}ms`;
                document.getElementById("vis-q-mon").style.height = `${Math.min(24, Math.max(4, s.queue_length * 2))}px`;
            } else if (s.slice_id === "ANALYTICS") {
                anaMsg = s.messages;
                anaQueue = s.queue_length;
                anaLat = s.avg_latency_ms;
                document.getElementById("slice-ana-msgs").textContent = s.messages;
                document.getElementById("slice-ana-queue").textContent = s.queue_length;
                document.getElementById("slice-ana-lat").textContent = `${s.avg_latency_ms}ms`;
                document.getElementById("vis-q-ana").style.height = `${Math.min(24, Math.max(4, s.queue_length * 1.5))}px`;
            }
        });
    }

    // 4. Fog vs Cloud Comparison
    if (data.comparison) {
        document.getElementById("fog-lat-disp").textContent = `${data.comparison.fog_avg_latency_ms || 48} ms`;
        document.getElementById("cloud-lat-disp").textContent = `${data.comparison.cloud_avg_latency_ms || 320} ms`;
        
        const redPercent = data.comparison.latency_reduction_percent || 85;
        document.getElementById("gain-badge").textContent = `${redPercent}% FASTER`;
        document.getElementById("latency-reduction-bar").style.width = `${redPercent}%`;
        
        const trafficRed = data.comparison.cloud_traffic_reduction_percent || 96.2;
        document.getElementById("traffic-red-disp").textContent = `${trafficRed}%`;
        document.getElementById("vis-cloud-saved").textContent = `${trafficRed}% saved`;
        document.getElementById("crit-alert-disp").textContent = `${data.comparison.critical_alert_time_fog_ms || 45}ms`;
        
        if (chartTrafficDoughnut) {
            chartTrafficDoughnut.data.datasets[0].data = [trafficRed, (100 - trafficRed)];
            chartTrafficDoughnut.update("none");
        }
    }

    // 5. Update Timeline Charts
    const timeLabel = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    timelineLabels.push(timeLabel);
    dataCrit.push(critMsg);
    dataMon.push(monMsg);
    dataAna.push(anaMsg);
    queueCrit.push(critQueue);
    queueMon.push(monQueue);
    queueAna.push(anaQueue);

    if (timelineLabels.length > MAX_CHART_POINTS) {
        timelineLabels.shift();
        dataCrit.shift();
        dataMon.shift();
        dataAna.shift();
        queueCrit.shift();
        queueMon.shift();
        queueAna.shift();
    }

    if (chartSliceTimeline) chartSliceTimeline.update("none");
    if (chartQueueDepth) chartQueueDepth.update("none");

    // Latency breakdown update
    if (chartLatencyBreakdown && data.latency_breakdown) {
        const lb = data.latency_breakdown;
        chartLatencyBreakdown.data.datasets[0].data = [lb.mqtt_latency_ms, lb.mqtt_latency_ms, lb.mqtt_latency_ms];
        chartLatencyBreakdown.data.datasets[1].data = [2, 18, 110];
        chartLatencyBreakdown.data.datasets[2].data = [lb.fog_processing_ms, lb.fog_processing_ms, lb.fog_processing_ms];
        chartLatencyBreakdown.update("none");
    }

    // 6. Demo Stage Display
    if (data.demo) {
        const stageNum = data.demo.current_stage;
        updateDemoStageUI(stageNum, data.demo.auto_cycle);
    }

    // 7. Recent Events & Target Machine Telemetry
    if (data.recent_events && data.recent_events.length > 0) {
        const targetEvent = data.recent_events.find(e => e.machine_id === "M-001") || data.recent_events[0];
        updateTelemetryCard(targetEvent);
        updateAlertsFeed(data.recent_events);
    }
}

// Update Target Machine Telemetry Card
function updateTelemetryCard(event) {
    if (!event) return;
    
    const prob = (event.failure_probability || 0.12) * 100;
    const status = event.health_status || "HEALTHY";
    
    const badge = document.getElementById("m001-health-badge");
    const probEl = document.getElementById("tel-prob");
    const barProb = document.getElementById("bar-prob");

    probEl.textContent = `${prob.toFixed(1)}%`;
    barProb.style.width = `${Math.min(100, prob)}%`;

    if (status === "CRITICAL" || prob > 70) {
        badge.textContent = `HEALTH SCORE: ${(100 - prob).toFixed(0)}% (CRITICAL)`;
        badge.className = "health-score-badge critical";
        probEl.className = "r-val text-critical";
        barProb.className = "r-fill fill-rose";
    } else if (status === "WARNING" || prob > 40) {
        badge.textContent = `HEALTH SCORE: ${(100 - prob).toFixed(0)}% (WARNING)`;
        badge.className = "health-score-badge warning";
        probEl.className = "r-val text-warning";
        barProb.className = "r-fill fill-amber";
    } else {
        badge.textContent = `HEALTH SCORE: ${(100 - prob).toFixed(0)}% (HEALTHY)`;
        badge.className = "health-score-badge";
        probEl.className = "r-val text-emerald";
        barProb.className = "r-fill fill-emerald";
    }

    // If payload details present in item
    if (event.payload) {
        const p = event.payload;
        if (p.temperature) {
            document.getElementById("tel-temp").textContent = `${p.temperature.toFixed(1)} °C`;
            document.getElementById("bar-temp").style.width = `${Math.min(100, (p.temperature / 120) * 100)}%`;
        }
        if (p.vibration) {
            document.getElementById("tel-vib").textContent = `${p.vibration.toFixed(2)} m/s²`;
            document.getElementById("bar-vib").style.width = `${Math.min(100, (p.vibration / 12) * 100)}%`;
        }
        if (p.current) {
            document.getElementById("tel-curr").textContent = `${p.current.toFixed(1)} A`;
            document.getElementById("bar-curr").style.width = `${Math.min(100, (p.current / 30) * 100)}%`;
        }
        if (p.rpm) {
            document.getElementById("tel-rpm").textContent = `${p.rpm} RPM`;
            document.getElementById("bar-rpm").style.width = `${Math.min(100, (p.rpm / 3000) * 100)}%`;
        }
        if (p.pressure) {
            document.getElementById("tel-press").textContent = `${p.pressure.toFixed(0)} PSI`;
            document.getElementById("bar-press").style.width = `${Math.min(100, (p.pressure / 250) * 100)}%`;
        }
    }
}

// Update Alerts & Action Feed
function updateAlertsFeed(events) {
    const feed = document.getElementById("alerts-feed");
    const countBadge = document.getElementById("alert-counter-badge");
    
    const alertEvents = events.filter(e => e.alert !== null && e.alert !== undefined);
    countBadge.textContent = `${alertEvents.length} ALERTS`;

    if (alertEvents.length === 0) {
        feed.innerHTML = `
            <div class="alert-empty-state">
                <span class="empty-icon">✓</span>
                <p>System operational. All machines running within nominal parameters.</p>
            </div>
        `;
        return;
    }

    let html = "";
    alertEvents.slice(0, 8).forEach(e => {
        const a = e.alert;
        const sevClass = a.severity === "CRITICAL" ? "critical" : "warning";
        const timeStr = new Date(a.generated_at * 1000).toLocaleTimeString();
        
        html += `
            <div class="alert-item ${sevClass}">
                <div class="alert-item-header">
                    <span class="alert-item-title">${a.title || a.message}</span>
                    <span class="alert-item-time">${timeStr}</span>
                </div>
                <div class="alert-item-msg">${a.message} (Failure Risk: ${(a.failure_probability * 100).toFixed(1)}%)</div>
                ${e.recommendation ? `<div class="alert-item-rec"><strong>Action:</strong> ${e.recommendation}</div>` : ""}
            </div>
        `;
    });
    feed.innerHTML = html;
}

// Demo Stage UI Switcher
function updateDemoStageUI(stageNum, autoActive) {
    const label = document.getElementById("current-stage-display");
    const dot = document.getElementById("system-status-dot");
    
    document.querySelectorAll(".btn-stage").forEach(b => b.classList.remove("active"));
    
    if (stageNum === 1) {
        label.textContent = "Stage 1: Normal Operation (Analytics Slice)";
        label.style.color = "var(--color-emerald)";
        dot.style.backgroundColor = "var(--color-emerald)";
        document.getElementById("btn-stage-1").classList.add("active");
    } else if (stageNum === 2) {
        label.textContent = "Stage 2: Warning State (Monitoring Slice)";
        label.style.color = "var(--color-amber)";
        dot.style.backgroundColor = "var(--color-amber)";
        document.getElementById("btn-stage-2").classList.add("active");
    } else if (stageNum === 3) {
        label.textContent = "Stage 3: Critical State (Critical Slice)";
        label.style.color = "var(--color-rose)";
        dot.style.backgroundColor = "var(--color-rose)";
        document.getElementById("btn-stage-3").classList.add("active");
    }

    const autoBtn = document.getElementById("btn-auto-demo");
    const autoIcon = document.getElementById("auto-demo-icon");
    if (autoActive) {
        autoBtn.classList.add("active");
        autoIcon.textContent = "⏸";
    } else {
        autoBtn.classList.remove("active");
        autoIcon.textContent = "▶";
    }
}

// Demo Controls Callbacks
async function setDemoStage(stageNum) {
    try {
        await fetch(`/api/simulation/stage/${stageNum}`, { method: "POST" });
    } catch (e) {
        console.error("Error setting demo stage:", e);
    }
}

async function toggleAutoDemo() {
    autoDemoActive = !autoDemoActive;
    try {
        await fetch(`/api/simulation/auto?enable=${autoDemoActive}&duration=20`, { method: "POST" });
    } catch (e) {
        console.error("Error toggling auto demo:", e);
    }
}

// ==========================================================
// Interactive Manual Telemetry Injector Handlers
// ==========================================================
function updateSliderUI(key, val, unit) {
    const el = document.getElementById(`val-${key}`);
    if (el) {
        el.textContent = `${Number(val).toFixed(key === 'rpm' || key === 'press' || key === 'cool' ? 0 : 1)} ${unit}`;
    }
}

function loadPreset(type) {
    if (type === 'nominal') {
        setSlider('temp', 45, '°C');
        setSlider('vib', 2.2, 'm/s²');
        setSlider('curr', 8.5, 'A');
        setSlider('rpm', 2200, 'RPM');
        setSlider('press', 100, 'PSI');
        setSlider('cool', 85, '%');
    } else if (type === 'overheat') {
        setSlider('temp', 78, '°C');
        setSlider('vib', 4.5, 'm/s²');
        setSlider('curr', 14.5, 'A');
        setSlider('rpm', 1950, 'RPM');
        setSlider('press', 140, 'PSI');
        setSlider('cool', 35, '%');
    } else if (type === 'bearing') {
        setSlider('temp', 98, '°C');
        setSlider('vib', 10.5, 'm/s²');
        setSlider('curr', 22.0, 'A');
        setSlider('rpm', 1250, 'RPM');
        setSlider('press', 195, 'PSI');
        setSlider('cool', 15, '%');
    } else if (type === 'electrical') {
        setSlider('temp', 92, '°C');
        setSlider('vib', 7.8, 'm/s²');
        setSlider('curr', 26.5, 'A');
        setSlider('rpm', 1400, 'RPM');
        setSlider('press', 170, 'PSI');
        setSlider('cool', 25, '%');
    }
}

function setSlider(key, val, unit) {
    const input = document.getElementById(`input-${key}`);
    if (input) {
        input.value = val;
        updateSliderUI(key, val, unit);
    }
}

async function injectManualTelemetry() {
    const machineId = document.getElementById('select-machine').value || 'M-001';
    const payload = {
        machine_id: machineId,
        temperature: parseFloat(document.getElementById('input-temp').value),
        vibration: parseFloat(document.getElementById('input-vib').value),
        current: parseFloat(document.getElementById('input-curr').value),
        rpm: parseInt(document.getElementById('input-rpm').value),
        pressure: parseFloat(document.getElementById('input-press').value),
        coolant_level: parseFloat(document.getElementById('input-cool').value),
        operating_hours: 3200
    };

    const resultEl = document.getElementById('injector-result');
    resultEl.style.display = 'flex';
    resultEl.innerHTML = `<span>⏳ Ingesting to MQTT broker...</span>`;

    try {
        const res = await fetch('/api/simulation/inject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        const slice = data.assigned_slice || 'ANALYTICS';
        const prob = ((data.failure_probability || 0.1) * 100).toFixed(1);
        const health = data.health_status || 'HEALTHY';
        
        resultEl.innerHTML = `
            <span>Target: <strong>${machineId}</strong></span>
            <span>Slice: <span class="inj-slice-tag ${slice}">${slice} (${data.priority})</span></span>
            <span>Failure Risk: <strong>${prob}%</strong></span>
            <span>Status: <strong>${health}</strong></span>
            ${data.alert ? `<span class="text-critical" style="margin-left:8px;">🚨 ${data.alert.severity} ALERT GENERATED</span>` : ""}
        `;
    } catch (e) {
        console.error('Error injecting manual telemetry:', e);
        resultEl.innerHTML = `<span class="text-critical">Error injecting telemetry</span>`;
    }
}

