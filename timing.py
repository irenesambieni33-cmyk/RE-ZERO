"""Market timing and volatility-window engine.
No broker calls. Times are configurable local-time defaults, not guarantees of profitability.
"""
from __future__ import annotations
from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Dict, Any
import math

LOCAL_TZ = "Africa/Porto-Novo"
DEFAULT_WINDOWS = {
    "Londres": ("08:00", "11:00"),
    "Ouverture New York": ("14:00", "17:00"),
    "Chevauchement Londres/NY": ("14:00", "16:00"),
    "BTC US": ("14:00", "18:00"),
}

def _parse_hhmm(value: str) -> time:
    h, m = [int(x) for x in value.split(":")]
    return time(h, m)

def in_window(now: datetime, start: str, end: str) -> bool:
    t = now.time()
    a, b = _parse_hhmm(start), _parse_hhmm(end)
    return a <= t < b if a <= b else (t >= a or t < b)

def current_windows(now: datetime | None = None) -> list[str]:
    now = now or datetime.now(ZoneInfo(LOCAL_TZ))
    return [name for name, (start, end) in DEFAULT_WINDOWS.items() if in_window(now, start, end)]

def volatility_profile(m15_df) -> Dict[str, Any]:
    """Estimate current volatility regime from recent M15 OHLCV data."""
    if m15_df is None or len(m15_df) < 40:
        return {"ok": False, "score": 0.0, "ratio": math.nan, "percentile": math.nan, "regime": "DONNÉES INSUFFISANTES"}
    df = m15_df.copy()
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    ret = close.pct_change().abs()
    recent = ret.rolling(4).mean().iloc[-1]
    baseline = ret.rolling(40).mean().iloc[-1]
    ratio = float(recent / baseline) if baseline and math.isfinite(float(baseline)) else math.nan
    history = ret.rolling(4).mean().dropna()
    percentile = float((history <= recent).mean() * 100) if not history.empty and math.isfinite(float(recent)) else math.nan
    atr_like = ((high - low) / close.replace(0, math.nan)).rolling(4).mean().iloc[-1]
    volume_z = math.nan
    if "volume" in df:
        vol = df["volume"].astype(float)
        mean = vol.rolling(20).mean().iloc[-1]
        std = vol.rolling(20).std().iloc[-1]
        if std and math.isfinite(float(std)):
            volume_z = float((vol.iloc[-1] - mean) / std)
    if not math.isfinite(ratio):
        regime = "INCONNU"; score = 0.0
    elif ratio < 0.65:
        regime = "FAIBLE"; score = 25.0
    elif ratio <= 1.25:
        regime = "NORMALE"; score = 65.0
    elif ratio <= 2.0:
        regime = "EXPANSION"; score = 90.0
    elif ratio <= 2.6:
        regime = "FORTE"; score = 70.0
    else:
        regime = "EXTRÊME"; score = 20.0
    return {"ok": True, "score": score, "ratio": ratio, "percentile": percentile, "atr_like_pct": float(atr_like * 100) if math.isfinite(float(atr_like)) else math.nan, "volume_z": volume_z, "regime": regime}

def timing_assessment(instrument: str, m15_result: Dict[str, Any], m15_df, now: datetime | None = None, custom_window: tuple[str, str] | None = None) -> Dict[str, Any]:
    now = now or datetime.now(ZoneInfo(LOCAL_TZ))
    windows = current_windows(now)
    if custom_window:
        cstart, cend = custom_window
        if in_window(now, cstart, cend):
            windows.append(f"Fenêtre personnalisée {cstart}-{cend}")
        else:
            windows = [w for w in windows if not w.startswith("Fenêtre personnalisée")]
    profile = volatility_profile(m15_df)
    ind = m15_result.get("indicators", {}) if m15_result else {}
    adx = float(ind.get("adx14")) if ind.get("adx14") is not None and math.isfinite(float(ind.get("adx14"))) else math.nan
    ratio = profile.get("ratio", math.nan)
    session_score = 90.0 if windows else 35.0
    trend_score = 80.0 if math.isfinite(adx) and adx >= 20 else 55.0 if math.isfinite(adx) and adx >= 15 else 25.0
    vol_score = float(profile.get("score", 0.0))
    total = round(0.45 * vol_score + 0.30 * session_score + 0.25 * trend_score, 1)
    if not profile.get("ok"):
        status = "ATTENTE"
    elif profile.get("regime") == "EXTRÊME":
        status = "RISQUE ÉLEVÉ"
    elif total >= 72:
        status = "FENÊTRE FAVORABLE"
    elif total >= 55:
        status = "SURVEILLER"
    else:
        status = "ATTENTE"
    return {"local_time": now.strftime("%H:%M:%S"), "timezone": "Bénin (UTC+1)", "windows": windows, "profile": profile, "adx": adx, "score": total, "status": status,
            "note": "Le moteur privilégie les phases de volatilité exploitable et évite les régimes trop faibles ou extrêmes. Les horaires sont des fenêtres de surveillance, pas des heures magiques."}
