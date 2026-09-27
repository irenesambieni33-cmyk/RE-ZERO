def derive_levels(df, state, structure, min_rr=2.0):
    """Dérive entry/stop/target à partir de la structure réellement détectée.
    - entry = dernière clôture
    - stop  = dernier swing opposé au sens du régime (invalidation structurelle réelle)
    - target = entry +/- (min_rr * risque) : c'est une cible de gestion du risque
      (méthode RR standard), PAS une prédiction de niveau atteint.
    Retourne None si le régime n'est pas directionnel ou si les swings nécessaires
    sont absents/incohérents — on ne fabrique jamais de niveau."""
    if df is None or not len(df):
        return None
    regime = (state or {}).get("regime")
    highs = (structure or {}).get("swing_highs") or []
    lows = (structure or {}).get("swing_lows") or []
    entry = float(df["Close"].iloc[-1])

    if regime == "TREND_BULLISH" and lows:
        stop = float(lows[-1])
        if stop >= entry:
            return None
        risk = entry - stop
        target = entry + min_rr * risk
        return {"direction": "LONG", "entry": entry, "stop": stop, "target": target,
                "basis": "Stop = dernier swing low. Target = RR minimum x risque (pas une prédiction)."}

    if regime == "TREND_BEARISH" and highs:
        stop = float(highs[-1])
        if stop <= entry:
            return None
        risk = stop - entry
        target = entry - min_rr * risk
        return {"direction": "SHORT", "entry": entry, "stop": stop, "target": target,
                "basis": "Stop = dernier swing high. Target = RR minimum x risque (pas une prédiction)."}

    return None
