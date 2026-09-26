class DataValidator:
    REQUIRED = ["Open", "High", "Low", "Close"]
    def validate(self, df):
        errors = []
        if df is None or df.empty:
            return False, ["EMPTY_DATA"]
        for c in self.REQUIRED:
            if c not in df.columns:
                errors.append("MISSING_" + c)
        if errors:
            return False, errors
        if df[self.REQUIRED].isna().any().any():
            errors.append("NAN_OHLC")
        if (df["High"] < df["Low"]).any():
            errors.append("HIGH_BELOW_LOW")
        return len(errors) == 0, errors
