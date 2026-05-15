"""White-box tests for ShareCodeService.

Targeted decision paths:
  - successful generation (happy path)
  - rejection: unknown purpose (Purpose enum raises ValueError)
  - rejection: unknown individual (find_individual returns None)
  - revoke success and revoke-on-missing
"""
from src.validation.validators import SHARE_CODE_PATTERN

def test_generate_happy_path(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT', ttl_hours=2)
    assert sc is not None
    assert SHARE_CODE_PATTERN.match(sc.code)
    assert sc.individual_id == 'IND-0001'
    assert sc.purpose == 'EMPLOYMENT'
    assert sc.revoked is False

def test_generate_unknown_purpose_returns_none(services):
    assert services['share_code'].generate('IND-0001', 'GARDENING') is None

def test_generate_unknown_individual_returns_none(services):
    assert services['share_code'].generate('IND-NOPE', 'EMPLOYMENT') is None

def test_generate_writes_audit_entry(services):
    services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    entries = services['audit'].read_all()
    assert any((e['event_type'] == 'SHARE_CODE_GENERATED' for e in entries))

def test_revoke_existing(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    assert services['share_code'].revoke(sc.code) is True
    stored = services['repo'].find_share_code(sc.code)
    assert stored.revoked is True

def test_revoke_missing_returns_false(services):
    assert services['share_code'].revoke('NOTACODE9') is False
