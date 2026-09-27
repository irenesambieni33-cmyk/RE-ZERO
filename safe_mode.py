class SafeMode:
    def block(self, reason):
        return {"safe_mode": True, "reason": reason, "action": "NO NEW TRADE DECISION"}
