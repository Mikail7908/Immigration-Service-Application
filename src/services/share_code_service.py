import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Optional
from ..domain.enums import Purpose
from ..domain.models import ShareCode
from ..repository.file_repository import FileRepository
from ..repository.audit_repository import AuditRepository
from ..logging_setup import get_logger
DEFAULT_TTL_HOURS = 24
CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 9

class ShareCodeService:

    def __init__(self, repo: FileRepository, audit: AuditRepository):
        self.repo = repo
        self.audit = audit
        self.log = get_logger()

    def generate(self, individual_id: str, purpose: str, ttl_hours: int=DEFAULT_TTL_HOURS) -> Optional[ShareCode]:
        try:
            Purpose(purpose)
        except ValueError:
            self.log.warning('share code generation rejected: unknown purpose', extra={'event': 'share_code.reject', 'correlation_id': None})
            return None
        if self.repo.find_individual(individual_id) is None:
            self.log.warning('share code generation rejected: unknown individual', extra={'event': 'share_code.reject', 'correlation_id': None})
            return None
        for _ in range(10):
            code = ''.join((secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH)))
            if self.repo.find_share_code(code) is None:
                break
        else:
            self.log.error('share code generation failed: collision exhaustion')
            return None
        now = datetime.now(timezone.utc)
        sc = ShareCode(code=code, individual_id=individual_id, purpose=purpose, created_at=now.isoformat(), expires_at=(now + timedelta(hours=ttl_hours)).isoformat(), revoked=False)
        self.repo.save_share_code(sc)
        self.audit.record('SHARE_CODE_GENERATED', {'individual_id': individual_id, 'purpose': purpose, 'expires_at': sc.expires_at})
        self.log.info('share code generated', extra={'event': 'share_code.generated', 'correlation_id': None})
        return sc

    def revoke(self, code: str) -> bool:
        ok = self.repo.revoke_share_code(code)
        if ok:
            self.audit.record('SHARE_CODE_REVOKED', {'code': code})
            self.log.info('share code revoked', extra={'event': 'share_code.revoked', 'correlation_id': None})
        return ok
