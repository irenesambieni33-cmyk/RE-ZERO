class ContradictionEngine:
    def check(self, evidence):
        return {
            "contradictions": [],
            "status": "NO_CRITICAL_CONTRADICTION_DETECTED",
            "note": "Absence de contradiction ≠ validation."
        }
