class StructureEngine:
    def analyze(self, df, window=3):
        if df is None or len(df) < 10:
            return {"status": "INSUFFICIENT"}
        h, l = df["High"], df["Low"]
        highs, lows = [], []
        for i in range(window, len(df)-window):
            if h.iloc[i] == h.iloc[i-window:i+window+1].max():
                highs.append(float(h.iloc[i]))
            if l.iloc[i] == l.iloc[i-window:i+window+1].min():
                lows.append(float(l.iloc[i]))
        return {"swing_highs": highs[-5:], "swing_lows": lows[-5:], "bias": "UNCONFIRMED"}
