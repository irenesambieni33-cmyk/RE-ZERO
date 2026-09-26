from datetime import datetime, timezone

class DecisionHistory:
    def __init__(self):
        self._items = []
    def record(self, decision, reason=None):
        item = {"version": len(self._items)+1, "decision": decision,
                "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        self._items.append(item)
        return item
    def export(self):
        return list(self._items)
