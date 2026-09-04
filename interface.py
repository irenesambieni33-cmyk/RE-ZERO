"""Streamlit presentation layer and professional Plotly dashboard."""
from __future__ import annotations
from typing import Dict, Optional
import math
import plotly.graph_objects as go
import streamlit as st
from config import APP_NAME, APP_SUBTITLE, TIMEFRAMES
from risk import build_setup, build_step_up, risk_summary
from security import validate_setup
from setup_quality import evaluate_setup_quality
from safety import safety_gate
from timing import timing_assessment
from alerts import build_alert, send_telegram
from performance import backtest_trade_plans
from liquidity import build_liquidity_map
from trade_manager import TradeManager
from macro_context import fetch_macro_events, macro_assessment
from browser_notifications import notify_opportunity
from decision_engine import decide

def _fmt(v, digits=5):
    if v is None: return "—"
    try:
        if not math.isfinite(float(v)): return "—"
        return f"{float(v):,.{digits}f}"
    except (TypeError, ValueError): return "—"

def decision_badge(d):
    return {"ACHAT":"🟢 ACHAT","VENTE":"🔴 VENTE","ATTENDRE":"🟠 ATTENDRE","AUCUN SETUP":"⚪ AUCUN SETUP"}.get(d,d)

def decision_card(d):
    styles={"ACHAT":("#198754","rgba(25,135,84,.12)"),"VENTE":("#dc3545","rgba(220,53,69,.12)"),"ATTENDRE":("#fd7e14","rgba(253,126,20,.12)"),"AUCUN SETUP":("#6c757d","rgba(108,117,125,.12)")}
    color,bg=styles.get(d,("#6c757d","rgba(108,117,125,.12)"))
    st.markdown(f'''<div class="decision-card" style="border-color:{color};background:{bg}"><div class="decision-label">DÉCISION DU MOTEUR</div><div class="decision-value" style="color:{color}">{decision_badge(d)}</div><div class="decision-note">Trade préparé sur <b>M15</b> avec contexte D1/H4, confirmation H1 et validation M5.</div></div>''',unsafe_allow_html=True)

def apply_css():
    st.markdown("""<style>
    .block-container{max-width:1450px;padding-top:1rem;padding-bottom:3rem}.hero{padding:1.2rem 1.4rem;border:1px solid rgba(128,128,128,.22);border-radius:18px;margin-bottom:1rem}.muted{opacity:.72;font-size:.9rem}
    .decision-card{border:2px solid;border-radius:18px;padding:1.2rem 1.4rem;margin:.6rem 0 1.2rem;text-align:center}.decision-label{font-size:.82rem;letter-spacing:.12em;opacity:.7;font-weight:700}.decision-value{font-size:2rem;font-weight:900;margin:.3rem 0}.decision-note{font-size:.92rem;opacity:.78}
    </style>""",unsafe_allow_html=True)

def render_chart(tf_result: Dict, liquidity=None):
    """Render a highly legible trading chart with thick overlays and readable candles."""
    df = tf_result.get("data")
    if df is None or df.empty:
        st.info("Pas assez de données pour afficher le graphique.")
        return

    plot_df = df.tail(180).copy()
    fig = go.Figure()

    # Candles: larger body/wick contrast and no rangeslider clutter.
    fig.add_trace(go.Candlestick(
        x=plot_df.index,
        open=plot_df["open"], high=plot_df["high"],
        low=plot_df["low"], close=plot_df["close"],
        name="Bougies",
        increasing_line_width=1.5,
        decreasing_line_width=1.5,
    ))

    # Main trend lines: deliberately thicker for mobile readability.
    for col, name, width in [
        ("ema20", "EMA 20", 3.0),
        ("ema50", "EMA 50", 3.0),
        ("sma200", "SMA 200", 3.5),
    ]:
        if col in plot_df:
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df[col], mode="lines", name=name,
                line=dict(width=width), connectgaps=False,
            ))

    for col, name in [("bb_upper", "BB haute"), ("bb_lower", "BB basse")]:
        if col in plot_df:
            fig.add_trace(go.Scatter(
                x=plot_df.index, y=plot_df[col], mode="lines", name=name,
                line=dict(width=2, dash="dot"), connectgaps=False,
            ))

    zones = tf_result.get("zones", {})
    liquidity = liquidity or {}
    # Limit annotations to the nearest/most relevant levels so the chart stays readable.
    for z in zones.get("supports", [])[:3]:
        fig.add_hline(y=z["price"], line_dash="dot", line_width=2,
                      annotation_text=f"Support {_fmt(z['price'])}",
                      annotation_position="bottom right")
    for z in zones.get("resistances", [])[:3]:
        fig.add_hline(y=z["price"], line_dash="dot", line_width=2,
                      annotation_text=f"Résistance {_fmt(z['price'])}",
                      annotation_position="top right")

    fib_levels = tf_result.get("fib", {}).get("levels", {})
    for label, value in list(fib_levels.items())[:6]:
        fig.add_hline(y=value, line_dash="dash", line_width=1.5,
                      annotation_text=f"Fib {label}", annotation_position="left")

    for pool in liquidity.get("pools", [])[:5]:
        ptype = pool.get("type", "Liquidité")
        fig.add_hline(y=pool["price"], line_dash="dot", line_width=2,
                      annotation_text=f"Liquidité {ptype} {_fmt(pool['price'])}",
                      annotation_position="top left")

    sd = tf_result.get("structure_data", {}).get("data")
    if sd is not None and not sd.empty:
        sd = sd.loc[sd.index.isin(plot_df.index)]
        sh = sd[sd["swing_high"]]
        sl = sd[sd["swing_low"]]
        if not sh.empty:
            fig.add_trace(go.Scatter(
                x=sh.index, y=sh.high, mode="markers+text", text=sh.swing_label,
                name="Swing High", textposition="top center",
                marker=dict(size=10), textfont=dict(size=12),
            ))
        if not sl.empty:
            fig.add_trace(go.Scatter(
                x=sl.index, y=sl.low, mode="markers+text", text=sl.swing_label,
                name="Swing Low", textposition="bottom center",
                marker=dict(size=10), textfont=dict(size=12),
            ))
        for col in ["bos", "choch"]:
            if col in sd:
                ev = sd[sd[col] != ""]
                if not ev.empty:
                    fig.add_trace(go.Scatter(
                        x=ev.index, y=ev.close, mode="markers+text", text=ev[col],
                        name=col.upper(), textposition="top center",
                        marker=dict(size=11), textfont=dict(size=12),
                    ))

    fig.update_layout(
        height=720,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        margin=dict(l=25, r=25, t=55, b=25),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
                    font=dict(size=12)),
        xaxis=dict(showgrid=True, tickfont=dict(size=12), title="Temps"),
        yaxis=dict(showgrid=True, tickfont=dict(size=12), title="Prix", fixedrange=False),
        hoverlabel=dict(font_size=13),
    )
    st.plotly_chart(fig, use_container_width=True, config={
        "responsive": True, "displaylogo": False, "scrollZoom": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    })

def render_dashboard(instrument: str, price: float, result: Dict, capital: float, crypto_snapshot=None, monitor: bool = False, custom_window=None, trade_manager: TradeManager | None = None, macro_events=None):
    st.markdown(f'<div class="hero"><h1>{APP_NAME}</h1><div class="muted">{APP_SUBTITLE}</div></div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4); c1.metric("Instrument",instrument); c2.metric("Prix actuel",_fmt(price)); c3.metric("Score",f'{result["score"]:+.1f}'); c4.metric("Qualité du scénario",f'{result["confidence"]:.0f}/100')
    if crypto_snapshot and crypto_snapshot.get("ok"):
        st.subheader("₿ MICROSTRUCTURE BTC")
        a,b,c,d,e=st.columns(5); a.metric("Variation 24h",f'{crypto_snapshot["change_pct"]:+.2f}%'); b.metric("High 24h",_fmt(crypto_snapshot["high_24h"])); c.metric("Low 24h",_fmt(crypto_snapshot["low_24h"])); d.metric("Volume BTC",f'{crypto_snapshot["volume_btc"]:,.0f}'); e.metric("Order-book imbalance",f'{crypto_snapshot["orderbook_imbalance"]:+.2%}')
        st.caption("Snapshot public BTC/USDT. Il sert de filtre de contexte, pas de promesse de liquidité ou de prix d'exécution.")
    elif instrument == "BTC/USD":
        st.info("Le snapshot microstructure BTC est indisponible. L'analyse principale continue avec les données de marché disponibles.")
    macro_events = macro_events or {"events": []}
    macro = macro_assessment(instrument, macro_events)
    st.subheader("🌍 CONTEXTE MACRO & ANNONCES")
    ma,mb,mc=st.columns(3)
    ma.metric("Risque macro", macro.get("risk","NORMAL"))
    nearest=macro.get("nearest") or {}
    mb.metric("Prochaine annonce", nearest.get("title","Aucune"))
    mins=macro.get("minutes_to_event")
    mc.metric("Échéance", f"{mins:.0f} min" if mins is not None else "—")
    for rr in macro.get("reasons",[]): st.caption("• "+rr)
    st.caption(macro.get("note",""))
    st.subheader("ANALYSE MULTI-TIMEFRAME"); st.caption("Trade préparé en M15 : D1/H4 = contexte, H1 = confirmation, M5 = validation de l'entrée. Le moteur combine tendance, structure, liquidité, pression acheteurs/vendeurs et risque macro.")
    cols=st.columns(len(TIMEFRAMES))
    for col,tf in zip(cols,TIMEFRAMES):
        r=result["timeframes"].get(tf,{})
        with col:
            st.markdown(f"**{tf}**")
            if not r.get("available"): st.warning("Indisponible"); continue
            st.write(f"Direction : **{r['direction']}**"); st.write(f"Score : **{r['score']:+.1f}**"); st.write(f"Qualité : **{r['confidence']:.0f}/100**"); st.write(f"Tendance : **{r['trend']}**")
            sd=r.get("structure_data",{}); st.caption(f"Structure : {r['structure']} • HH {sd.get('hh',0)} • HL {sd.get('hl',0)} • LH {sd.get('lh',0)} • LL {sd.get('ll',0)}")
            ind=r.get("indicators",{}); st.caption(f"RSI {_fmt(ind.get('rsi14'),1)} • ADX {_fmt(ind.get('adx14'),1)} • MACD {_fmt(ind.get('macd_hist'),5)} • CCI {_fmt(ind.get('cci20'),1)} • MFI {_fmt(ind.get('mfi14'),1)}")
    st.subheader("⚖️ PRESSION ACHETEURS / VENDEURS")
    flow=m15=result.get("timeframes",{}).get("M15",{}).get("orderflow",{}) or {}
    if flow.get("ok"):
        fa,fb,fc=st.columns(3); fa.metric("Acheteurs",f"{flow.get('buyers',0):.1f}%"); fb.metric("Vendeurs",f"{flow.get('sellers',0):.1f}%"); fc.metric("Biais",flow.get("bias","ÉQUILIBRE"))
        st.progress(int(max(0,min(100,flow.get("buyers",50)))))
        st.caption(flow.get("note",""))
    with st.expander("🧠 Détail de la qualité RE-ZERO", expanded=False):
        st.caption("Les familles sont volontairement pondérées pour limiter le double comptage d'indicateurs corrélés.")
        for tf in TIMEFRAMES:
            r=result["timeframes"].get(tf,{})
            if r.get("available"):
                st.write(f"**{tf}** — score {r.get("score",0):+.1f} / qualité {r.get("confidence",0):.0f}/100")
                st.json(r.get("score_breakdown",{}), expanded=False)
    trade_manager = trade_manager or TradeManager()
    m15=result["timeframes"].get("M15",{}); setup=None; setup_source="M15"
    liquidity = build_liquidity_map(m15.get("data") if m15.get("available") else None, m15.get("structure_data",{}), m15.get("indicators",{}).get("atr14"))
    # Context used only to describe the health of an active trade; TP2/SL remain the only automatic exit rules.
    m15_pre = result["timeframes"].get("M15", {})
    m15_ind = m15_pre.get("indicators", {}) or {}
    m15_dir = m15_pre.get("direction", "NEUTRE")
    momentum_state = "FAVORABLE" if ((float(m15_ind.get("macd_hist", 0) or 0) > 0 and m15_dir == "ACHAT") or (float(m15_ind.get("macd_hist", 0) or 0) < 0 and m15_dir == "VENTE")) else "DÉFAVORABLE"
    trend_state = m15_pre.get("trend", "INCONNU")
    liquidity_state = liquidity.get("bias", "INCONNU") if liquidity.get("ok") else "INCONNUE"
    volatility_state = (timing_assessment(instrument, m15_pre, m15_pre.get("data") if m15_pre.get("available") else None, custom_window=custom_window).get("status", "INCONNUE"))
    active_update = trade_manager.update(instrument, price, {"momentum": momentum_state, "trend": trend_state, "liquidity": liquidity_state, "volatility": volatility_state})
    active_trade = trade_manager.active
    # The M15 setup must use the latest M15 price, not the latest lower-timeframe price (M5).
    setup_price = m15.get("price") if m15.get("available") else price
    decision_guard = decide(result, rg, dq, macro.get("risk", "NORMAL"))
    st.subheader("🎯 MOTEUR DE DÉCISION")
    da,db,dc=st.columns(3)
    da.metric("Scénario", decision_guard.get("scenario", "NEUTRE"))
    db.metric("Statut", decision_guard.get("status", "REJETÉ"))
    dc.metric("Qualité données", f"{dq.get("score",0):.0f}/100")
    if decision_guard.get("hard_blocks"):
        for reason in decision_guard["hard_blocks"]: st.warning("⛔ "+reason)
    if decision_guard.get("soft_warnings"):
        for reason in decision_guard["soft_warnings"]: st.caption("⚠️ "+reason)
    if active_trade is None and decision_guard.get("status") in {"CANDIDAT","CANDIDAT FORT"} and result["decision"] in {"ACHAT","VENTE"} and m15.get("available") and macro.get("risk") not in {"BLOQUÉ / CHOC MACRO","TRÈS ÉLEVÉ"}:
        setup=build_setup(setup_price,m15.get("indicators",{}).get("atr14"),m15.get("structure_data",{}),result["decision"],m15.get("zones",{}))
        if not setup.get("valid"): setup=None
    st.subheader("GRAPHIQUE")
    available=[tf for tf in TIMEFRAMES if result["timeframes"].get(tf,{}).get("available")]
    if not available: st.error("Aucun timeframe exploitable."); return
    default_index=available.index("M15") if "M15" in available else (available.index("H1") if "H1" in available else 0)
    chart_tf=st.selectbox("Timeframe du graphique",available,index=default_index); render_chart(result["timeframes"][chart_tf], liquidity if chart_tf == "M15" else None)
    st.subheader("💧 CARTE DE LIQUIDITÉ")
    if liquidity.get("ok"):
        lp1,lp2,lp3=st.columns(3)
        lp1.metric("Pools détectés", len(liquidity.get("pools",[])))
        nearest=liquidity.get("nearest") or {}
        lp2.metric("Zone la plus proche", _fmt(nearest.get("price")) if nearest else "—")
        lp3.metric("Biais liquidité", liquidity.get("bias","INCONNU"))
        pools=liquidity.get("pools",[])
        if pools:
            st.dataframe({"Type":[p["type"] for p in pools[:8]],"Prix":[_fmt(p["price"]) for p in pools[:8]],"Touches":[p["touches"] for p in pools[:8]],"Distance ATR":[f'{p["distance_atr"]:.2f}×' for p in pools[:8]],"Force":[f'{p["strength"]:.0f}/100' for p in pools[:8]]},use_container_width=True,hide_index=True)
        st.caption(liquidity.get("note",""))
    else:
        st.info("Carte de liquidité indisponible : données M15 insuffisantes.")

    st.subheader("⏱️ MOTEUR DE TIMING & VOLATILITÉ")
    timing = timing_assessment(instrument, m15, m15.get("data") if m15.get("available") else None, custom_window=custom_window)
    ta,tb,tc,td = st.columns(4)
    ta.metric("Fenêtre", timing.get("status", "ATTENTE"))
    tb.metric("Score timing", f"{timing.get('score',0):.0f}/100")
    profile = timing.get("profile", {})
    tc.metric("Régime volatilité", profile.get("regime", "INCONNU"))
    td.metric("Heure locale", timing.get("local_time", "—"))
    if timing.get("windows"):
        st.caption("Fenêtres actives : " + " • ".join(timing["windows"]) + " • fuseau Bénin (UTC+1).")
    else:
        st.caption("Aucune fenêtre de liquidité configurée n'est active actuellement. Le moteur peut surveiller le marché sans forcer un trade.")
    if profile.get("ok"):
        pa,pb,pc = st.columns(3)
        pa.metric("Volatilité relative", _fmt(profile.get("ratio"), 2) + "×")
        pb.metric("Percentile volatilité", _fmt(profile.get("percentile"), 0) + "%")
        pc.metric("Volume Z", _fmt(profile.get("volume_z"), 2))
    st.caption(timing.get("note", ""))

    st.subheader("🧠 RÉGIME DE MARCHÉ & QUALITÉ DES DONNÉES")
    rg=m15.get("regime",{}) or {}; dq=m15.get("data_quality",{}) or {}
    ra,rb,rc,rd=st.columns(4)
    ra.metric("Régime", rg.get("base","INCONNU"))
    rb.metric("Direction régime", rg.get("direction","—"))
    rc.metric("Volatilité", rg.get("volatility","—"))
    rd.metric("Qualité données", f'{dq.get("score",0):.0f}/100')
    st.caption(rg.get("note", ""))
    if dq.get("issues"):
        st.caption("Audit données : " + " • ".join(dq["issues"][:4]))

    st.subheader("🔒 POSITION EN COURS")
    if active_trade is not None:
        t=active_trade
        sign=1 if t.direction=="ACHAT" else -1
        risk_dist=abs(t.entry-t.sl)
        r_now=sign*(float(t.current_price)-t.entry)/risk_dist if risk_dist else 0.0
        p1,p2,p3,p4,p5=st.columns(5)
        p1.metric("Position", f'{t.direction} {t.symbol}')
        p2.metric("Prix actuel", _fmt(t.current_price))
        p3.metric("R actuel", f'{r_now:+.2f}R')
        p4.metric("TP2", _fmt(t.tp2))
        p5.metric("SL", _fmt(t.sl))
        st.success("🔒 TRADE ACTIF : RE-ZERO suit cette position jusqu'à TP2 ou SL. Aucun nouveau trade ne sera proposé avant la clôture.")
        st.caption(f'Qualité à l’entrée : {t.grade} ({t.quality_score:.0f}/100) • MFE {t.max_favorable_r:+.2f}R • MAE {t.max_adverse_r:+.2f}R')
        if active_update.get("event")=="SUIVI":
            st.info("Le scénario est en suivi. Le moteur observe structure, tendance, volatilité, momentum et liquidité sans ouvrir une nouvelle position.")
            st.metric("État du scénario", getattr(t, "last_health", "EN SUIVI"))
            if getattr(t, "last_health_note", ""):
                st.caption(t.last_health_note)
        if t.liquidity_note: st.caption("💧 " + t.liquidity_note)
    else:
        st.info("Aucune position active. Le moteur peut chercher une nouvelle opportunité validée.")

    st.subheader("🎯 PLAN DE TRADE M15")
    if setup:
        a,b,c,d,e=st.columns(5); a.metric("ENTRY",_fmt(setup["entry"])); b.metric("STOP LOSS",_fmt(setup["sl"])); c.metric("TAKE PROFIT 1",_fmt(setup["tp1"])); d.metric("TAKE PROFIT 2",_fmt(setup["tp2"])); e.metric("R:R",f"1:{setup['rr1']:.1f} / 1:{setup['rr2']:.1f}")
        st.caption(f"Setup source : **{setup_source}** • Multi-marché • R:R minimum : 1:2 • Aucun ordre automatique.")
    else: st.info("Aucun plan M15 valide : Entry, Stop Loss et Take Profits ne sont affichés que lorsqu'un setup respecte les conditions minimales.")
    st.subheader("📈 STEP-UP / GESTION DE POSITION")
    if setup:
        for step in build_step_up(setup)["steps"]:
            st.markdown(f"**{step['name']} — {step['trigger_text']} : {_fmt(step['trigger'])}**"); st.write(f"SL de référence : **{_fmt(step['sl'])}** • {step['action']}")
        st.caption("Les STEP-UP sont théoriques : aucun déplacement de SL ni ordre broker n'est exécuté automatiquement.")
    else: st.info("Les STEP-UP apparaîtront avec un setup M15 valide.")
    decision_card(result["decision"])
    st.subheader("STRUCTURE DU MARCHÉ")
    chart_result=result["timeframes"][chart_tf]; sd=chart_result.get("structure_data",{}); a,b,c,d=st.columns(4); a.metric("HH",sd.get("hh",0)); b.metric("HL",sd.get("hl",0)); c.metric("LH",sd.get("lh",0)); d.metric("LL",sd.get("ll",0)); st.write("**BOS :**",", ".join(sd.get("bos",[])) or "Aucun récent"); st.write("**CHoCH :**",", ".join(sd.get("choch",[])) or "Aucun récent")
    st.subheader("SUPPORT / RÉSISTANCE")
    z=chart_result.get("zones",{}); st.dataframe({"Support":[_fmt(x["price"]) for x in z.get("supports",[])],"Touches support":[x["touches"] for x in z.get("supports",[])],"Résistance":[_fmt(x["price"]) for x in z.get("resistances",[])],"Touches résistance":[x["touches"] for x in z.get("resistances",[])]},use_container_width=True,hide_index=True)
    st.subheader("FIBONACCI"); fib=chart_result.get("fib",{})
    if fib.get("levels"): st.dataframe({"Niveau":list(fib["levels"].keys()),"Prix":[_fmt(v) for v in fib["levels"].values()]},use_container_width=True,hide_index=True); st.write("Niveau le plus proche :",fib.get("nearest"))
    else: st.info("Pas assez de swings significatifs pour calculer Fibonacci.")
    st.subheader("🧠 QUALITÉ DU SETUP RE-ZERO")
    quality = evaluate_setup_quality(result, setup, liquidity)
    qa, qb, qc = st.columns(3)
    qa.metric("Score qualité", f"{quality.get('score', 0):.0f}/100")
    qb.metric("Classe", quality.get("grade", "REJETÉ"))
    qc.metric("Autorisation", "OUI" if quality.get("approved") else "NON")
    if quality.get("families"):
        st.dataframe({"Famille": list(quality["families"].keys()), "Score": list(quality["families"].values())}, use_container_width=True, hide_index=True)
    for reason in quality.get("reasons", []): st.caption("• " + reason)
    st.caption(quality.get("note", ""))

    st.subheader("🛡️ SAFETY GATE")
    open_risk_fraction = 0.0
    if active_trade is not None and capital > 0:
        open_risk_fraction = min(1.0, abs(active_trade.entry-active_trade.sl)*active_trade.units/capital)
    gate = safety_gate(setup if active_trade is None else None, quality if active_trade is None else {"approved":False}, capital, open_risk_fraction=open_risk_fraction)
    st.write("**Statut :**", "🟢 VALIDÉ" if gate["approved"] else "🔴 BLOQUÉ")
    failed = [k for k,v in gate["checks"].items() if not v]
    if failed: st.caption("Blocages : " + ", ".join(failed))
    else: st.caption("Toutes les barrières critiques sont satisfaites. Aucun ordre broker n'est envoyé par cette version.")
    alert = build_alert(instrument, result, quality, gate, timing, setup) if active_trade is None else {"active":False,"message":"Trade déjà actif : aucune nouvelle alerte d’entrée."}
    notify_key = f"{instrument}|{alert.get('direction')}|{alert.get('quality')}|{(alert.get('setup') or {}).get('entry')}|{(alert.get('setup') or {}).get('sl')}|{(alert.get('setup') or {}).get('tp2')}"
    notify_opportunity(alert, notify_key)
    st.subheader("🚨 DÉTECTION D'OPPORTUNITÉ")
    if alert["active"]:
        st.success(alert["message"])
        if monitor:
            last_key = st.session_state.get("last_alert_key")
            alert_key = f"{instrument}:{result.get('decision')}:{round(quality.get('score',0))}:{setup.get('entry') if setup else 0}"
            if last_key != alert_key:
                st.toast(alert["message"], icon="🚨")
                st.session_state["last_alert_key"] = alert_key
                try:
                    token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
                    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
                    if token and chat_id:
                        send_telegram(alert, token, chat_id)
                except Exception:
                    pass
        st.caption("Le moteur a simultanément validé direction, qualité, sécurité et fenêtre de volatilité. Ceci reste une alerte d'analyse, pas une garantie de gain.")
    else:
        st.info("Aucune opportunité suffisamment filtrée maintenant. Le moteur préfère attendre plutôt que d'inventer un trade pour faire joli.")
    if active_trade is None and setup and quality.get("approved") and gate.get("approved") and alert.get("active"):
        rs_action=risk_summary(capital,setup["entry"],setup["sl"])
        st.subheader("🎯 TU AS PLACÉ LE TRADE ?")
        st.warning("Après avoir placé le trade selon ce plan, appuie ici. RE-ZERO verrouillera le suivi de cette position en PAPER. Aucun ordre broker réel n’est envoyé.")
        if st.button("🔒 J'AI PLACÉ CE TRADE — DÉMARRER LE SUIVI", type="primary", use_container_width=True):
            opened=trade_manager.open(instrument, setup, rs_action["units"], quality, liquidity_note=(liquidity.get("nearest") or {}).get("type", ""))
            if opened.get("ok"):
                st.toast("Trade PAPER pris. Suivi verrouillé jusqu’à TP2 ou SL.", icon="🔒")
                st.rerun()
            else:
                st.error(opened.get("reason","Impossible d’ouvrir la position."))

    st.subheader("📊 PERFORMANCE")
    perf=trade_manager.snapshot().get("performance",{})
    pc1,pc2,pc3,pc4=st.columns(4)
    pc1.metric("Trades clôturés", perf.get("trades",0))
    pc2.metric("Win Rate", f'{perf.get("win_rate",0):.1f}%')
    pc3.metric("Net P&L", f'{perf.get("net_pnl",0):+.2f}')
    pf=perf.get("profit_factor",0)
    pc4.metric("Profit Factor", "∞" if pf==float("inf") else f'{pf:.2f}')
    if trade_manager.history:
        st.dataframe({"Instrument":[t.symbol for t in trade_manager.history],"Sens":[t.direction for t in trade_manager.history],"Entrée":[_fmt(t.entry) for t in trade_manager.history],"Sortie":[_fmt(t.exit_price) for t in trade_manager.history],"Résultat":[t.exit_reason for t in trade_manager.history],"P&L":[f'{t.pnl:+.2f}' for t in trade_manager.history]},use_container_width=True,hide_index=True)
    else:
        st.caption("Aucun trade PAPER clôturé dans cette session. La performance historique du moteur se teste via le backtest, pas via une statistique inventée.")

    st.subheader("GESTION DU RISQUE")
    if setup:
        rs=risk_summary(capital,setup["entry"],setup["sl"]); a,b,c,d=st.columns(4); a.metric("Capital",f"{capital:,.2f}"); b.metric("Risque autorisé",f"{rs['risk_amount']:,.2f}"); c.metric("Distance Entry → SL",_fmt(rs["distance"])); d.metric("Unités théoriques",f"{rs['units']:,.2f}"); st.caption(f"Risque ouvert maximum configuré : {rs['max_open_risk_amount']:,.2f} ({rs['max_open_risk_fraction']:.0%}). {rs['note']}")
    else: st.info("La gestion du risque détaillée sera affichée lorsqu'un setup valide existe.")
    st.subheader("POURQUOI CETTE DÉCISION ?"); st.write(result["explanation"])
    if result.get("available_count",0)<len(TIMEFRAMES): st.warning("Certains timeframes sont indisponibles. La confiance est réduite et aucun signal complet n'est forcé.")