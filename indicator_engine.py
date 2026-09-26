import numpy as np
import pandas as pd

class IndicatorEngine:
    def calculate(self, df):
        x = df.copy()
        c, h, l = x["Close"], x["High"], x["Low"]

        for n in [20, 50, 100, 200]:
            x[f"SMA_{n}"] = c.rolling(n).mean()
        for n in [9, 21, 50, 200]:
            x[f"EMA_{n}"] = c.ewm(span=n, adjust=False).mean()

        d = c.diff()
        gain = d.clip(lower=0)
        loss = -d.clip(upper=0)
        rs = gain.rolling(14).mean() / loss.rolling(14).mean().replace(0, np.nan)
        x["RSI_14"] = 100 - 100 / (1 + rs)

        fast = c.ewm(span=12, adjust=False).mean()
        slow = c.ewm(span=26, adjust=False).mean()
        x["MACD"] = fast - slow
        x["MACD_SIGNAL"] = x["MACD"].ewm(span=9, adjust=False).mean()

        tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
        x["ATR_14"] = tr.rolling(14).mean()

        mid = c.rolling(20).mean()
        sd = c.rolling(20).std()
        x["BB_MID"] = mid
        x["BB_UPPER"] = mid + 2*sd
        x["BB_LOWER"] = mid - 2*sd

        low14 = l.rolling(14).min()
        high14 = h.rolling(14).max()
        x["STOCH_K"] = 100*(c-low14)/(high14-low14).replace(0, np.nan)
        x["STOCH_D"] = x["STOCH_K"].rolling(3).mean()

        if "Volume" in x.columns:
            x["VOLUME_MA_20"] = x["Volume"].rolling(20).mean()
        return x
