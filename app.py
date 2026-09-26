import streamlit as st
from core.intelligence_core import MarketIntelligenceCore

st.set_page_config(page_title="RE-ZERO", page_icon="🧠", layout="wide")
st.title("🧠 RE-ZERO — V4.4 TRADER")
st.caption("Analyste de marché • aide à la décision • aucune exécution broker automatique")
core = MarketIntelligenceCore()
asset = st.selectbox("ASSET", ["EUR/USD", "XAU/USD (GC=F PROXY)", "BTC/USD"])
tf = st.selectbox("TIMEFRAME", ["M15", "M30", "H1", "H4", "D1"])
if "GC=F" in asset:
    st.warning("PROXY DATA — GC=F n'est pas un flux XAU/USD direct.")
if st.button("🔎 START ANALYSIS", use_container_width=True):
    r = core.analyze(asset, tf)
    st.metric("MARKET STATUS", r["market_status"])
    st.write("SYSTEM STATE:", r.get("system_state"))
    st.subheader("DECISION")
    decision = r["decision"]["decision"]
    st.error("⛔ PAS DE TRADE" if decision == "PAS DE TRADE" else f"🟡 {decision}")
    st.json(r["decision"])
    st.subheader("DATA STATUS"); st.json(r["data"])
    st.subheader("MARKET INTELLIGENCE"); st.json(r.get("intelligence", {}))
    st.subheader("RISK & EXECUTION"); st.json({"risk":r.get("risk"), "execution_quality":r.get("execution_quality")})
    if hasattr(r.get("indicators"), "empty") and not r["indicators"].empty:
        st.subheader("INDICATORS"); st.dataframe(r["indicators"], use_container_width=True)
    st.caption(f"Audit: {r.get('audit_id','N/A')} • Config: {r.get('config_version','N/A')} • {r.get('timestamp','')}")
