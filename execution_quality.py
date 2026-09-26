class ExecutionQualityEngine:
    def evaluate(self, spread_available=False, data_fresh=True, event_lock=False):
        reasons = []
        if not spread_available: reasons.append("SPREAD_UNAVAILABLE")
        if not data_fresh: reasons.append("STALE_DATA")
        if event_lock: reasons.append("NEWS_LOCK")
        return {"acceptable": not reasons, "reasons": reasons,
                "quality": "ACCEPTABLE" if not reasons else "BLOCKED"}
