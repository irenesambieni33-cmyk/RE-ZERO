class LiquidityEngine:
    def analyze(self, df):
        if df is None or len(df) < 2:
            return {"status": "INSUFFICIENT"}
        return {
            "inferred_zones": {
                "previous_high": float(df["High"].iloc[-2]),
                "previous_low": float(df["Low"].iloc[-2])
            },
            "truth": "INFERRED",
            "warning": "Une zone n'est pas une preuve d'ordres institutionnels."
        }
