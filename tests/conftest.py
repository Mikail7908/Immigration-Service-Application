import json
import sys
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.logging_setup import configure_logging
from src.repository.file_repository import FileRepository
from src.repository.audit_repository import AuditRepository
from src.services.share_code_service import ShareCodeService
from src.services.authorisation_service import AuthorisationService
from src.services.verification_service import VerificationService
from src.services.analytics_service import AnalyticsService
SEED_INDIVIDUALS = [{'individual_id': 'IND-0001', 'full_name': 'Amelia Hart', 'date_of_birth': '1990-04-12', 'passport_number': 'P1234567A', 'permit_number': 'PA1234567', 'status_type': 'SETTLED', 'status_valid_until': None, 'right_to_work': True, 'right_to_rent': True, 'right_to_study': True, 'entry_permitted': True, 'conditions': []}, {'individual_id': 'IND-0002', 'full_name': 'Noah Bennett', 'date_of_birth': '1995-09-30', 'passport_number': 'K9876543B', 'permit_number': 'PB7654321', 'status_type': 'LIMITED_LEAVE', 'status_valid_until': '2027-03-31', 'right_to_work': True, 'right_to_rent': True, 'right_to_study': False, 'entry_permitted': True, 'conditions': ['max 20 hours']}, {'individual_id': 'IND-0004', 'full_name': 'Tomasz Kowalski', 'date_of_birth': '1988-07-22', 'passport_number': 'Z1112223C', 'permit_number': None, 'status_type': 'EXPIRED_LEAVE', 'status_valid_until': '2025-12-01', 'right_to_work': False, 'right_to_rent': False, 'right_to_study': False, 'entry_permitted': False, 'conditions': []}]
SEED_ORGS = [{'organisation_id': 'ORG-EMP-01', 'name': 'Acme', 'role': 'EMPLOYER', 'email_domain': 'acme.co.uk', 'authorised': True}, {'organisation_id': 'ORG-LND-01', 'name': 'Riverside', 'role': 'LANDLORD', 'email_domain': 'riverside.com', 'authorised': True}, {'organisation_id': 'ORG-EDU-01', 'name': 'Northbridge', 'role': 'EDUCATION', 'email_domain': 'northbridge.ac.uk', 'authorised': True}, {'organisation_id': 'ORG-BDR-01', 'name': 'Border Force', 'role': 'BORDER_CONTROL', 'email_domain': 'borderforce.gov.uk', 'authorised': True}, {'organisation_id': 'ORG-LAW-01', 'name': 'Metro Police', 'role': 'LAW_ENFORCEMENT', 'email_domain': 'met.police.uk', 'authorised': True}, {'organisation_id': 'ORG-EMP-99', 'name': 'Suspended', 'role': 'EMPLOYER', 'email_domain': 'suspended.com', 'authorised': False}]

@pytest.fixture(autouse=True, scope='session')
def _configure_logging(tmp_path_factory):
    configure_logging(log_dir=str(tmp_path_factory.mktemp('logs')))

@pytest.fixture
def tmp_data_dir(tmp_path):
    (tmp_path / 'individuals.json').write_text(json.dumps(SEED_INDIVIDUALS))
    (tmp_path / 'organisations.json').write_text(json.dumps(SEED_ORGS))
    (tmp_path / 'share_codes.json').write_text('[]')
    return tmp_path

@pytest.fixture
def repo(tmp_data_dir):
    return FileRepository(str(tmp_data_dir))

@pytest.fixture
def audit(tmp_path):
    return AuditRepository(str(tmp_path / 'audit.jsonl'))

@pytest.fixture
def services(repo, audit):
    authoriser = AuthorisationService(repo)
    sc = ShareCodeService(repo, audit)
    ver = VerificationService(repo, audit, authoriser)
    ana = AnalyticsService(audit)
    return {'repo': repo, 'audit': audit, 'authoriser': authoriser, 'share_code': sc, 'verify': ver, 'analytics': ana}
