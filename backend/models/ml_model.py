"""
ML Model Training and Inference for IoT Predictive Maintenance.
Trains a Random Forest classifier on synthetic industrial telemetry data
and provides inference for failure probability and machine health state.
"""

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")

FEATURE_COLUMNS = [
    "temperature",
    "vibration",
    "current",
    "rpm",
    "pressure",
    "coolant_level",
    "operating_hours",
    "stress_index"
]

def generate_synthetic_data(num_samples: int = 12000, random_state: int = 42) -> pd.DataFrame:
    """Generate 10,000+ realistic synthetic industrial sensor telemetry samples."""
    np.random.seed(random_state)
    
    # 70% Normal/Healthy, 20% Degrading/Warning, 10% Critical/Failure
    n_healthy = int(num_samples * 0.70)
    n_warning = int(num_samples * 0.20)
    n_critical = num_samples - n_healthy - n_warning
    
    # 1. Healthy state
    h_temp = np.random.normal(45, 8, n_healthy)
    h_vib = np.random.normal(2.5, 0.8, n_healthy)
    h_curr = np.random.normal(8.5, 1.5, n_healthy)
    h_rpm = np.random.normal(2200, 150, n_healthy)
    h_press = np.random.normal(100, 12, n_healthy)
    h_cool = np.random.normal(85, 8, n_healthy)
    h_hours = np.random.uniform(50, 3000, n_healthy)
    h_stress = (h_temp / 100.0) * 0.3 + (h_vib / 10.0) * 0.4 + (h_curr / 25.0) * 0.3
    h_label = np.zeros(n_healthy, dtype=int)
    
    # 2. Warning state
    w_temp = np.random.normal(75, 6, n_warning)
    w_vib = np.random.normal(6.2, 0.9, n_warning)
    w_curr = np.random.normal(16.0, 2.0, n_warning)
    w_rpm = np.random.normal(1800, 200, n_warning)
    w_press = np.random.normal(150, 18, n_warning)
    w_cool = np.random.normal(45, 12, n_warning)
    w_hours = np.random.uniform(3000, 7000, n_warning)
    w_stress = (w_temp / 100.0) * 0.3 + (w_vib / 10.0) * 0.4 + (w_curr / 25.0) * 0.3
    w_label = np.zeros(n_warning, dtype=int)  # Not yet failed, but warning
    
    # 3. Critical state
    c_temp = np.random.normal(96, 5, n_critical)
    c_vib = np.random.normal(9.0, 1.0, n_critical)
    c_curr = np.random.normal(23.0, 2.2, n_critical)
    c_rpm = np.random.normal(1300, 250, n_critical)
    c_press = np.random.normal(190, 20, n_critical)
    c_cool = np.random.normal(18, 8, n_critical)
    c_hours = np.random.uniform(6000, 10000, n_critical)
    c_stress = (c_temp / 100.0) * 0.3 + (c_vib / 10.0) * 0.4 + (c_curr / 25.0) * 0.3
    c_label = np.ones(n_critical, dtype=int)  # Imminent failure
    
    # Also mark 25% of warning as approaching failure for continuous probability calibration
    w_failure_indices = np.random.choice(n_warning, size=int(n_warning * 0.35), replace=False)
    w_label[w_failure_indices] = 1

    temp = np.concatenate([h_temp, w_temp, c_temp])
    vib = np.concatenate([h_vib, w_vib, c_vib])
    curr = np.concatenate([h_curr, w_curr, c_curr])
    rpm = np.concatenate([h_rpm, w_rpm, c_rpm])
    press = np.concatenate([h_press, w_press, c_press])
    cool = np.concatenate([h_cool, w_cool, c_cool])
    hours = np.concatenate([h_hours, w_hours, c_hours])
    stress = np.concatenate([h_stress, w_stress, c_stress])
    label = np.concatenate([h_label, w_label, c_label])
    
    df = pd.DataFrame({
        "temperature": np.clip(temp, 10, 130),
        "vibration": np.clip(vib, 0.1, 15),
        "current": np.clip(curr, 2, 35),
        "rpm": np.clip(rpm, 500, 3500),
        "pressure": np.clip(press, 20, 250),
        "coolant_level": np.clip(cool, 0, 100),
        "operating_hours": hours,
        "stress_index": np.clip(stress, 0.05, 1.5),
        "failure": label
    })
    return df

def train_and_save_model():
    """Train Random Forest classifier on synthetic dataset and save model & scaler."""
    print("Generating synthetic industrial dataset (12,000 samples)...")
    df = generate_synthetic_data(12000)
    
    X = df[FEATURE_COLUMNS]
    y = df["failure"]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=12,
        min_samples_split=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_scaled, y_train)
    
    train_acc = model.score(X_train_scaled, y_train)
    test_acc = model.score(X_test_scaled, y_test)
    print(f"Model trained successfully. Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}")
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"Saved model to {MODEL_PATH} and scaler to {SCALER_PATH}")
    return model, scaler

class Predictor:
    """Predictor class for Fog Node and Cloud ML inference."""
    
    def __init__(self):
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            self.model, self.scaler = train_and_save_model()
        else:
            self.model = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            
    def compute_features(self, payload: dict) -> list:
        """Extract and compute the feature vector from sensor payload."""
        temp = float(payload.get("temperature", 45.0))
        vib = float(payload.get("vibration", 2.5))
        curr = float(payload.get("current", 8.5))
        rpm = float(payload.get("rpm", 2200.0))
        press = float(payload.get("pressure", 100.0))
        cool = float(payload.get("coolant_level", 85.0))
        hours = float(payload.get("operating_hours", 1000.0))
        
        # Derived stress index
        stress = (temp / 100.0) * 0.3 + (vib / 10.0) * 0.4 + (curr / 25.0) * 0.3
        return [temp, vib, curr, rpm, press, cool, hours, stress]
        
    def predict_failure_probability(self, payload: dict) -> float:
        """Predict failure probability (0.0 to 1.0) for a given sensor payload."""
        features = self.compute_features(payload)
        features_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        features_scaled = self.scaler.transform(features_df)
        proba = self.model.predict_proba(features_scaled)[0][1]
        
        # Extreme rule-based boost if values are dangerously beyond critical thresholds
        temp = float(payload.get("temperature", 45.0))
        vib = float(payload.get("vibration", 2.5))
        curr = float(payload.get("current", 8.5))
        if temp > 95 or vib > 8.5 or curr > 22:
            proba = max(proba, 0.88)
        elif temp > 75 or vib > 5.5 or curr > 15:
            proba = max(proba, 0.48)
            
        return float(np.clip(proba, 0.0, 1.0))
        
    def classify_health(self, failure_prob: float) -> str:
        """Classify machine health state based on failure probability."""
        if failure_prob > 0.70:
            return "CRITICAL"
        elif failure_prob > 0.40:
            return "WARNING"
        else:
            return "HEALTHY"

# Global singleton predictor instance
predictor = Predictor()
