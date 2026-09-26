class RiskEngine:
    def evaluate(self, entry=None, stop=None, target=None, capital=None, risk_pct=1.0):
        if entry is None or stop is None or target is None:
            return {"available": True, "status": "WAITING_FOR_LEVELS", "rr": None, "gate": False}
        risk = abs(float(entry) - float(stop))
        reward = abs(float(target) - float(entry))
        if risk <= 0:
            return {"available": True, "status": "INVALID_STOP", "rr": None, "gate": False}
        rr = reward / risk
        result = {"available": True, "status": "VALID", "rr": round(rr, 3), "minimum_rr": 2.0, "gate": rr >= 2.0}
        if capital is not None and capital > 0:
            cash_risk = float(capital) * float(risk_pct) / 100.0
            result.update({"capital": float(capital), "risk_pct": float(risk_pct), "cash_risk": round(cash_risk, 2)})
        return result

    def status(self):
        return {"available": True, "minimum_rr": 2.0, "max_trades_day": 3}
