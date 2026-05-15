"""White-box tests for AnalyticsService.

Confirms aggregation correctness AND the privacy constraint: no personal
information (individual_id, share code, passport, DOB) ever appears in the
analytics summary, regardless of what is in the audit log.
"""
import json
from src.domain.enums import VerificationRoute, OutcomeStatus
from src.domain.models import VerificationRequest

def _request_for(svc, code):
    return VerificationRequest(organisation_id='ORG-EMP-01', organisation_email='hr@acme.co.uk', role='EMPLOYER', route=VerificationRoute.SHARE_CODE.value, declared_purpose='EMPLOYMENT', confirm_lawful_purpose=True, confirm_data_protection=True, confirm_non_discriminatory=True, share_code=code, date_of_birth='1990-04-12')

def test_summary_counts_attempts_and_generations(services):
    sc1 = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    sc2 = services['share_code'].generate('IND-0002', 'ACCOMMODATION')
    services['verify'].verify(_request_for(services, sc1.code))
    services['verify'].verify(_request_for(services, sc1.code))
    s = services['analytics'].summary()
    assert s['total_share_codes_generated'] == 2
    assert s['total_verification_attempts'] == 2
    assert s['requests_by_organisation']['ORG-EMP-01'] == 2
    assert s['requests_by_role']['EMPLOYER'] == 2
    assert s['requests_by_declared_purpose']['EMPLOYMENT'] == 2
    assert s['share_codes_generated_by_purpose']['EMPLOYMENT'] == 1
    assert s['share_codes_generated_by_purpose']['ACCOMMODATION'] == 1

def test_summary_counts_failures(services):
    services['verify'].verify(_request_for(services, 'NOTACODE9'))
    s = services['analytics'].summary()
    assert s['total_validation_failures'] >= 1
    assert s['requests_by_outcome'][OutcomeStatus.NOT_FOUND.value] == 1

def test_summary_contains_no_personal_information(services):
    sc = services['share_code'].generate('IND-0001', 'EMPLOYMENT')
    services['verify'].verify(_request_for(services, sc.code))
    blob = json.dumps(services['analytics'].summary())
    assert 'IND-0001' not in blob
    assert sc.code not in blob
    assert '1990-04-12' not in blob

def test_empty_summary_when_no_activity(services):
    s = services['analytics'].summary()
    assert s['total_verification_attempts'] == 0
    assert s['total_share_codes_generated'] == 0
    assert s['requests_by_organisation'] == {}
