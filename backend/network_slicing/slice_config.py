"""
Network Slicing Configuration.
Defines slice categories, priority levels, and threshold parameters.
"""

# Slice IDs
SLICE_CRITICAL = "CRITICAL"
SLICE_MONITORING = "MONITORING"
SLICE_ANALYTICS = "ANALYTICS"

# Priority levels (Lower number = Higher Priority)
PRIORITY_MAP = {
    SLICE_CRITICAL: 1,      # Highest Priority
    SLICE_MONITORING: 2,    # Medium Priority
    SLICE_ANALYTICS: 3      # Lowest Priority
}

# Thresholds
CRITICAL_FAILURE_PROB_THRESHOLD = 0.70
MONITORING_FAILURE_PROB_THRESHOLD = 0.40

# Hardware sensor extreme triggers (instant critical classification)
CRITICAL_TEMP_THRESHOLD = 95.0       # °C
CRITICAL_VIBRATION_THRESHOLD = 8.0   # m/s²
CRITICAL_CURRENT_THRESHOLD = 20.0    # A
CRITICAL_PRESSURE_THRESHOLD = 210.0  # PSI

# Warning sensor triggers (monitoring classification)
WARNING_TEMP_THRESHOLD = 70.0        # °C
WARNING_VIBRATION_THRESHOLD = 5.0    # m/s²
WARNING_CURRENT_THRESHOLD = 14.0     # A
