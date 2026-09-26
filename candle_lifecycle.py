class CandleLifecycleManager:
    def status(self, df):
        return {"state": "UNKNOWN" if df is None or df.empty else "LATEST_CANDLE_UNVERIFIED"}
