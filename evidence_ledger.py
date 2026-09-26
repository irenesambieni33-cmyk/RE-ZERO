class EvidenceLedger:
    def __init__(self):
        self.items = []
    def add(self, source, observation, truth="FACT"):
        self.items.append({"source": source, "observation": observation, "truth": truth})
    def export(self):
        return list(self.items)
