import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional
from ..domain.enums import RequesterRole, Purpose, ROLE_PURPOSE_MAP, AUTHORITY_ROLES, SHARE_CODE_ROLES
SHARE_CODE_PATTERN = re.compile('^[A-Z0-9]{9}$')
PASSPORT_PATTERN = re.compile('^[A-Z0-9]{8,12}$')
PERMIT_PATTERN = re.compile('^P[A-Z0-9]{7,11}$')
DOB_PATTERN = re.compile('^\\d{4}-\\d{2}-\\d{2}$')
EMAIL_PATTERN = re.compile('^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$')

@dataclass
class ValidationResult:
    ok: bool
    reason: str = ''

    @classmethod
    def success(cls) -> 'ValidationResult':
        return cls(True, '')

    @classmethod
    def failure(cls, reason: str) -> 'ValidationResult':
        return cls(False, reason)

def validate_share_code_format(code: Optional[str]) -> ValidationResult:
    if not code:
        return ValidationResult.failure('share code missing')
    if not SHARE_CODE_PATTERN.match(code):
        return ValidationResult.failure('share code format invalid')
    return ValidationResult.success()

def validate_dob_format(dob: Optional[str]) -> ValidationResult:
    if not dob:
        return ValidationResult.failure('date of birth missing')
    if not DOB_PATTERN.match(dob):
        return ValidationResult.failure('date of birth format invalid')
    try:
        date.fromisoformat(dob)
    except ValueError:
        return ValidationResult.failure('date of birth not a real date')
    return ValidationResult.success()

def validate_passport_format(passport: Optional[str]) -> ValidationResult:
    if not passport:
        return ValidationResult.failure('passport number missing')
    if not PASSPORT_PATTERN.match(passport):
        return ValidationResult.failure('passport number format invalid')
    return ValidationResult.success()

def validate_permit_format(permit: Optional[str]) -> ValidationResult:
    if not permit:
        return ValidationResult.failure('permit number missing')
    if not PERMIT_PATTERN.match(permit):
        return ValidationResult.failure('permit number format invalid')
    return ValidationResult.success()

def validate_email_format(email: Optional[str]) -> ValidationResult:
    if not email:
        return ValidationResult.failure('organisation email missing')
    if not EMAIL_PATTERN.match(email):
        return ValidationResult.failure('organisation email format invalid')
    return ValidationResult.success()

def validate_email_domain(email: str, expected_domain: str) -> ValidationResult:
    domain = email.split('@', 1)[1].lower()
    if domain != expected_domain.lower():
        return ValidationResult.failure('organisation email domain does not match record')
    return ValidationResult.success()

def validate_share_code_expiry(expires_at_iso: str, now: Optional[datetime]=None) -> ValidationResult:
    now = now or datetime.now(timezone.utc)
    try:
        expires_at = datetime.fromisoformat(expires_at_iso)
    except ValueError:
        return ValidationResult.failure('share code expiry malformed')
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        return ValidationResult.failure('share code expired')
    return ValidationResult.success()

def validate_purpose_for_role(role: str, purpose: str) -> ValidationResult:
    try:
        role_enum = RequesterRole(role)
        purpose_enum = Purpose(purpose)
    except ValueError:
        return ValidationResult.failure('unknown role or purpose')
    allowed = ROLE_PURPOSE_MAP.get(role_enum, set())
    if purpose_enum not in allowed:
        return ValidationResult.failure('declared purpose not permitted for role')
    return ValidationResult.success()

def validate_route_for_role(role: str, route: str) -> ValidationResult:
    try:
        role_enum = RequesterRole(role)
    except ValueError:
        return ValidationResult.failure('unknown role')
    if route == 'SHARE_CODE' and role_enum not in SHARE_CODE_ROLES:
        return ValidationResult.failure('role not permitted to use share-code route')
    if route == 'DOCUMENT' and role_enum not in AUTHORITY_ROLES:
        return ValidationResult.failure('role not permitted to use document route')
    if route not in ('SHARE_CODE', 'DOCUMENT'):
        return ValidationResult.failure('unknown verification route')
    return ValidationResult.success()

def validate_confirmations(lawful: bool, data_protection: bool, non_discriminatory: bool) -> ValidationResult:
    if not (lawful and data_protection and non_discriminatory):
        return ValidationResult.failure('required confirmations missing')
    return ValidationResult.success()
