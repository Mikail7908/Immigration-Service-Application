"""White-box tests for VerificationService.

These tests exercise each decision branch in verify() / _verify_share_code() /
_verify_document() / _project_outcome() - covering both happy paths and every
documented failure path. Identical inputs must yield identical outputs, so each
test reuses the same fixture-driven setup.
"""
from datetime import datetime, timedelta, timezone
from src.domain.enums import VerificationRoute, OutcomeStatus
from src.domain.models import VerificationRequest, ShareCode

def _employer_share_code_request(code, dob='1990-04-12', purpose='EMPLOYMENT', confirms=(True, True, True)):
    return VerificationRequest(organisation_id='ORG-EMP-01', organisation_email='hr@acme.co.uk', role='EMPLOYER', route=VerificationRoute.SHARE_CODE.value, declared_purpose=purpose, confirm_lawful_purpose=confirms[0], confirm_data_protection=confirms[1], confirm_non_discriminatory=confirms[2], share_code=code, date_of_birth=dob)

def test_share_code_employer_eligible(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    out = services['verify'].verify(_employer_share_code_request(sc.code))
    assert out.status == OutcomeStatus.ELIGIBLE.value
    assert out.details['right_to_work'] is True
    assert 'status_type' not in out.details
    assert 'entry_permitted' not in out.details

def test_share_code_landlord_eligible(services):
    sc = services['share_code'].generate('IND-0002', 'ACCOMMODATION')
    req = VerificationRequest(organisation_id='ORG-LND-01', organisation_email='agent@riverside.com', role='LANDLORD', route=VerificationRoute.SHARE_CODE.value, declared_purpose='ACCOMMODATION', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, share_code=sc.code, date_of_birth='1995-09-30')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.ELIGIBLE.value
    assert out.details['right_to_rent'] is True

def test_document_border_control_eligible(services):
    req = VerificationRequest(organisation_id='ORG-BDR-01', organisation_email='officer@borderforce.gov.uk', role='BORDER_CONTROL', route=VerificationRoute.DOCUMENT.value, declared_purpose='BORDER_ENTRY', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, passport_number='P1234567A')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.ELIGIBLE.value
    assert out.details['entry_permitted'] is True

def test_document_law_enforcement_by_permit(services):
    req = VerificationRequest(organisation_id='ORG-LAW-01', organisation_email='officer@met.police.uk', role='LAW_ENFORCEMENT', route=VerificationRoute.DOCUMENT.value, declared_purpose='LAW_ENFORCEMENT', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, permit_number='PB7654321')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.ELIGIBLE.value
    assert 'status_type' in out.details

def test_share_code_not_eligible_expired_leave(services):
    sc = services['share_code'].generate('IND-0004', 'EMPLOYMENT')
    out = services['verify'].verify(_employer_share_code_request(sc.code, dob='1988-07-22'))
    assert out.status == OutcomeStatus.NOT_ELIGIBLE.value
    assert out.details['right_to_work'] is False

def test_missing_confirmations(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    out = services['verify'].verify(_employer_share_code_request(sc.code, confirms=(False, True, True)))
    assert out.status == OutcomeStatus.CONFIRMATIONS_MISSING.value

def test_unauthorised_organisation(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    req = _employer_share_code_request(sc.code)
    req.organisation_id = 'ORG-EMP-99'
    req.organisation_email = 'hr@suspended.com'
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.UNAUTHORISED.value

def test_purpose_role_mismatch(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    out = services['verify'].verify(_employer_share_code_request(sc.code, purpose='ACCOMMODATION'))
    assert out.status == OutcomeStatus.PURPOSE_MISMATCH.value

def test_route_role_mismatch(services):
    req = VerificationRequest(organisation_id='ORG-EMP-01', organisation_email='hr@acme.co.uk', role='EMPLOYER', route=VerificationRoute.DOCUMENT.value, declared_purpose='EMPLOYMENT', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, passport_number='P1234567A')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.UNAUTHORISED.value

def test_share_code_format_invalid(services):
    out = services['verify'].verify(_employer_share_code_request('bad'))
    assert out.status == OutcomeStatus.INVALID_INPUT.value

def test_share_code_not_found(services):
    out = services['verify'].verify(_employer_share_code_request('ZZZZ99999'))
    assert out.status == OutcomeStatus.NOT_FOUND.value

def test_share_code_revoked(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    services['share_code'].revoke(sc.code)
    out = services['verify'].verify(_employer_share_code_request(sc.code))
    assert out.status == OutcomeStatus.EXPIRED.value

def test_share_code_expired(services):
    expired = ShareCode(code='EXPIRED99', individual_id='IND-0001', purpose='EMPLOYMENT', created_at=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat(), expires_at=(datetime.now(timezone.utc) - timedelta(days=1)).isoformat(), revoked=False)
    services['repo'].save_share_code(expired)
    out = services['verify'].verify(_employer_share_code_request('EXPIRED99'))
    assert out.status == OutcomeStatus.EXPIRED.value

def test_share_code_purpose_mismatch_against_stored(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    bad = ShareCode(code='MISMATCH9', individual_id='IND-0001', purpose='ACCOMMODATION', created_at=datetime.now(timezone.utc).isoformat(), expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
    services['repo'].save_share_code(bad)
    out = services['verify'].verify(_employer_share_code_request('MISMATCH9'))
    assert out.status == OutcomeStatus.PURPOSE_MISMATCH.value

def test_share_code_dob_mismatch(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    out = services['verify'].verify(_employer_share_code_request(sc.code, dob='2000-01-01'))
    assert out.status == OutcomeStatus.IDENTITY_MISMATCH.value

def test_document_passport_invalid_format(services):
    req = VerificationRequest(organisation_id='ORG-BDR-01', organisation_email='officer@borderforce.gov.uk', role='BORDER_CONTROL', route=VerificationRoute.DOCUMENT.value, declared_purpose='BORDER_ENTRY', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, passport_number='bad')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.INVALID_INPUT.value

def test_document_no_identifier_provided(services):
    req = VerificationRequest(organisation_id='ORG-BDR-01', organisation_email='officer@borderforce.gov.uk', role='BORDER_CONTROL', route=VerificationRoute.DOCUMENT.value, declared_purpose='BORDER_ENTRY', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True)
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.INVALID_INPUT.value

def test_document_not_found(services):
    req = VerificationRequest(organisation_id='ORG-BDR-01', organisation_email='officer@borderforce.gov.uk', role='BORDER_CONTROL', route=VerificationRoute.DOCUMENT.value, declared_purpose='BORDER_ENTRY', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, passport_number='X9999999Z')
    out = services['verify'].verify(req)
    assert out.status == OutcomeStatus.NOT_FOUND.value

def test_determinism_same_input_same_outcome(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    out1 = services['verify'].verify(_employer_share_code_request(sc.code))
    out2 = services['verify'].verify(_employer_share_code_request(sc.code))
    assert out1.status == out2.status
    assert out1.details == out2.details
