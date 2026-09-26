class DriftDetectionEngine:
    def assess(self, baseline=None, recent=None):
        if baseline is None or recent is None:
            return {"status": "NOT_AVAILABLE", "reason": "Historique insuffisant"}
        return {"status": "OBSERVATION", "data_drift": "NOT_IMPLEMENTED_WITHOUT_VALID_SAMPLE"}
