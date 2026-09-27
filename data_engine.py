from .provider_manager import ProviderManager
from .validator import DataValidator
from .data_quality import DataQuality
from .freshness import FreshnessManager
from .market_clock import MarketClock
from core.models import DataResult

# yfinance n'a pas d'intervalle "4h" natif : H4 est reconstruit à partir de bougies H1 (voir _resample_h4).
INTERVAL = {"M15":"15m", "M30":"30m", "H1":"60m", "H4":"60m", "D1":"1d"}
RESAMPLE_RULE = {"H4": "4h"}

class DataEngine:
    def __init__(self):
        self.provider = ProviderManager()
        self.validator = DataValidator()
        self.quality = DataQuality()
        self.freshness = FreshnessManager()

    @staticmethod
    def _resample(df, rule):
        if df is None or df.empty:
            return df
        agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
        if "Volume" in df.columns:
            agg["Volume"] = "sum"
        out = df.resample(rule).agg(agg)
        return out.dropna(subset=["Open", "High", "Low", "Close"])

    def fetch(self, asset, ticker, timeframe, is_proxy=False, proxy_instrument=None):
        received = MarketClock.now()
        try:
            df = self.provider.fetch(ticker, interval=INTERVAL.get(timeframe, "15m"))
            rule = RESAMPLE_RULE.get(timeframe)
            if rule:
                df = self._resample(df, rule)
            ok, errors = self.validator.validate(df)
            quality = self.quality.score(df, errors)
            status = "VALID" if ok and quality >= 0.9 else "DEGRADED" if ok else "CORRUPTED"
            last = df.index[-1].to_pydatetime() if ok and len(df) else None
            if last and last.tzinfo is None:
                last = last.replace(tzinfo=received.tzinfo)
            warnings = ["PROXY DATA: GC=F utilisé comme proxy de XAU/USD."] if is_proxy else []
            return DataResult(status, df, "Yahoo Finance", "yfinance", "runtime",
                received, last, timeframe, asset, "UTC", quality,
                self.freshness.score(last), 0.0, errors, warnings, True,
                is_proxy, proxy_instrument)
        except Exception as e:
            return DataResult("INSUFFICIENT", None, "Yahoo Finance", "yfinance", "runtime",
                received, None, timeframe, asset, "UTC", 0, 0, 0,
                [str(e)], [], False, is_proxy, proxy_instrument)
