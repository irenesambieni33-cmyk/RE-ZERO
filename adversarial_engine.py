class AdversarialEngine:
    def challenge(self, scenario):
        return {
            "question": "Qu'est-ce qui pourrait me faire changer d'avis ?",
            "checks": ["fakeout", "data_stale", "regime_change", "poor_RR", "macro_event"]
        }
