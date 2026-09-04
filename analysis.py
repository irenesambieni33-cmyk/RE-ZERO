"""RE-ZERO multi-timeframe confluence engine. Scores quality; it does not claim guaranteed win probability."""
from __future__ import annotations
from typing import Dict, List
import math, numpy as np, pandas as pd
from config import TIMEFRAME_WEIGHTS
from fibonacci import calculate_fibonacci, confluence
from indicators import add_indicators
from structure import analyze_structure
from support_resistance import detect_zones
from orderflow import buyer_seller_pressure
from regime import detect_regime
from data_quality import audit_ohlcv

INDICATOR_KEYS=["ema20","ema50","sma200","hma20","tema20","dema20","ema_spread_pct","rsi7","rsi14","rsi21","stoch_rsi","macd","macd_signal","macd_hist","ppo","ppo_signal","ppo_hist","atr14","atr_pct","natr14","bb_upper","bb_lower","bb_mid","bb_width","bb_percent","std20_pct","realized_vol20","realized_vol60","adx14","di_plus","di_minus","dx14","aroon_up","aroon_down","aroon_osc","vortex_plus","vortex_minus","vortex_diff","stoch_k","stoch_d","roc12","roc24","mom10","cci20","williams_r","ultimate_osc","trix","fisher10","awesome_osc","dpo20","kst","kc_mid","kc_upper","kc_lower","donchian_high20","donchian_low20","donchian_mid20","donchian_pos","supertrend","supertrend_dir","psar","psar_dir","ichimoku_conversion","ichimoku_base","ichimoku_span_a","ichimoku_span_b","ichimoku_cloud_top","ichimoku_cloud_bottom","ichimoku_bias","cmf20","mfi14","obv","rel_volume20","vwap","volume_z20","eom14","force_index13","bull_power13","bear_power13","return1","log_return","range_pct","body_pct","upper_wick_pct","lower_wick_pct","zscore20","skew20","kurtosis20","drawdown","distance_high20_pct","distance_low20_pct","volatility_ratio"]

def _last(df,key):
    s=df[key].dropna() if key in df else pd.Series(dtype=float)
    return float(s.iloc[-1]) if not s.empty else math.nan

def analyze_timeframe(df:pd.DataFrame,timeframe:str)->Dict:
    base={"timeframe":timeframe,"available":False,"direction":"NEUTRE","score":0.0,"confidence":0.0,"trend":"RANGE / NEUTRE","structure":"RANGE / NEUTRE","indicators":{},"structure_data":{},"zones":{},"fib":{},"confluence":{},"reasons":[],"score_breakdown":{}}
    if df is None or df.empty:return base
    work=add_indicators(df); structure=analyze_structure(work); work=structure["data"]; zones=detect_zones(work); fib=calculate_fibonacci(work,structure)
    price=_last(work,"close"); ind={k:_last(work,k) for k in INDICATOR_KEYS}; score=0.; possible=0.; reasons=[]; breakdown={}
    def feature(name,value,maximum,reason=""):
        nonlocal score,possible
        if value is None or not math.isfinite(value): return
        score+=value; possible+=maximum; breakdown[name]=round(value/maximum*100,1) if maximum else 0
        if reason and abs(value)>0.01: reasons.append(reason)
    # Independent families, with capped contributions to avoid double counting correlated oscillators.
    ema=1 if ind["ema20"]>ind["ema50"] else -1 if ind["ema20"]<ind["ema50"] else 0 if np.isfinite(ind["ema20"]) and np.isfinite(ind["ema50"]) else None
    feature("Tendance EMA",1.0*ema,1.0,"EMA20 > EMA50" if ema==1 else "EMA20 < EMA50" if ema==-1 else "")
    if np.isfinite(ind["sma200"]): feature("Tendance SMA",1 if price>ind["sma200"] else -1,1,"Prix au-dessus de SMA200" if price>ind["sma200"] else "Prix sous SMA200")
    if np.isfinite(ind["adx14"]) and np.isfinite(ind["di_plus"]) and np.isfinite(ind["di_minus"]):
        ds=(1 if ind["di_plus"]>ind["di_minus"] else -1 if ind["di_minus"]>ind["di_plus"] else 0) if ind["adx14"]>=20 else 0
        feature("Force ADX",ds,1,"ADX/DI acheteurs" if ds>0 else "ADX/DI vendeurs" if ds<0 else "ADX faible")
    feature("Supertrend",ind["supertrend_dir"] if np.isfinite(ind["supertrend_dir"]) else None,1,"Supertrend haussier" if ind["supertrend_dir"]>0 else "Supertrend baissier" if ind["supertrend_dir"]<0 else "")
    feature("Ichimoku",ind["ichimoku_bias"] if np.isfinite(ind["ichimoku_bias"]) else None,1,"Prix au-dessus du nuage Ichimoku" if ind["ichimoku_bias"]>0 else "Prix sous le nuage Ichimoku" if ind["ichimoku_bias"]<0 else "")
    if np.isfinite(ind["aroon_osc"]): feature("Aroon",1 if ind["aroon_osc"]>10 else -1 if ind["aroon_osc"]<-10 else 0,0.75,"Aroon haussier" if ind["aroon_osc"]>10 else "Aroon baissier" if ind["aroon_osc"]<-10 else "Aroon neutre")
    if np.isfinite(ind["vortex_diff"]): feature("Vortex",1 if ind["vortex_diff"]>0.05 else -1 if ind["vortex_diff"]<-0.05 else 0,0.75,"Vortex haussier" if ind["vortex_diff"]>0.05 else "Vortex baissier" if ind["vortex_diff"]<-0.05 else "Vortex neutre")
    # Momentum ensemble: one bounded family score, not five independent votes.
    mom=[]
    if np.isfinite(ind["rsi14"]): mom.append(1 if 52<=ind["rsi14"]<=68 else -1 if 32<=ind["rsi14"]<=48 else 0)
    if np.isfinite(ind["macd_hist"]): mom.append(1 if ind["macd_hist"]>0 else -1 if ind["macd_hist"]<0 else 0)
    if np.isfinite(ind["stoch_k"]) and np.isfinite(ind["stoch_d"]): mom.append(1 if ind["stoch_k"]>ind["stoch_d"] else -1 if ind["stoch_k"]<ind["stoch_d"] else 0)
    if np.isfinite(ind["roc12"]): mom.append(1 if ind["roc12"]>0 else -1 if ind["roc12"]<0 else 0)
    if np.isfinite(ind["cci20"]): mom.append(1 if ind["cci20"]>50 else -1 if ind["cci20"]<-50 else 0)
    if np.isfinite(ind["ppo_hist"]): mom.append(1 if ind["ppo_hist"]>0 else -1 if ind["ppo_hist"]<0 else 0)
    if np.isfinite(ind["ultimate_osc"]): mom.append(1 if ind["ultimate_osc"]>50 else -1 if ind["ultimate_osc"]<50 else 0)
    if np.isfinite(ind["trix"]): mom.append(1 if ind["trix"]>0 else -1 if ind["trix"]<0 else 0)
    if np.isfinite(ind["fisher10"]): mom.append(1 if ind["fisher10"]>0 else -1 if ind["fisher10"]<0 else 0)
    if mom: feature("Momentum",float(np.mean(mom)),1,"Momentum global haussier" if np.mean(mom)>.2 else "Momentum global baissier" if np.mean(mom)<-.2 else "Momentum mitigé")
    # Volatility is a quality filter rather than directional vote.
    vol_score=0
    if np.isfinite(ind["volatility_ratio"]): vol_score=1 if 0.75<=ind["volatility_ratio"]<=1.8 else -0.25
    if np.isfinite(ind["bb_width"]) and np.isfinite(ind["atr_pct"]): feature("Volatilité",vol_score,1,"Régime de volatilité exploitable" if vol_score>0 else "Volatilité extrême ou trop faible")
    # Volume/flow family, deliberately low weight for FX tick volume.
    flow=[]
    if np.isfinite(ind["cmf20"]): flow.append(1 if ind["cmf20"]>0 else -1 if ind["cmf20"]<0 else 0)
    if np.isfinite(ind["mfi14"]): flow.append(1 if ind["mfi14"]>50 else -1 if ind["mfi14"]<50 else 0)
    if np.isfinite(ind["obv"]):
        obv_delta=work["obv"].diff(5).dropna()
        if not obv_delta.empty: flow.append(1 if obv_delta.iloc[-1]>0 else -1 if obv_delta.iloc[-1]<0 else 0)
    if flow: feature("Flux/Volume",0.5*float(np.mean(flow)),0.5,"Flux favorables aux acheteurs" if np.mean(flow)>.2 else "Flux favorables aux vendeurs" if np.mean(flow)<-.2 else "Flux mitigés")
    trend=structure["trend"]; feature("Structure",1.5 if trend=="HAUSSIÈRE" else -1.5 if trend=="BAISSIÈRE" else 0,1.5,"Structure haussière" if trend=="HAUSSIÈRE" else "Structure baissière" if trend=="BAISSIÈRE" else "")
    recent_bos=structure.get("bos",[])[-1:]+structure.get("choch",[])[-1:]
    if any("HAUSSIER" in x for x in recent_bos): feature("BOS/CHoCH",1,1,"BOS/CHoCH haussier récent")
    elif any("BAISSIER" in x for x in recent_bos): feature("BOS/CHoCH",-1,1,"BOS/CHoCH baissier récent")
    else: feature("BOS/CHoCH",0,1)
    conf=confluence(fib,zones,price,ind["atr14"])
    if conf["bull"]>conf["bear"]: feature("Zones/Fibonacci",1,1,"Confluence support/Fibonacci haussière")
    elif conf["bear"]>conf["bull"]: feature("Zones/Fibonacci",-1,1,"Confluence résistance/Fibonacci baissière")
    else: feature("Zones/Fibonacci",0,1)
    # Price vs VWAP/Keltner as a contextual check.
    ctx=[]
    if np.isfinite(ind["vwap"]): ctx.append(1 if price>ind["vwap"] else -1)
    if np.isfinite(ind["kc_upper"]) and np.isfinite(ind["kc_lower"]): ctx.append(1 if price>ind["kc_mid"] else -1)
    if ctx: feature("Contexte prix",0.5*float(np.mean(ctx)),0.5,"Prix dans un contexte haussier" if np.mean(ctx)>.2 else "Prix dans un contexte baissier" if np.mean(ctx)<-.2 else "")
    if np.isfinite(ind["donchian_pos"]):
        dp=ind["donchian_pos"]; feature("Breakout Donchian",0.75 if dp>=0.80 else -0.75 if dp<=0.20 else 0,0.75,"Prix proche du haut du canal Donchian" if dp>=0.80 else "Prix proche du bas du canal Donchian" if dp<=0.20 else "")
    if np.isfinite(ind["zscore20"]):
        zs=ind["zscore20"]; feature("Z-Score",0.5 if 0<zs<2.5 else -0.5 if -2.5<zs<0 else 0,0.5,"Z-score positif" if 0<zs<2.5 else "Z-score négatif" if -2.5<zs<0 else "")
    if np.isfinite(ind["volume_z20"]): feature("Anomalie volume",0.25 if ind["volume_z20"]>1 else 0,0.25,"Volume nettement supérieur à sa moyenne" if ind["volume_z20"]>1 else "")
    normalized=100*score/possible if possible else 0
    direction="ACHAT" if normalized>=25 else "VENTE" if normalized<=-25 else "NEUTRE"
    completeness=min(1.,possible/16.0); confidence=min(100.,abs(normalized)*completeness)
    flow=buyer_seller_pressure(work)
    regime=detect_regime(work)
    quality=audit_ohlcv(work,timeframe)
    return {"timeframe":timeframe,"available":True,"data":work,"price":price,"direction":direction,"score":normalized,"confidence":confidence,"trend":trend,"structure":trend,"indicators":ind,"structure_data":structure,"zones":zones,"fib":fib,"confluence":conf,"reasons":reasons,"score_breakdown":breakdown,"orderflow":flow,"regime":regime,"data_quality":quality}

def _same_direction(results,tfs,direction):
    usable=[results.get(tf,{}) for tf in tfs if results.get(tf,{}).get("available")]
    return len(usable)>=2 and all(r.get("direction")==direction for r in usable)

def analyze_multi_timeframe(frames:Dict[str,pd.DataFrame])->Dict:
    results={}
    for tf in TIMEFRAME_WEIGHTS:
        try: results[tf]=analyze_timeframe(frames.get(tf,pd.DataFrame()),tf)
        except Exception as exc: results[tf]={"timeframe":tf,"available":False,"direction":"NEUTRE","score":0.,"confidence":0.,"trend":"RANGE / NEUTRE","structure":"RANGE / NEUTRE","error":str(exc)}
    usable=[r for r in results.values() if r.get("available")]; total_w=sum(TIMEFRAME_WEIGHTS[tf] for tf in results if results[tf].get("available")); global_score=sum(results[tf]["score"]*TIMEFRAME_WEIGHTS[tf] for tf in results if results[tf].get("available"))/total_w if total_w else 0.
    major_bull=_same_direction(results,["D1","H4","H1"],"ACHAT"); major_bear=_same_direction(results,["D1","H4","H1"],"VENTE")
    m15,m5=results.get("M15",{}),results.get("M5",{}); lower_complete=bool(m15.get("available") and m5.get("available")); lower_bull=lower_complete and m15.get("direction")==m5.get("direction")=="ACHAT"; lower_bear=lower_complete and m15.get("direction")==m5.get("direction")=="VENTE"
    if major_bull and lower_bull and global_score>=40: decision="ACHAT"
    elif major_bear and lower_bear and global_score<=-40: decision="VENTE"
    elif abs(global_score)>=20: decision="ATTENDRE"
    else: decision="AUCUN SETUP"
    available=sum(bool(r.get("available")) for r in results.values()); alignment=sum(1 for tf in ["D1","H4","H1"] if results.get(tf,{}).get("available") and results[tf].get("direction") in {"ACHAT","VENTE"}); confirmation=sum(1 for tf in ["M15","M5"] if results.get(tf,{}).get("available") and results[tf].get("direction") in {"ACHAT","VENTE"})
    avg_conf=float(np.mean([r.get("confidence",0) for r in usable])) if usable else 0
    directional_alignment=(alignment/3)*20+(confirmation/2)*15; data_factor=available/5
    confidence=min(100.,abs(global_score)*0.55+directional_alignment+avg_conf*0.25)*(0.65+0.35*data_factor)
    if decision=="ATTENDRE": confidence=min(confidence,70.)
    if decision=="AUCUN SETUP": confidence=min(confidence,50.)
    if decision in {"ACHAT","VENTE"} and not lower_complete: decision="ATTENDRE"; confidence=min(confidence,65.)
    lines=[f"{tf} {results[tf].get('direction','NEUTRE').lower() if results[tf].get('available') else 'indisponible'}" for tf in ["D1","H4","H1","M15","M5"]]
    if decision in {"ACHAT","VENTE"}: explanation=f"{', '.join(lines)}. Alignement multi-timeframe favorable et confluence suffisante pour un setup candidat. Le score est une mesure de qualité, pas une probabilité garantie de gain."
    elif decision=="ATTENDRE": explanation=f"{', '.join(lines)}. Un biais existe mais la confirmation/confluence est insuffisante. Le moteur refuse de forcer un trade."
    else: explanation=f"{', '.join(lines)}. Les conditions ne forment pas une configuration suffisamment convergente. Aucun setup n'est forcé."
    return {"timeframes":results,"score":global_score,"confidence":confidence,"decision":decision,"explanation":explanation,"available_count":available}
