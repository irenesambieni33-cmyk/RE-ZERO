import uuid
from datetime import datetime, timezone

class AuditEngine:
    def id(self):
        return "RZ-" + uuid.uuid4().hex[:12].upper()
    def stamp(self):
        return datetime.now(timezone.utc).isoformat()
