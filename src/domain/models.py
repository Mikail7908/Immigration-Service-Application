from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

@dataclass
class Individual:
    individual_id: str
    full_name: str
    date_of_birth: str
    passport_number: Optional[str]
    permit_number: Optional[str]
    status_type: str
    status_valid_until: Optional[str]
    right_to_work: bool
    right_to_rent: bool
    right_to_study: bool
    entry_permitted: bool
    conditions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ShareCode:
    code: str
    individual_id: str
    purpose: str
    created_at: str
    expires_at: str
    revoked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Organisation:
    organisation_id: str
    name: str
    role: str
    email_domain: str
    authorised: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class VerificationRequest:
    organisation_id: str
    organisation_email: str
    role: str
    route: str
    declared_purpose: str
    confirm_lawful_purpose: bool
    confirm_data_protection: bool
    confirm_non_discriminatory: bool
    share_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    passport_number: Optional[str] = None
    permit_number: Optional[str] = None

@dataclass
class VerificationOutcome:
    status: str
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
