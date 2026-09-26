class IndicatorDependencyEngine:
    def analyze(self, names):
        groups = {}
        for name in names:
            groups.setdefault(name.split("_")[0], []).append(name)
        return {
            "warning": "Les indicateurs basés sur le même OHLC ne sont pas des confirmations indépendantes.",
            "groups": groups
        }
