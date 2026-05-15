from typing import Tuple
from ..domain.models import Organisation
from ..repository.file_repository import FileRepository
from ..validation.validators import validate_email_format, validate_email_domain, validate_confirmations, ValidationResult

class AuthorisationService:
    """Determines whether a requesting organisation is allowed to call the service.
    Authorisation is intentionally separate from input validation: the design
    distinguishes "do we trust the caller?" from "is the caller's payload well
    formed?". This lets the audit trail report unauthorised attempts independently
    of malformed-input failures.
    """

    def __init__(self, repo: FileRepository):
        self.repo = repo

    def authorise(self, organisation_id: str, organisation_email: str, role: str, lawful: bool, data_protection: bool, non_discriminatory: bool) -> Tuple[ValidationResult, Organisation]:
        conf = validate_confirmations(lawful, data_protection, non_discriminatory)
        if not conf.ok:
            return (conf, None)
        email_fmt = validate_email_format(organisation_email)
        if not email_fmt.ok:
            return (email_fmt, None)
        org = self.repo.find_organisation(organisation_id)
        if org is None:
            return (ValidationResult.failure('organisation not recognised'), None)
        if not org.authorised:
            return (ValidationResult.failure('organisation not authorised'), None)
        if org.role != role:
            return (ValidationResult.failure('declared role does not match organisation record'), None)
        domain_check = validate_email_domain(organisation_email, org.email_domain)
        if not domain_check.ok:
            return (domain_check, None)
        return (ValidationResult.success(), org)
