"""RE-ZERO RE-ZERO intelligent macro + orderflow trading engine."""
import logging
import streamlit as st
from analysis import analyze_multi_timeframe
from config import APP_NAME, CACHE_TTL_SECONDS, INSTRUMENTS
from data import fetch_instrument
from interface import apply_css, render_dashboard
from backtest import backtest_timeframe
from security import validate_setup
from crypto_data import fetch_btc_snapshot
from performance import backtest_trade_plans
from timing import timing_assessment
from alerts import build_alert, send_telegram
from trade_manager import TradeManager
from weekend_market import weekend_policy
from macro_context import fetch_macro_events
from browser_notifications import render_notification_control
from validation_engine import validate_backtest
from streamlit_autorefresh import st_autorefresh
logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title=APP_NAME,page_icon="📊",layout="wide",initial_sidebar_state="expanded")
apply_css()
@st.cache_data(ttl=CACHE_TTL_SECONDS,show_spinner=False)
def load_market(instrument): return fetch_instrument(instrument)
def main():
    st.sidebar.header("Paramètres"); instrument=st.sidebar.selectbox("Marché", list(INSTRUMENTS.keys()), index=2); capital=st.sidebar.number_input("Capital de référence",min_value=0.0,value=1000.0,step=100.0)
    st.sidebar.caption("Risque par trade : 1% • Risque ouvert max : 2% • R:R minimum : 1:2")
    st.sidebar.success("🔐 MODE SÉCURISÉ : ANALYSE")
    st.sidebar.caption("RE-ZERO : EUR/USD + XAU/USD + BTC/USD • Macro + NFP + Liquidity + Orderflow + Trade Manager")
    st.sidebar.warning("Aucun ordre réel n'est autorisé dans cette version. Le mode week-end est réservé aux instruments réellement négociables 24/7, notamment BTC.")
    st.sidebar.subheader("🔔 Notifications téléphone")
    notif_enabled = st.sidebar.checkbox("Activer les notifications navigateur", value=False, help="Autorise les notifications du navigateur. La page RE-ZERO doit rester ouverte.")
    if notif_enabled:
        render_notification_control(True)
    st.sidebar.subheader("⏱️ Surveillance intelligente")
    monitor = st.sidebar.checkbox("Activer la surveillance", value=False)
    refresh_seconds = st.sidebar.select_slider("Fréquence de scan", options=[30,60,120,300], value=60, format_func=lambda x: f"{x}s")
    scan_start = st.sidebar.time_input("Début fenêtre personnalisée", value=__import__("datetime").time(14, 0))
    scan_end = st.sidebar.time_input("Fin fenêtre personnalisée", value=__import__("datetime").time(17, 0))
    if st.sidebar.button("Actualiser les données"): load_market.clear(); st.session_state["analysis_started"]=False; st.rerun()
    wp = weekend_policy(instrument)
    if wp.get("weekend"):
        st.sidebar.info(f"📅 Week-end : {wp["status"]}. {wp["note"]}")
    if monitor:
        st_autorefresh(interval=refresh_seconds * 1000, key="market_monitor_refresh")
        load_market.clear()
        st.sidebar.success(f"🟢 Surveillance active • scan toutes les {refresh_seconds}s")
    else:
        st.sidebar.caption("La surveillance automatique est désactivée.")
    st.markdown(f'<div class="hero"><h1>{APP_NAME}</h1><div class="muted">{INSTRUMENTS[instrument]["label"]} • Trade préparé en <b>M15</b> • Analyse D1 → H4 → H1 → M15 → M5</div></div>',unsafe_allow_html=True)
    if "trade_manager" not in st.session_state:
        st.session_state["trade_manager"] = TradeManager()
    if not st.session_state.get("analysis_started",False):
        st.info("Configure ton instrument et ton capital, puis démarre l'analyse. L'IA observe d'abord les unités supérieures avant de préparer le setup M15.")
        if st.button("🚀 DÉBUTER L'ANALYSE",type="primary",use_container_width=True): st.session_state["analysis_started"]=True; st.rerun()
        st.caption("Aucun signal n'est calculé avant l'appui sur le bouton."); return
    if st.button("🔄 Refaire l'analyse",use_container_width=True): load_market.clear(); st.rerun()
    if st.sidebar.button("🧪 Validation statistique M15"):
        st.session_state["run_stat_validation"] = True
    try:
        with st.spinner("Analyse D1 → H4 → H1 → M15 → M5 en cours…"): frames,warnings,used_proxy=load_market(instrument)
        if used_proxy: st.warning("XAU/USD : GC=F est utilisé comme proxy futures. Ce n'est pas le spot XAU/USD.")
        for key,msg in warnings.items():
            if key!="global": st.info(msg)
        if not frames: st.error("Impossible de récupérer les données de marché. Vérifiez la connexion réseau puis réessayez."); return
        result=analyze_multi_timeframe(frames)
        macro_events=fetch_macro_events(days=7)
        crypto_snapshot = fetch_btc_snapshot() if instrument == "BTC/USD" else None
        if st.session_state.pop("run_stat_validation", False):
            with st.spinner("Validation historique séquentielle + robustesse statistique en cours…"):
                bt=backtest_trade_plans(frames.get("M15"), "M15", horizon=16, max_samples=160, step=4)
            st.subheader("🧪 VALIDATION STATISTIQUE RE-ZERO")
            if bt.get("ok"):
                rows=bt.get("rows",[])
                vr=validate_backtest(rows, n_trials=1) if rows else {"verdict":"ÉCHANTILLON TROP PETIT","robustness_score":0,"walk_forward_positive_fold_rate":float("nan"),"permutation_pvalue":float("nan"),"note":"Aucun setup."}
                a,b,c,d=st.columns(4)
                a.metric("Trades", bt.get("trades",0))
                b.metric("Expectancy", f'{bt.get("expectancy_r",0):+.2f}R')
                c.metric("Robustesse", f'{vr.get("robustness_score",0):.0f}/100')
                d.metric("Verdict", vr.get("verdict","—"))
                e,f,g=st.columns(3)
                e.metric("Win rate", f'{bt.get("win_rate",0):.1f}%')
                wf=vr.get("walk_forward_positive_fold_rate")
                f.metric("Walk-forward positif", "—" if wf!=wf else f'{wf*100:.0f}%')
                pv=vr.get("permutation_pvalue")
                g.metric("Permutation p", "—" if pv!=pv else f'{pv:.3f}')
                st.caption(vr.get("note", ""))
                if vr.get("regimes"):
                    st.write("**Résultats par régime**")
                    st.dataframe({k:{"trades":v.get("trades",0),"win_rate":round(v.get("win_rate",0),1),"expectancy_R":round(v.get("expectancy_r",0),3),"max_dd_R":round(v.get("max_drawdown_r",0),2)} for k,v in vr["regimes"].items()},use_container_width=True)
            else:
                st.warning(bt.get("reason","Validation indisponible."))
        price=next((float(frames[tf]["close"].iloc[-1]) for tf in ["M5","M15","H1","H4","D1"] if tf in frames and not frames[tf].empty),None)
        if price is None: st.error("Aucun prix exploitable n'a été trouvé."); return
        render_dashboard(instrument,price,result,capital,crypto_snapshot=crypto_snapshot, monitor=monitor, custom_window=(scan_start.strftime("%H:%M"), scan_end.strftime("%H:%M")), trade_manager=st.session_state["trade_manager"], macro_events=macro_events)
    except Exception:
        logging.exception("Unexpected application error"); st.error("Une erreur interne est survenue pendant l'analyse. L'interface reste disponible ; consultez les logs pour le diagnostic technique.")
if __name__=="__main__": main()
