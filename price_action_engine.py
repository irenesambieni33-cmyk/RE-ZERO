class PriceActionEngine:
    def analyze(self, df):
        if df is None or len(df) < 3:
            return {"status": "INSUFFICIENT"}
        a, b = df.iloc[-2], df.iloc[-1]
        bullish = b["Close"] > b["Open"] and a["Close"] < a["Open"] and b["Close"] >= a["Open"] and b["Open"] <= a["Close"]
        bearish = b["Close"] < b["Open"] and a["Close"] > a["Open"] and b["Open"] >= a["Close"] and b["Close"] <= a["Open"]
        return {"engulfing": "BULLISH" if bullish else "BEARISH" if bearish else "NONE"}
