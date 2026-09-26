from datetime import datetime, timezone
class DataProvenance:
    def build(self, provider, ticker, timeframe, is_proxy=False):
        return {
            "provider": provider,
            "ticker": ticker,
            "timeframe": timeframe,
            "is_proxy": is_proxy,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
