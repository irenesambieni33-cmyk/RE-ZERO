class MTFEngine:
    """Confluence de régime sur plusieurs timeframes de la hiérarchie MTF (config.json).
    Informatif seulement pour l'instant : ne bloque pas encore la décision (voir README)."""

    def __init__(self, data_engine, indicator_engine, state_engine, max_frames=3):
        self.data = data_engine
        self.ind = indicator_engine
        self.state = state_engine
        self.max_frames = max_frames

    def analyze(self, asset, ticker, base_timeframe, hierarchy, is_proxy=False, proxy_instrument=None):
        if not hierarchy or base_timeframe not in hierarchy:
            frames = [base_timeframe]
        else:
            idx = hierarchy.index(base_timeframe)
            # les `max_frames` timeframes les plus proches du timeframe de base, lui inclus
            frames = hierarchy[:idx + 1][-self.max_frames:]

        per_tf = {}
        for tf in frames:
            dr = self.data.fetch(asset, ticker, tf, is_proxy, proxy_instrument)
            if dr.data is None or dr.status not in ("VALID", "DEGRADED"):
                per_tf[tf] = {"regime": "UNKNOWN", "reason": "DATA_UNAVAILABLE"}
                continue
            df = self.ind.calculate(dr.data)
            per_tf[tf] = self.state.detect(df)

        regimes = [v.get("regime") for v in per_tf.values()]
        known = [r for r in regimes if r not in (None, "UNKNOWN")]
        if not known:
            alignment = "UNKNOWN"
        elif len(set(known)) == 1 and len(known) == len(regimes):
            alignment = f"ALIGNED_{known[0]}"
        else:
            alignment = "MIXED"

        return {
            "base_timeframe": base_timeframe,
            "frames_analyzed": frames,
            "per_timeframe": per_tf,
            "alignment": alignment,
            "note": "Confluence informative — n'est pas (encore) un hard gate de décision.",
        }
