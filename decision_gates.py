class DecisionGates:
    HARD = ["DATA VALID", "REGIME IDENTIFIED", "STRUCTURE VALID", "SCENARIO DEFINED",
            "CONTRADICTIONS CHECKED", "NO CONTRADICTIONS", "INVALIDATION DEFINED", "RR >= 1:2",
            "RISK ENGINE AVAILABLE", "MACRO ACCEPTABLE", "EXECUTION ACCEPTABLE"]

    def evaluate(self, **values):
        gates = {name: bool(values.get(name, False)) for name in self.HARD}
        failed = [k for k, v in gates.items() if not v]
        decision = "SURVEILLER" if not failed else "PAS DE TRADE"
        return {"gates": gates, "failed_hard_gates": failed, "decision": decision,
                "rule": "Un hard gate échoué impose NO TRADE."}
