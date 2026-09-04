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
    st.sidebar.caption("RE-ZERO RE-ZERO : EUR/USD + XAU/USD + BTC/USD • Macro + NFP + Liquidity + Orderflow + Trade Manager")
    st.sidebar.warning("Aucun ordre réel n'est autorisé dans cette version. Le mode week-end est réservé aux instruments réellement négociables 24/7, notamment BTC.")
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
    if st.sidebar.button("🧪 Backtest rapide M15"):
        st.session_state["run_backtest"] = True
    try:
        with st.spinner("Analyse D1 → H4 → H1 → M15 → M5 en cours…"): frames,warnings,used_proxy=load_market(instrument)
        if used_proxy: st.warning("XAU/USD : GC=F est utilisé comme proxy futures. Ce n'est pas le spot XAU/USD.")
        for key,msg in warnings.items():
            if key!="global": st.info(msg)
        if not frames: st.error("Impossible de récupérer les données de marché. Vérifiez la connexion réseau puis réessayez."); return
        result=analyze_multi_timeframe(frames)
        macro_events=fetch_macro_events(days=7)
        crypto_snapshot = fetch_btc_snapshot() if instrument == "BTC/USD" else None
        if st.session_state.pop("run_backtest", False):
            with st.spinner("Backtest historique M15 en cours…"):
                bt=backtest_timeframe(frames.get("M15"), "M15")
            st.subheader("🧪 VALIDATION HISTORIQUE V5")
            if bt.get("ok"):
                a,b,c,d=st.columns(4); a.metric("Trades simulés",bt["samples"]); b.metric("Win Rate",f"{bt["win_rate"]:.1f}%"); c.metric("Gagnants",bt["wins"]); d.metric("Perdants",bt["losses"])
                st.dataframe({"Confiance":list(bt["buckets"].keys()),"Trades":[v["trades"] for v in bt["buckets"].values()],"Win Rate historique":[f"{v["win_rate"]:.1f}%" for v in bt["buckets"].values()]},use_container_width=True,hide_index=True)
                st.caption(bt["note"])
            else: st.warning(bt.get("reason","Backtest indisponible."))
        price=next((float(frames[tf]["close"].iloc[-1]) for tf in ["M5","M15","H1","H4","D1"] if tf in frames and not frames[tf].empty),None)
        if price is None: st.error("Aucun prix exploitable n'a été trouvé."); return
        render_dashboard(instrument,price,result,capital,crypto_snapshot=crypto_snapshot, monitor=monitor, custom_window=(scan_start.strftime("%H:%M"), scan_end.strftime("%H:%M")), trade_manager=st.session_state["trade_manager"], macro_events=macro_events)
    except Exception:
        logging.exception("Unexpected application error"); st.error("Une erreur interne est survenue pendant l'analyse. L'interface reste disponible ; consultez les logs pour le diagnostic technique.")
if __name__=="__main__": main()
