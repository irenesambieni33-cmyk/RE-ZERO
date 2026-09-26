from datetime import datetime, timezone

class FreshnessManager:
    def score(self, timestamp):
        if timestamp is None:
            return 0.0
        age = (datetime.now(timezone.utc) - timestamp).total_seconds()
        if age <= 120:
            return 1.0
        if age <= 900:
            return 0.8
        if age <= 3600:
            return 0.5
        return 0.1
