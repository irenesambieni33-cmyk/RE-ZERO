from datetime import datetime, timezone


class MacroEngine:
    """Aucun flux macro/calendrier économique en direct n'est branché ici — en fabriquer un
    serait mentir sur la nature de l'information. Le statut MACRO ACCEPTABLE dépend donc :
    1. d'un blackout explicite défini en config (fenêtres connues à l'avance), qui bloque toujours ;
    2. sinon, d'une confirmation manuelle de l'utilisateur (ex. case à cocher côté UI),
       qui doit rester le comportement par défaut restrictif tant qu'aucun vrai flux n'existe."""

    def __init__(self, blackout_windows=None):
        self.blackout_windows = blackout_windows or []

    def evaluate(self, manual_acceptable=False, now_utc=None):
        now_utc = now_utc or datetime.now(timezone.utc)
        active = []
        for w in self.blackout_windows:
            try:
                start = datetime.fromisoformat(w["start"])
                end = datetime.fromisoformat(w["end"])
                if start <= now_utc <= end:
                    active.append(w.get("label", "BLACKOUT"))
            except Exception:
                continue

        if active:
            return {"acceptable": False, "reason": "BLACKOUT_WINDOW_ACTIVE", "active_events": active,
                    "note": "Fenêtre macro à risque déclarée en config.json."}

        return {
            "acceptable": bool(manual_acceptable),
            "reason": "MANUAL_CONFIRMATION" if manual_acceptable else "NO_MANUAL_CONFIRMATION",
            "active_events": [],
            "note": "Pas de flux macro live branché : confirmation manuelle requise.",
        }
