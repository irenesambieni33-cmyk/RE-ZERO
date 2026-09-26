class DataQuality:
    def score(self, df, errors):
        if errors:
            return 0.0
        if df is None or len(df) < 50:
            return 0.35
        return 1.0
