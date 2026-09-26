class TruthLayer:
    LEVELS = ["FACT", "DERIVED", "INFERRED", "HYPOTHESIS", "UNKNOWN", "CONTRADICTORY"]
    def tag(self, value, level):
        return {"value": value, "truth_level": level}
