import json
import os
import threading
from pathlib import Path
from typing import List, Optional
from ..domain.models import Individual, ShareCode, Organisation

class FileRepository:
    """JSON file-based persistence for individuals, organisations, share codes"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.individuals_path = self.data_dir / 'individuals.json'
        self.organisations_path = self.data_dir / 'organisations.json'
        self.share_codes_path = self.data_dir / 'share_codes.json'
        self._lock = threading.Lock()
        for p in (self.individuals_path, self.organisations_path, self.share_codes_path):
            if not p.exists():
                p.write_text('[]')

    def _read(self, path: Path) -> List[dict]:
        with path.open('r', encoding='utf-8') as f:
            return json.load(f)

    def _write(self, path: Path, data: List[dict]) -> None:
        tmp = path.with_suffix(path.suffix + '.tmp')
        with tmp.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)

    def list_individuals(self) -> List[Individual]:
        return [Individual(**d) for d in self._read(self.individuals_path)]

    def find_individual(self, individual_id: str) -> Optional[Individual]:
        for d in self._read(self.individuals_path):
            if d['individual_id'] == individual_id:
                return Individual(**d)
        return None

    def find_individual_by_passport(self, passport_number: str) -> Optional[Individual]:
        for d in self._read(self.individuals_path):
            if d.get('passport_number') == passport_number:
                return Individual(**d)
        return None

    def find_individual_by_permit(self, permit_number: str) -> Optional[Individual]:
        for d in self._read(self.individuals_path):
            if d.get('permit_number') == permit_number:
                return Individual(**d)
        return None

    def find_organisation(self, organisation_id: str) -> Optional[Organisation]:
        for d in self._read(self.organisations_path):
            if d['organisation_id'] == organisation_id:
                return Organisation(**d)
        return None

    def list_organisations(self) -> List[Organisation]:
        return [Organisation(**d) for d in self._read(self.organisations_path)]

    def save_share_code(self, code: ShareCode) -> None:
        with self._lock:
            data = self._read(self.share_codes_path)
            data.append(code.to_dict())
            self._write(self.share_codes_path, data)

    def find_share_code(self, code: str) -> Optional[ShareCode]:
        for d in self._read(self.share_codes_path):
            if d['code'] == code:
                return ShareCode(**d)
        return None

    def list_share_codes(self) -> List[ShareCode]:
        return [ShareCode(**d) for d in self._read(self.share_codes_path)]

    def revoke_share_code(self, code: str) -> bool:
        with self._lock:
            data = self._read(self.share_codes_path)
            for d in data:
                if d['code'] == code:
                    d['revoked'] = True
                    self._write(self.share_codes_path, data)
                    return True
            return False
