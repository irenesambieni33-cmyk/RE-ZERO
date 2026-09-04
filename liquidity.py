"""Liquidity-map engine for M15 trade planning.

This is a price-action approximation of liquidity pools. It does not claim to see
institutional order flow or hidden orders that are not present in the public data.
"""
from __future__ import annotations
from typing import Dict, Any, List
import math
import numpy as np
import pandas as pd


def _cluster(values: List[float], tolerance: float) -> List[Dict[str, Any]]:
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return []
    groups: List[List[float]] = [[values[0]]]
    for v in values[1:]:
        center = float(np.mean(groups[-1]))
        if abs(v - center) <= tolerance:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [
        {"price": float(np.mean(g)), "touches": len(g), "low": min(g), "high": max(g),
         "strength": round(min(100.0, 35.0 + 15.0 * len(g)), 1)}
        for g in groups if len(g) >= 2
    ]


def build_liquidity_map(m15_df: pd.DataFrame, structure: Dict[str, Any] | None = None,
                        atr: float | None = None, lookback: int = 120) -> Dict[str, Any]:
    if m15_df is None or m15_df.empty or len(m15_df) < 30:
        return {"ok": False, "pools": [], "nearest": None, "bias": "INCONNU", "note": "Données M15 insuffisantes."}
    df = m15_df.tail(lookback).copy()
    close = float(df["close"].iloc[-1])
    if atr is None or not math.isfinite(float(atr)) or atr <= 0:
        atr = float((df["high"] - df["low"]).rolling(14).mean().iloc[-1])
    tolerance = max(float(atr) * 0.18, close * 0.00035)

    highs = df["high"].astype(float).to_numpy()
    lows = df["low"].astype(float).to_numpy()
    local_highs, local_lows = [], []
    for i in range(2, len(df) - 2):
        if highs[i] >= max(highs[i-2:i+3]): local_highs.append(highs[i])
        if lows[i] <= min(lows[i-2:i+3]): local_lows.append(lows[i])

    if structure:
        local_highs += [x["price"] for x in structure.get("swings", {}).get("highs", [])[-10:]]
        local_lows += [x["price"] for x in structure.get("swings", {}).get("lows", [])[-10:]]

    eq_highs = _cluster(local_highs, tolerance)
    eq_lows = _cluster(local_lows, tolerance)
    pools: List[Dict[str, Any]] = []
    for z in eq_highs:
        if z["price"] > close:
            z.update({"type": "LIQUIDITÉ AU-DESSUS", "side": "BUY_STOP_POOL", "distance_atr": (z["price"]-close)/atr})
            pools.append(z)
    for z in eq_lows:
        if z["price"] < close:
            z.update({"type": "LIQUIDITÉ EN-DESSOUS", "side": "SELL_STOP_POOL", "distance_atr": (close-z["price"])/atr})
            pools.append(z)

    # Recent session extremes are useful reference pools even when there are no equal highs/lows.
    recent_high = float(df["high"].tail(24).max())
    recent_low = float(df["low"].tail(24).min())
    if recent_high > close and all(abs(recent_high-p["price"]) > tolerance for p in pools):
        pools.append({"price": recent_high, "touches": 1, "low": recent_high, "high": recent_high,
                      "strength": 45.0, "type": "LIQUIDITÉ HAUT RÉCENT", "side": "SELL_STOP_POOL",
                      "distance_atr": (recent_high-close)/atr})
    if recent_low < close and all(abs(recent_low-p["price"]) > tolerance for p in pools):
        pools.append({"price": recent_low, "touches": 1, "low": recent_low, "high": recent_low,
                      "strength": 45.0, "type": "LIQUIDITÉ BAS RÉCENT", "side": "SELL_STOP_POOL",
                      "distance_atr": (close-recent_low)/atr})

    pools.sort(key=lambda x: abs(float(x["price"])-close))
    nearest = pools[0] if pools else None
    bias = "HAUT À SURVEILLER" if nearest and nearest["price"] > close else "BAS À SURVEILLER" if nearest else "INCONNU"
    return {"ok": True, "pools": pools[:12], "nearest": nearest, "tolerance": tolerance,
            "current_price": close, "bias": bias,
            "note": "Carte de liquidité basée sur les extrêmes et concentrations de prix visibles. Elle ne mesure pas les ordres cachés ni un carnet institutionnel complet."}


def liquidity_score(liquidity: Dict[str, Any], direction: str, entry: float, tp: float, sl: float) -> Dict[str, Any]:
    if not liquidity.get("ok") or direction not in {"ACHAT", "VENTE"}:
        return {"score": 0.0, "approved": False, "reason": "Carte de liquidité indisponible."}
    target_side = "BUY_STOP_POOL" if direction == "ACHAT" else "SELL_STOP_POOL"
    candidates = [p for p in liquidity.get("pools", []) if p.get("side") == target_side]
    between = [p for p in candidates if min(entry, tp) <= p["price"] <= max(entry, tp)]
    score = 4.0
    reasons = ["Aucune piscine de liquidité directionnelle forte avant la cible."]
    if candidates:
        nearest = min(candidates, key=lambda p: abs(p["price"]-entry))
        score = 8.0
        reasons = [f"Liquidité {nearest['type'].lower()} détectée à {_fmt_price(nearest['price'])}."]
        if between:
            score = 15.0
            reasons.append("Une zone de liquidité se trouve sur le chemin vers la cible.")
    # Avoid rewarding a target that is beyond the nearest opposing liquidity by too much.
    if candidates and between and between[0]["price"] != tp:
        score = min(score, 12.0)
    return {"score": min(15.0, score), "approved": score >= 8.0, "reason": " ".join(reasons)}


def _fmt_price(x: float) -> str:
    return f"{float(x):.5f}"
