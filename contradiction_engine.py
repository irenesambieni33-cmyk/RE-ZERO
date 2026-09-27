class ContradictionEngine:
    """Détecte des contradictions simples entre les couches d'évidence déjà calculées
    (régime vs structure, régime vs price action). Ignore volontairement toute donnée
    non présente dans le ledger plutôt que de supposer."""

    def check(self, evidence):
        by_source = {item["source"]: item["observation"] for item in (evidence or [])}
        regime = (by_source.get("REGIME") or {}).get("regime")
        structure = by_source.get("STRUCTURE") or {}
        pa = by_source.get("PRICE_ACTION") or {}
        highs, lows = structure.get("swing_highs") or [], structure.get("swing_lows") or []

        contradictions = []
        if regime == "TREND_BULLISH" and len(lows) >= 2 and lows[-1] < lows[-2]:
            contradictions.append("Régime haussier mais swing lows descendants (structure baissière).")
        if regime == "TREND_BEARISH" and len(highs) >= 2 and highs[-1] > highs[-2]:
            contradictions.append("Régime baissier mais swing highs ascendants (structure haussière).")
        if regime == "TREND_BULLISH" and pa.get("engulfing") == "BEARISH":
            contradictions.append("Régime haussier mais engulfing baissier sur la dernière bougie.")
        if regime == "TREND_BEARISH" and pa.get("engulfing") == "BULLISH":
            contradictions.append("Régime baissier mais engulfing haussier sur la dernière bougie.")

        status = "CONTRADICTION_DETECTED" if contradictions else "NO_CRITICAL_CONTRADICTION_DETECTED"
        return {"contradictions": contradictions, "status": status,
                "note": "Absence de contradiction ≠ validation."}
