# ============================================
# BREAKPOINT SUPPORT - AUTO-INJECTED
# ============================================
import json
import os
import time

class BreakpointManager:
    """Handles breakpoint checking during execution"""
    
    def __init__(self):
        self.breakpoints = self._load_breakpoints()
        self.status_file = "json_info/breakpoint_status.json"
        self.continue_file = "json_info/breakpoint_continue.json"
        os.makedirs("json_info", exist_ok=True)
        
    def _load_breakpoints(self):
        """Load breakpoints from JSON file"""
        try:
            if os.path.exists("json_info/breakpoints.json"):
                with open("json_info/breakpoints.json", "r") as f:
                    data = json.load(f)
                    return set(data.get("breakpoints", []))
        except Exception as e:
            pass
        return set()
    
    def check(self, task_index):
        """Check if execution should pause at this task index"""
        if task_index in self.breakpoints:
            
            # Signal that breakpoint is hit
            with open(self.status_file, "w") as f:
                json.dump({"status": "paused", "task_index": task_index}, f)
            
            # Wait for continue signal
            while True:
                if os.path.exists(self.continue_file):
                    os.remove(self.continue_file)
                    if os.path.exists(self.status_file):
                        os.remove(self.status_file)
                    break
                time.sleep(0.1)

# Initialize breakpoint manager
_breakpoint_manager = BreakpointManager()

def check_breakpoint(task_index):
    """Check if breakpoint is set for this task"""
    _breakpoint_manager.check(task_index)
# ============================================
# END BREAKPOINT SUPPORT
# ============================================