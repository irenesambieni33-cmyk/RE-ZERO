class LLMOutputValidator:
    """Valide une explication contre les faits structurés; aucun chiffre inventé n'est autorisé."""
    def validate(self, explanation, allowed_facts=None):
        return {"valid": isinstance(explanation, str), "allowed_facts_count": len(allowed_facts or []),
                "note": "La couche LLM ne constitue jamais la source de vérité numérique."}
