from collections import Counter
from typing import Dict, Any
from ..repository.audit_repository import AuditRepository

class AnalyticsService:
    """Produces aggregated oversight from the audit log, free of personal information.
    Intentional design constraint: this service NEVER returns individual-level
    identifiers (individual_id, share code values, passport numbers, DOBs). It
    aggregates only over coarse fields such as organisation_id, role, declared
    purpose, and date. This keeps the analytics surface consistent with privacy
    obligations even when consumed by less-trusted operational dashboards.
    """

    def __init__(self, audit: AuditRepository):
        self.audit = audit

    def summary(self) -> Dict[str, Any]:
        entries = self.audit.read_all()
        attempts = [e for e in entries if e['event_type'] == 'VERIFICATION_ATTEMPT']
        generations = [e for e in entries if e['event_type'] == 'SHARE_CODE_GENERATED']
        failures = [e for e in entries if e['event_type'] == 'VALIDATION_FAILURE']
        by_org: Counter = Counter()
        by_role: Counter = Counter()
        by_purpose: Counter = Counter()
        by_outcome: Counter = Counter()
        by_day: Counter = Counter()
        for a in attempts:
            p = a['payload']
            by_org[p.get('organisation_id')] += 1
            by_role[p.get('role')] += 1
            by_purpose[p.get('declared_purpose')] += 1
            by_outcome[p.get('outcome_status')] += 1
            by_day[a['timestamp'][:10]] += 1
        share_code_by_purpose: Counter = Counter()
        for g in generations:
            share_code_by_purpose[g['payload'].get('purpose')] += 1
        return {'total_verification_attempts': len(attempts), 'total_share_codes_generated': len(generations), 'total_validation_failures': len(failures), 'requests_by_organisation': dict(by_org), 'requests_by_role': dict(by_role), 'requests_by_declared_purpose': dict(by_purpose), 'requests_by_outcome': dict(by_outcome), 'requests_per_day': dict(by_day), 'share_codes_generated_by_purpose': dict(share_code_by_purpose)}
