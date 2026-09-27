class ScenarioEngine:
    """Construit des scénarios ancrés sur la structure/régime réellement détectés.
    Les invalidations pointent vers des niveaux de swing réels quand ils existent ;
    sinon le scénario reste explicitement marqué comme indéterminé (pas de niveau inventé)."""

    def build(self, state, structure, liquidity, price_action):
        regime = (state or {}).get("regime", "UNKNOWN")
        highs = (structure or {}).get("swing_highs") or []
        lows = (structure or {}).get("swing_lows") or []
        scenarios = []

        if highs and lows:
            nearest_high, nearest_low = highs[-1], lows[-1]
            scenarios.append({
                "scenario": "Continuation haussière",
                "condition": f"Clôture au-dessus de {nearest_high}",
                "invalidation": f"Clôture sous {nearest_low} (dernier swing low)",
            })
            scenarios.append({
                "scenario": "Continuation baissière",
                "condition": f"Clôture sous {nearest_low}",
                "invalidation": f"Clôture au-dessus de {nearest_high} (dernier swing high)",
            })
            scenarios.append({
                "scenario": "Range / fakeout",
                "condition": f"Prix contenu entre {nearest_low} et {nearest_high}",
                "invalidation": "Cassure confirmée (clôture) d'une des deux bornes ci-dessus",
            })
        else:
            scenarios.append({
                "scenario": "Indéterminé",
                "condition": "Structure insuffisante pour définir des niveaux",
                "invalidation": "À définir — pas assez de swings détectés",
            })

        for s in scenarios:
            s["regime_context"] = regime
        return scenarios
