from datetime import datetime, timezone
class MarketClock:
    @staticmethod
    def now():
        return datetime.now(timezone.utc)
