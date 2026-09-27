import json
from pathlib import Path
from data.data_engine import DataEngine
from indicators.indicator_engine import IndicatorEngine
from market.market_state import MarketStateEngine
from market.mtf_engine import MTFEngine
from market.macro_engine import MacroEngine
from analysis.structure_engine import StructureEngine
from analysis.liquidity_engine import LiquidityEngine
from analysis.price_action_engine import PriceActionEngine
from analysis.scenario_engine import ScenarioEngine
from analysis.contradiction_engine import ContradictionEngine
from analysis.adversarial_engine import AdversarialEngine
from decision.decision_gates import DecisionGates
from decision.decision_history import DecisionHistory
from risk.risk_engine import RiskEngine
from risk.level_engine import derive_levels
from execution.execution_quality import ExecutionQualityEngine
from audit.audit_engine import AuditEngine
from core.capability_registry import CapabilityRegistry
from core.system_state import SystemState
from truth.evidence_ledger import EvidenceLedger

class MarketIntelligenceCore:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        self.cfg = json.loads((root / "config.json").read_text(encoding="utf-8"))
        self.data, self.ind, self.state = DataEngine(), IndicatorEngine(), MarketStateEngine()
        self.structure, self.liq, self.pa = StructureEngine(), LiquidityEngine(), PriceActionEngine()
        self.scenario, self.contra, self.adversarial = ScenarioEngine(), ContradictionEngine(), AdversarialEngine()
        self.gates, self.risk, self.execution = DecisionGates(), RiskEngine(), ExecutionQualityEngine()
        self.audit, self.cap, self.system = AuditEngine(), CapabilityRegistry(), SystemState()
        self.history = DecisionHistory()
        self.mtf = MTFEngine(self.data, self.ind, self.state)
        self.macro = MacroEngine(self.cfg.get("macro", {}).get("blackout_windows", []))

    def analyze(self, asset, timeframe, macro_acceptable=False, event_lock=False):
        self.system.set("DATA_LOADING")
        profile = self.cfg["assets"][asset]
        dr = self.data.fetch(asset, profile["ticker"], timeframe, profile.get("proxy", False), profile.get("proxy_instrument"))
        if dr.data is None:
            self.system.set("DEGRADED")
            decision = self.gates.evaluate(**{"DATA VALID": False})
            self.history.record(decision["decision"], "DATA_UNAVAILABLE")
            return {"market_status":"DATA UNAVAILABLE", "system_state":self.system.state, "data":dr.__dict__, "indicators":{}, "intelligence":{}, "risk":self.risk.status(), "decision":decision}

        self.system.set("ANALYZING")
        df = self.ind.calculate(dr.data)
        state, structure = self.state.detect(df), self.structure.analyze(df)
        liquidity, price_action = self.liq.analyze(df), self.pa.analyze(df)
        scenarios = self.scenario.build(state, structure, liquidity, price_action)

        ledger = EvidenceLedger()
        ledger.add("DATA", {"status": dr.status, "quality": dr.quality_score, "freshness": dr.freshness_score}, "FACT")
        ledger.add("REGIME", state, "DERIVED")
        ledger.add("STRUCTURE", structure, "INFERRED")
        ledger.add("LIQUIDITY", liquidity, "INFERRED")
        ledger.add("PRICE_ACTION", price_action, "INFERRED")
        contradictions = self.contra.check(ledger.export())

        mtf = self.mtf.analyze(asset, profile["ticker"], timeframe, self.cfg.get("mtf_hierarchy", []),
                                profile.get("proxy", False), profile.get("proxy_instrument"))

        data_valid = dr.status == "VALID"
        regime_valid = state.get("regime") not in (None, "UNKNOWN")
        structure_valid = structure.get("status") != "INSUFFICIENT" and bool(structure.get("swing_highs") or structure.get("swing_lows"))
        scenario_defined = bool(scenarios)
        invalidation_defined = any("À définir" not in str(s.get("invalidation", "")) for s in scenarios)

        levels = derive_levels(df, state, structure, self.cfg["risk"].get("minimum_rr", 2.0))
        if levels:
            risk = self.risk.evaluate(entry=levels["entry"], stop=levels["stop"], target=levels["target"],
                                       risk_pct=self.cfg["risk"].get("default_risk_pct", 1.0))
            risk["direction"], risk["basis"] = levels["direction"], levels["basis"]
        else:
            risk = self.risk.evaluate()

        execution = self.execution.evaluate(asset=asset, data_fresh=dr.freshness_score >= 0.5, event_lock=event_lock)
        macro = self.macro.evaluate(manual_acceptable=macro_acceptable)

        gates = self.gates.evaluate(**{
            "DATA VALID": data_valid, "REGIME IDENTIFIED": regime_valid, "STRUCTURE VALID": structure_valid,
            "SCENARIO DEFINED": scenario_defined, "CONTRADICTIONS CHECKED": True,
            "NO CONTRADICTIONS": contradictions.get("status") == "NO_CRITICAL_CONTRADICTION_DETECTED",
            "INVALIDATION DEFINED": invalidation_defined, "RR >= 1:2": bool(risk.get("gate")),
            "RISK ENGINE AVAILABLE": True, "MACRO ACCEPTABLE": bool(macro.get("acceptable")),
            "EXECUTION ACCEPTABLE": execution["acceptable"]})
        self.system.set("DECISION_READY")
        version = self.history.record(gates["decision"], ", ".join(gates["failed_hard_gates"]))
        return {
            "market_status":"ANALYSIS AVAILABLE", "system_state":self.system.state, "data":dr.__dict__,
            "indicators":df.tail(1).T.reset_index().rename(columns={"index":"indicator"}),
            "intelligence":{"capabilities":self.cap.snapshot(), "regime":state, "structure":structure,
                "liquidity":liquidity, "price_action":price_action, "scenarios":scenarios,
                "contradictions":contradictions, "adversarial":self.adversarial.challenge(scenarios[0]),
                "mtf":mtf, "evidence_ledger":ledger.export()},
            "risk":risk, "execution_quality":execution, "macro":macro, "decision":gates,
            "decision_version":version, "audit_id":self.audit.id(), "config_version":self.cfg.get("version"),
            "timestamp":self.audit.stamp()}
