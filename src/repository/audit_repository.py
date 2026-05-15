import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

class AuditRepository:
    """Append-only audit trail written as JSONL"""

    def __init__(self, audit_path: str):
        self.path = Path(audit_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        if not self.path.exists():
            self.path.touch()

    def record(self, event_type: str, payload: Dict[str, Any], correlation_id: Optional[str]=None) -> None:
        entry = {'timestamp': datetime.now(timezone.utc).isoformat(), 'event_type': event_type, 'correlation_id': correlation_id, 'payload': payload}
        line = json.dumps(entry, sort_keys=True)
        with self._lock:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(line + '\n')

    def read_all(self) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        entries = []
        with self.path.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
