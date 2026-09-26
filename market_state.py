class MarketStateEngine:
    def detect(self, df):
        if df is None or len(df) < 50:
            return {"regime": "UNKNOWN", "reason": "Données insuffisantes"}
        c = df["Close"]
        fast = c.rolling(20).mean()
        slow = c.rolling(50).mean()
        spread = float((fast.iloc[-1] - slow.iloc[-1]) / slow.iloc[-1] * 100)
        regime = "RANGE" if abs(spread) < 0.15 else "TREND_BULLISH" if spread > 0 else "TREND_BEARISH"
        return {"regime": regime, "ma_spread_pct": spread}
