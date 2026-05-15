import json
from typing import Optional
from ..domain.enums import VerificationRoute
from ..domain.models import VerificationRequest
from ..repository.file_repository import FileRepository
from ..repository.audit_repository import AuditRepository
from ..services.share_code_service import ShareCodeService
from ..services.authorisation_service import AuthorisationService
from ..services.verification_service import VerificationService
from ..services.analytics_service import AnalyticsService
from ..logging_setup import get_logger

class ConsoleApp:

    def __init__(self, data_dir: str='data', audit_path: str='logs/audit.jsonl'):
        self.repo = FileRepository(data_dir)
        self.audit = AuditRepository(audit_path)
        self.authoriser = AuthorisationService(self.repo)
        self.share_code_svc = ShareCodeService(self.repo, self.audit)
        self.verify_svc = VerificationService(self.repo, self.audit, self.authoriser)
        self.analytics_svc = AnalyticsService(self.audit)
        self.log = get_logger()

    def _prompt(self, label: str, default: Optional[str]=None) -> str:
        suffix = f' [{default}]' if default else ''
        raw = input(f'{label}{suffix}: ').strip()
        return raw or (default or '')

    def _prompt_yes_no(self, label: str) -> bool:
        return self._prompt(f'{label} (y/n)', 'n').lower().startswith('y')

    def _print_outcome(self, outcome) -> None:
        print('\n--- Verification Outcome ---')
        print(json.dumps(outcome.to_dict(), indent=2))
        print('----------------------------\n')

    def menu_generate_share_code(self) -> None:
        print('\n[Individual] Generate share code')
        individual_id = self._prompt('Your individual ID')
        purpose = self._prompt('Purpose (EMPLOYMENT/ACCOMMODATION/EDUCATION)')
        try:
            ttl = int(self._prompt('Time-to-live in hours', '24'))
        except ValueError:
            print('Invalid TTL; using 24.')
            ttl = 24
        sc = self.share_code_svc.generate(individual_id, purpose, ttl)
        if sc is None:
            print('Share code generation rejected (unknown individual or purpose).')
        else:
            print(f'\nShare code: {sc.code}')
            print(f'Expires at: {sc.expires_at}\n')

    def menu_verify_share_code(self) -> None:
        print('\n[Organisation] Verify by share code')
        role = self._prompt('Role (EMPLOYER/LANDLORD/EDUCATION)')
        purpose = self._prompt('Declared purpose (EMPLOYMENT/ACCOMMODATION/EDUCATION)')
        org_id = self._prompt('Organisation ID')
        org_email = self._prompt('Organisation email')
        code = self._prompt('Share code').upper()
        dob = self._prompt('Individual date of birth (YYYY-MM-DD)')
        c1 = self._prompt_yes_no('Confirm: lawful purpose')
        c2 = self._prompt_yes_no('Confirm: data protection obligations accepted')
        c3 = self._prompt_yes_no('Confirm: request is not discriminatory')
        req = VerificationRequest(organisation_id=org_id, organisation_email=org_email, role=role, route=VerificationRoute.SHARE_CODE.value, declared_purpose=purpose, confirm_lawful_purpose=c1, confirm_data_protection=c2, confirm_non_discriminatory=c3, share_code=code, date_of_birth=dob)
        self._print_outcome(self.verify_svc.verify(req))

    def menu_verify_document(self) -> None:
        print('\n[Authority] Verify by travel/identity document')
        role = self._prompt('Role (BORDER_CONTROL/LAW_ENFORCEMENT)')
        purpose = self._prompt('Declared purpose (BORDER_ENTRY/LAW_ENFORCEMENT)')
        org_id = self._prompt('Authority organisation ID')
        org_email = self._prompt('Authority email')
        doc_kind = self._prompt('Document type (passport/permit)', 'passport').lower()
        passport = permit = None
        if doc_kind == 'passport':
            passport = self._prompt('Passport number')
        else:
            permit = self._prompt('Permit number')
        c1 = self._prompt_yes_no('Confirm: lawful purpose')
        c2 = self._prompt_yes_no('Confirm: data protection obligations accepted')
        c3 = self._prompt_yes_no('Confirm: request is not discriminatory')
        req = VerificationRequest(organisation_id=org_id, organisation_email=org_email, role=role, route=VerificationRoute.DOCUMENT.value, declared_purpose=purpose, confirm_lawful_purpose=c1, confirm_data_protection=c2, confirm_non_discriminatory=c3, passport_number=passport, permit_number=permit)
        self._print_outcome(self.verify_svc.verify(req))

    def menu_analytics(self) -> None:
        print('\n[Operational] Aggregated analytics')
        print(json.dumps(self.analytics_svc.summary(), indent=2))

    def menu_list_seed(self) -> None:
        print('\n[Reference] Seeded individuals (IDs only):')
        for i in self.repo.list_individuals():
            print(f'  - {i.individual_id}  ({i.status_type})')
        print('\n[Reference] Seeded organisations:')
        for o in self.repo.list_organisations():
            print(f'  - {o.organisation_id} :: {o.name} :: role={o.role} :: domain={o.email_domain} :: authorised={o.authorised}')

    def run(self) -> None:
        while True:
            print('\n=== Immigration Verification Service (Prototype) ===')
            print('1. Generate share code (individual)')
            print('2. Verify by share code (employer/landlord/education)')
            print('3. Verify by document (border control / law enforcement)')
            print('4. View operational analytics')
            print('5. List seeded individuals and organisations')
            print('0. Exit')
            choice = self._prompt('Select', '0')
            if choice == '1':
                self.menu_generate_share_code()
            elif choice == '2':
                self.menu_verify_share_code()
            elif choice == '3':
                self.menu_verify_document()
            elif choice == '4':
                self.menu_analytics()
            elif choice == '5':
                self.menu_list_seed()
            elif choice == '0':
                print('Goodbye.')
                return
            else:
                print('Unknown selection.')
