import streamlit as st
from core.intelligence_core import MarketIntelligenceCore

st.set_page_config(page_title="RE-ZERO", page_icon="🧠", layout="wide")
st.title("🧠 RE-ZERO — V4.4 TRADER")
st.caption("Analyste de marché • aide à la décision • aucune exécution broker automatique")
if "core" not in st.session_state:
    st.session_state.core = MarketIntelligenceCore()
core = st.session_state.core
asset = st.selectbox("ASSET", ["EUR/USD", "XAU/USD (GC=F PROXY)", "BTC/USD"])
tf = st.selectbox("TIMEFRAME", ["M15", "M30", "H1", "H4", "D1"])
if "GC=F" in asset:
    st.warning("PROXY DATA — GC=F n'est pas un flux XAU/USD direct.")

with st.expander("⚠️ GATES MANUELS (aucun flux live branché pour ces deux points)"):
    macro_ok = st.checkbox(
        "Aucun événement macro majeur imminent (confirmation manuelle de ma part)",
        value=False,
        help="Pas de calendrier économique live branché : ce gate reste bloqué tant que tu ne confirmes pas toi-même.",
    )
    event_lock = st.checkbox("Verrouiller (news / événement en cours)", value=False)

if st.button("🔎 START ANALYSIS", use_container_width=True):
    r = core.analyze(asset, tf, macro_acceptable=macro_ok, event_lock=event_lock)
    st.metric("MARKET STATUS", r["market_status"])
    st.write("SYSTEM STATE:", r.get("system_state"))
    st.subheader("DECISION")
    decision = r["decision"]["decision"]
    st.error("⛔ PAS DE TRADE" if decision == "PAS DE TRADE" else f"🟡 {decision}")
    st.json(r["decision"])

    st.subheader("🎯 SETUP")
    risk = r.get("risk") or {}
    if risk.get("status") == "VALID":
        direction = risk.get("direction", "?")
        icon = "🟢" if direction == "LONG" else "🔴" if direction == "SHORT" else "⚪"
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(f"{icon} DIRECTION", direction)
        c2.metric("ENTRY", f"{risk['entry']:.5f}")
        c3.metric("STOP LOSS", f"{risk['stop']:.5f}")
        c4.metric("TAKE PROFIT", f"{risk['target']:.5f}")
        st.caption(f"RR = {risk['rr']} (minimum requis : {risk['minimum_rr']}) • {risk.get('basis', '')}")
        if decision == "PAS DE TRADE":
            st.warning(
                "Setup calculé mais la décision reste PAS DE TRADE : un ou plusieurs autres "
                "hard gates ont échoué (voir DECISION ci-dessus). Ce setup n'est PAS une "
                "recommandation à exécuter tant que la décision globale n'est pas SURVEILLER."
            )
    elif risk.get("status") == "WAITING_FOR_LEVELS":
        st.info("Pas de setup directionnel : régime non tranché (RANGE/UNKNOWN) ou structure insuffisante pour dériver un stop réel.")
    elif risk.get("status") == "INVALID_STOP":
        st.warning("Setup écarté : le stop dérivé de la structure est du mauvais côté du prix actuel (donnée incohérente).")
    else:
        st.info("Pas de setup disponible pour cette analyse.")

    intel = r.get("intelligence", {})
    if intel.get("mtf"):
        st.subheader("MTF (confluence multi-timeframe)")
        st.json(intel["mtf"])

    st.subheader("DATA STATUS"); st.json(r["data"])
    st.subheader("MARKET INTELLIGENCE"); st.json(intel)
    st.subheader("RISK & EXECUTION")
    st.json({"risk": r.get("risk"), "execution_quality": r.get("execution_quality"), "macro": r.get("macro")})
    if hasattr(r.get("indicators"), "empty") and not r["indicators"].empty:
        st.subheader("INDICATORS"); st.dataframe(r["indicators"], use_container_width=True)
    st.caption(f"Audit: {r.get('audit_id','N/A')} • Config: {r.get('config_version','N/A')} • {r.get('timestamp','')}")

with st.expander("📜 DECISION HISTORY (session)"):
    st.json(core.history.export())
