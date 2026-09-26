class SystemState:
    STATES = ("BOOT","INITIALIZING","DATA_LOADING","VALIDATING","READY","ANALYZING","DECISION_READY","MONITORING","DEGRADED","SAFE_MODE","BLOCKED","RECOVERY")
    def __init__(self): self.state = "BOOT"
    def set(self, state):
        if state not in self.STATES: raise ValueError("INVALID_SYSTEM_STATE")
        self.state = state
        return self.state
