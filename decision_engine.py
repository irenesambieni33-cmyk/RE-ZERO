"""Hierarchical decision engine. Direction is a scenario, not a price prediction."""
from __future__ import annotations
from typing import Dict, Any


def decide(result: Dict[str,Any], regime: Dict[str,Any], data_quality: Dict[str,Any], macro_risk: str = "NORMAL") -> Dict[str,Any]:
    direction=result.get("direction","NEUTRE")
    hard=[]; soft=[]
    if not data_quality.get("ok",False) or data_quality.get("score",0)<70: hard.append("Qualité des données insuffisante.")
    if regime.get("base") == "RANGE" and direction in {"ACHAT","VENTE"}: soft.append("Marché en range: privilégier les extrêmes et éviter les poursuites de mouvement.")
    if regime.get("volatility") == "EXPANSION": soft.append("Expansion de volatilité: attendre une confirmation et élargir l'invalidation si nécessaire.")
    if macro_risk in {"BLOQUÉ / CHOC MACRO","TRÈS ÉLEVÉ"}: hard.append(f"Risque macro {macro_risk}.")
    if direction not in {"ACHAT","VENTE"}: hard.append("Aucun scénario directionnel suffisamment structuré.")
    usable=[result.get("timeframes",{}).get(tf,{}) for tf in ("D1","H4","H1","M15","M5")]
    avail=[x for x in usable if x.get("available")]
    if len(avail)<4: hard.append("Couverture multi-timeframe incomplète.")
    status="REJETÉ" if hard else "CANDIDAT" if soft else "CANDIDAT FORT"
    return {"status":status,"hard_blocks":hard,"soft_warnings":soft,"scenario":direction,
            "thesis": "Scénario conditionnel, pas une prédiction: le trade n'est autorisé que si les barrières de risque et de qualité restent valides au moment de l'exécution.",
            "note":"Le moteur ne transforme jamais un score de qualité en probabilité de gain."}
