"""White-box tests for validators.

Intent: each validator contains multiple decision branches (missing input, format
mismatch, semantic mismatch). These tests cover every branch - both the success
path and each documented failure path - so that adding a new branch later forces
a deliberate test update
"""
from datetime import datetime, timedelta, timezone
import pytest
from src.validation.validators import validate_share_code_format, validate_dob_format, validate_passport_format, validate_permit_format, validate_email_format, validate_email_domain, validate_share_code_expiry, validate_purpose_for_role, validate_route_for_role, validate_confirmations

class TestShareCodeFormat:

    def test_valid(self):
        assert validate_share_code_format('ABCDE1234').ok

    def test_missing(self):
        assert not validate_share_code_format('').ok
        assert not validate_share_code_format(None).ok

    def test_wrong_length(self):
        assert not validate_share_code_format('ABC').ok

    def test_lowercase_rejected(self):
        assert not validate_share_code_format('abcde1234').ok

    def test_punctuation_rejected(self):
        assert not validate_share_code_format('ABCDE-123').ok

class TestDobFormat:

    def test_valid(self):
        assert validate_dob_format('1990-04-12').ok

    def test_missing(self):
        assert not validate_dob_format(None).ok

    def test_pattern_mismatch(self):
        assert not validate_dob_format('12-04-1990').ok

    def test_pattern_ok_but_unreal_date(self):
        assert not validate_dob_format('1990-13-40').ok

class TestPassportPermit:

    def test_passport_valid(self):
        assert validate_passport_format('P1234567A').ok

    def test_passport_short(self):
        assert not validate_passport_format('P1').ok

    def test_passport_missing(self):
        assert not validate_passport_format(None).ok

    def test_permit_valid(self):
        assert validate_permit_format('PA1234567').ok

    def test_permit_wrong_prefix(self):
        assert not validate_permit_format('XA1234567').ok

    def test_permit_missing(self):
        assert not validate_permit_format(None).ok

class TestEmail:

    def test_valid(self):
        assert validate_email_format('hr@acme.co.uk').ok

    def test_invalid_no_at(self):
        assert not validate_email_format('hr.acme.co.uk').ok

    def test_missing(self):
        assert not validate_email_format(None).ok

    def test_domain_match(self):
        assert validate_email_domain('hr@acme.co.uk', 'acme.co.uk').ok

    def test_domain_mismatch(self):
        assert not validate_email_domain('hr@evil.com', 'acme.co.uk').ok

    def test_domain_match_case_insensitive(self):
        assert validate_email_domain('hr@ACME.co.uk', 'acme.co.uk').ok

class TestExpiry:

    def test_valid_future(self):
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        assert validate_share_code_expiry(future).ok

    def test_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        assert not validate_share_code_expiry(past).ok

    def test_malformed(self):
        assert not validate_share_code_expiry('not-a-date').ok

    def test_naive_datetime_treated_as_utc(self):
        future_naive = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        assert validate_share_code_expiry(future_naive).ok

class TestPurposeAndRoute:

    @pytest.mark.parametrize('role,purpose,expected', [('EMPLOYER', 'EMPLOYMENT', True), ('EMPLOYER', 'ACCOMMODATION', False), ('LANDLORD', 'ACCOMMODATION', True), ('LANDLORD', 'EMPLOYMENT', False), ('EDUCATION', 'EDUCATION', True), ('BORDER_CONTROL', 'BORDER_ENTRY', True), ('LAW_ENFORCEMENT', 'LAW_ENFORCEMENT', True)])
    def test_purpose_for_role(self, role, purpose, expected):
        assert validate_purpose_for_role(role, purpose).ok == expected

    def test_unknown_role(self):
        assert not validate_purpose_for_role('MAYOR', 'EMPLOYMENT').ok

    def test_unknown_purpose(self):
        assert not validate_purpose_for_role('EMPLOYER', 'GARDENING').ok

    @pytest.mark.parametrize('role,route,expected', [('EMPLOYER', 'SHARE_CODE', True), ('LANDLORD', 'SHARE_CODE', True), ('EDUCATION', 'SHARE_CODE', True), ('BORDER_CONTROL', 'SHARE_CODE', False), ('BORDER_CONTROL', 'DOCUMENT', True), ('LAW_ENFORCEMENT', 'DOCUMENT', True), ('EMPLOYER', 'DOCUMENT', False)])
    def test_route_for_role(self, role, route, expected):
        assert validate_route_for_role(role, route).ok == expected

    def test_route_unknown(self):
        assert not validate_route_for_role('EMPLOYER', 'TELEPATHY').ok

class TestConfirmations:

    def test_all_true(self):
        assert validate_confirmations(True, True, True).ok

    @pytest.mark.parametrize('a,b,c', [(False, True, True), (True, False, True), (True, True, False), (False, False, False)])
    def test_any_false_rejected(self, a, b, c):
        assert not validate_confirmations(a, b, c).ok
