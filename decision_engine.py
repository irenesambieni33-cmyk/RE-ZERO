class DecisionEngine:
    def decide(self, gates):
        return "PAS DE TRADE" if not all(gates.values()) else "SURVEILLER"
