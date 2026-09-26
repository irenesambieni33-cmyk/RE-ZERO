import yfinance as yf

class ProviderManager:
    def fetch(self, ticker, period="60d", interval="15m"):
        return yf.download(ticker, period=period, interval=interval, auto_adjust=False, progress=False)
