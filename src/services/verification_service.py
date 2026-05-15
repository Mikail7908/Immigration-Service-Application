import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from ..domain.enums import OutcomeStatus, RequesterRole, VerificationRoute
from ..domain.models import VerificationRequest, VerificationOutcome, Individual
from ..repository.file_repository import FileRepository
from ..repository.audit_repository import AuditRepository
from ..validation.validators import validate_share_code_format, validate_share_code_expiry, validate_dob_format, validate_passport_format, validate_permit_format, validate_purpose_for_role, validate_route_for_role
from ..logging_setup import get_logger
from .authorisation_service import AuthorisationService

class VerificationService:
    """Orchestrates the verification flow.
    Flow is intentionally linear and deterministic:
      1. Authorise caller
      2. Validate route/purpose compatibility
      3. Validate inputs (share code OR document)
      4. Resolve individual record
      5. Apply role-scoped projection of status fields
      6. Record audit entry and return outcome
    Failure outcomes use the same VerificationOutcome shape as success outcomes so
    callers cannot distinguish failure types beyond what the role is permitted to
    see. This avoids leaking internal behaviour through response shape.
    """

    def __init__(self, repo: FileRepository, audit: AuditRepository, authoriser: AuthorisationService):
        self.repo = repo
        self.audit = audit
        self.authoriser = authoriser
        self.log = get_logger()

    def verify(self, req: VerificationRequest) -> VerificationOutcome:
        correlation_id = str(uuid.uuid4())
        self.log.info('verification request received', extra={'event': 'verify.received', 'correlation_id': correlation_id})
        auth_result, org = self.authoriser.authorise(req.organisation_id, req.organisation_email, req.role, req.confirm_lawful_purpose, req.confirm_data_protection, req.confirm_non_discriminatory)
        if not auth_result.ok:
            status = OutcomeStatus.CONFIRMATIONS_MISSING if 'confirmations' in auth_result.reason else OutcomeStatus.UNAUTHORISED
            return self._fail(req, correlation_id, status, auth_result.reason)
        route_check = validate_route_for_role(req.role, req.route)
        if not route_check.ok:
            return self._fail(req, correlation_id, OutcomeStatus.UNAUTHORISED, route_check.reason)
        purpose_check = validate_purpose_for_role(req.role, req.declared_purpose)
        if not purpose_check.ok:
            return self._fail(req, correlation_id, OutcomeStatus.PURPOSE_MISMATCH, purpose_check.reason)
        if req.route == VerificationRoute.SHARE_CODE.value:
            outcome = self._verify_share_code(req, correlation_id)
        else:
            outcome = self._verify_document(req, correlation_id)
        self.audit.record('VERIFICATION_ATTEMPT', {'organisation_id': req.organisation_id, 'role': req.role, 'route': req.route, 'declared_purpose': req.declared_purpose, 'outcome_status': outcome.status}, correlation_id=correlation_id)
        self.log.info('verification request completed', extra={'event': 'verify.completed', 'correlation_id': correlation_id})
        return outcome

    def _verify_share_code(self, req: VerificationRequest, correlation_id: str) -> VerificationOutcome:
        fmt = validate_share_code_format(req.share_code)
        if not fmt.ok:
            return self._fail(req, correlation_id, OutcomeStatus.INVALID_INPUT, fmt.reason)
        dob_fmt = validate_dob_format(req.date_of_birth)
        if not dob_fmt.ok:
            return self._fail(req, correlation_id, OutcomeStatus.INVALID_INPUT, dob_fmt.reason)
        sc = self.repo.find_share_code(req.share_code)
        if sc is None:
            return self._fail(req, correlation_id, OutcomeStatus.NOT_FOUND, 'share code not recognised')
        if sc.revoked:
            return self._fail(req, correlation_id, OutcomeStatus.EXPIRED, 'share code revoked')
        expiry = validate_share_code_expiry(sc.expires_at)
        if not expiry.ok:
            return self._fail(req, correlation_id, OutcomeStatus.EXPIRED, expiry.reason)
        if sc.purpose != req.declared_purpose:
            return self._fail(req, correlation_id, OutcomeStatus.PURPOSE_MISMATCH, 'share code purpose does not match declared purpose')
        individual = self.repo.find_individual(sc.individual_id)
        if individual is None:
            return self._fail(req, correlation_id, OutcomeStatus.NOT_FOUND, 'individual record missing')
        if individual.date_of_birth != req.date_of_birth:
            return self._fail(req, correlation_id, OutcomeStatus.IDENTITY_MISMATCH, 'date of birth does not match record')
        return self._project_outcome(individual, req, correlation_id)

    def _verify_document(self, req: VerificationRequest, correlation_id: str) -> VerificationOutcome:
        if req.passport_number:
            fmt = validate_passport_format(req.passport_number)
            if not fmt.ok:
                return self._fail(req, correlation_id, OutcomeStatus.INVALID_INPUT, fmt.reason)
            individual = self.repo.find_individual_by_passport(req.passport_number)
        elif req.permit_number:
            fmt = validate_permit_format(req.permit_number)
            if not fmt.ok:
                return self._fail(req, correlation_id, OutcomeStatus.INVALID_INPUT, fmt.reason)
            individual = self.repo.find_individual_by_permit(req.permit_number)
        else:
            return self._fail(req, correlation_id, OutcomeStatus.INVALID_INPUT, 'passport or permit number required')
        if individual is None:
            return self._fail(req, correlation_id, OutcomeStatus.NOT_FOUND, 'document not recognised')
        return self._project_outcome(individual, req, correlation_id)

    def _project_outcome(self, individual: Individual, req: VerificationRequest, correlation_id: str) -> VerificationOutcome:
        role = RequesterRole(req.role)
        details: Dict[str, Any] = {}
        eligible: bool
        if role == RequesterRole.EMPLOYER:
            eligible = individual.right_to_work
            details = {'right_to_work': eligible, 'check_until': individual.status_valid_until, 'conditions': individual.conditions}
        elif role == RequesterRole.LANDLORD:
            eligible = individual.right_to_rent
            details = {'right_to_rent': eligible, 'check_until': individual.status_valid_until}
        elif role == RequesterRole.EDUCATION:
            eligible = individual.right_to_study
            details = {'right_to_study': eligible, 'check_until': individual.status_valid_until, 'conditions': individual.conditions}
        elif role == RequesterRole.BORDER_CONTROL:
            eligible = individual.entry_permitted
            details = {'entry_permitted': eligible, 'status_type': individual.status_type, 'status_valid_until': individual.status_valid_until}
        else:
            eligible = individual.status_valid_until is None or individual.status_valid_until >= datetime.now(timezone.utc).date().isoformat()
            details = {'status_type': individual.status_type, 'status_valid': eligible, 'conditions': individual.conditions}
        status = OutcomeStatus.ELIGIBLE if eligible else OutcomeStatus.NOT_ELIGIBLE
        return VerificationOutcome(status=status.value, reason='ok' if eligible else 'individual does not meet role-specific eligibility', details=details, correlation_id=correlation_id)

    def _fail(self, req: VerificationRequest, correlation_id: str, status: OutcomeStatus, reason: str) -> VerificationOutcome:
        self.log.info('verification failure: %s', reason, extra={'event': 'verify.failure', 'correlation_id': correlation_id})
        self.audit.record('VALIDATION_FAILURE', {'organisation_id': req.organisation_id, 'role': req.role, 'route': req.route, 'declared_purpose': req.declared_purpose, 'status': status.value, 'reason': reason}, correlation_id=correlation_id)
        return VerificationOutcome(status=status.value, reason=reason, details={}, correlation_id=correlation_id)
