"""
Demonstration Scenario Controller.
Orchestrates the 3-stage demonstration:
Stage 1: Normal Operation (0-60s) -> Analytics Slice
Stage 2: Warning State (60-120s) -> Monitoring Slice
Stage 3: Critical State (120-180s) -> Critical Slice
"""

import time
import threading
from backend.simulation.iot_simulator import iot_simulator

class DemoScenarioController:
    def __init__(self, simulator=iot_simulator):
        self.simulator = simulator
        self.current_stage = 1
        self.stage_names = {
            1: "NORMAL_OPERATION",
            2: "WARNING_STATE",
            3: "CRITICAL_STATE"
        }
        self.auto_cycle = False
        self.auto_thread = None
        self.stage_duration_sec = 20  # Duration per stage in auto mode
        self.stage_start_time = time.time()
        self.target_machine = "M-001"

    def set_stage(self, stage_num: int):
        """Manually trigger a demo stage."""
        if stage_num not in [1, 2, 3]:
            return {"error": "Invalid stage number. Choose 1, 2, or 3."}
            
        self.current_stage = stage_num
        self.stage_start_time = time.time()
        
        if stage_num == 1:
            self.simulator.set_machine_override(self.target_machine, "NORMAL")
            desc = "Stage 1: Normal Operation (Analytics Slice, ~12% Failure Risk, Normal Operation)"
        elif stage_num == 2:
            self.simulator.set_machine_override(self.target_machine, "WARNING")
            desc = "Stage 2: Warning State (Monitoring Slice, ~58% Failure Risk, Degradation Warning)"
        else:
            self.simulator.set_machine_override(self.target_machine, "CRITICAL")
            desc = "Stage 3: Critical State (Critical Slice, ~92% Failure Risk, Immediate Emergency Alert)"
            
        print(f"[DemoScenario] Switched to {desc}")
        return {
            "current_stage": self.current_stage,
            "stage_name": self.stage_names[self.current_stage],
            "description": desc,
            "target_machine": self.target_machine,
            "timestamp": time.time()
        }

    def start_auto_demo(self, stage_duration: int = 20):
        """Run through Stage 1 -> Stage 2 -> Stage 3 automatically."""
        self.stage_duration_sec = stage_duration
        self.auto_cycle = True
        if not self.auto_thread or not self.auto_thread.is_alive():
            self.auto_thread = threading.Thread(target=self._auto_loop, daemon=True)
            self.auto_thread.start()
        return {"status": "Auto demo started", "stage_duration": stage_duration}

    def stop_auto_demo(self):
        self.auto_cycle = False
        return {"status": "Auto demo stopped"}

    def _auto_loop(self):
        while self.auto_cycle:
            for s in [1, 2, 3]:
                if not self.auto_cycle:
                    break
                self.set_stage(s)
                time.sleep(self.stage_duration_sec)

    def get_status(self) -> dict:
        elapsed = int(time.time() - self.stage_start_time)
        return {
            "current_stage": self.current_stage,
            "stage_name": self.stage_names[self.current_stage],
            "auto_cycle": self.auto_cycle,
            "stage_duration_sec": self.stage_duration_sec,
            "stage_elapsed_sec": elapsed,
            "target_machine": self.target_machine
        }

demo_controller = DemoScenarioController()
