"""White-box tests for AuthorisationService.

Targeted decision paths (each return statement is covered):
  1. missing confirmations
  2. malformed email
  3. unknown organisation
  4. unauthorised organisation
  5. mismatched role
  6. mismatched email domain
  7. success
"""

def test_success(services):
    result, org = services['authoriser'].authorise('ORG-EMP-01', 'hr@acme.co.uk', 'EMPLOYER', True, True, True)
    assert result.ok
    assert org.organisation_id == 'ORG-EMP-01'

def test_missing_confirmation(services):
    result, _ = services['authoriser'].authorise('ORG-EMP-01', 'hr@acme.co.uk', 'EMPLOYER', False, True, True)
    assert not result.ok
    assert 'confirmations' in result.reason

def test_bad_email(services):
    result, _ = services['authoriser'].authorise('ORG-EMP-01', 'not-an-email', 'EMPLOYER', True, True, True)
    assert not result.ok

def test_unknown_org(services):
    result, _ = services['authoriser'].authorise('ORG-DOES-NOT-EXIST', 'hr@acme.co.uk', 'EMPLOYER', True, True, True)
    assert not result.ok
    assert 'not recognised' in result.reason

def test_unauthorised_org(services):
    result, _ = services['authoriser'].authorise('ORG-EMP-99', 'hr@suspended.com', 'EMPLOYER', True, True, True)
    assert not result.ok
    assert 'not authorised' in result.reason

def test_role_mismatch(services):
    result, _ = services['authoriser'].authorise('ORG-EMP-01', 'hr@acme.co.uk', 'LANDLORD', True, True, True)
    assert not result.ok
    assert 'role' in result.reason

def test_domain_mismatch(services):
    result, _ = services['authoriser'].authorise('ORG-EMP-01', 'hr@evil.com', 'EMPLOYER', True, True, True)
    assert not result.ok
    assert 'domain' in result.reason
