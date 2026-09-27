from datetime import datetime, timezone

class ExecutionQualityEngine:
    """yfinance ne fournit pas de flux bid/ask : il n'y a pas de spread réel disponible.
    Plutôt que de fabriquer une valeur, ce moteur utilise un proxy honnête et vérifiable
    (marché probablement fermé le week-end pour forex/futures) et l'étiquette comme tel.
    Un vrai spread nécessiterait un flux broker/L1 — non branché ici."""

    WEEKEND_CLOSED_ASSETS = {"EUR/USD", "XAU/USD (GC=F PROXY)"}  # forex/futures ferment le week-end ; pas la crypto

    def evaluate(self, asset=None, now_utc=None, data_fresh=True, event_lock=False):
        now_utc = now_utc or datetime.now(timezone.utc)
        reasons = []
        if now_utc.weekday() >= 5 and asset in self.WEEKEND_CLOSED_ASSETS:
            reasons.append("MARKET_LIKELY_CLOSED_WEEKEND")
        if not data_fresh:
            reasons.append("STALE_DATA")
        if event_lock:
            reasons.append("NEWS_LOCK")
        return {
            "acceptable": not reasons,
            "reasons": reasons,
            "quality": "ACCEPTABLE" if not reasons else "BLOCKED",
            "spread_available": False,
            "note": "Proxy de session (pas de vrai spread bid/ask — flux broker non branché).",
        }
