from datetime import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from .views import *


# Create your tests here.


class TestCrLcs(TestCase):
    def setUp(self):
        get_user_model().objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        self.bank = Bank(name="tempBank")
        self.bank.save()
        self.bank_employee = BankEmployee(bank=self.bank, email="emp@tempBank.com", name="Emp")
        self.bank_employee.save()
        get_user_model().objects.create_user('emp@tempBank.com', 'emp@tempBank.com', 'emp')

    def tearDown(self):
        self.client.logout()

    def test_errors(self):
        response = self.client.delete(f"/lc/by_bank/{self.bank.id}/")
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, b"This endpoint only supports GET, POST")
        response = self.client.get('/lc/by_bank/0/')
        self.assertEquals(response.status_code, 404)
        response = self.client.get(f'/lc/by_bank/{self.bank.id}/')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.content, b"Must be logged in to see your bank's issued LCs")
        response = self.client.post(f'/lc/by_bank/{self.bank.id}/')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.content, b"Must be logged in to create an LC")
        self.client.login(username='temporary', password='temporary')
        response = self.client.get(f'/lc/by_bank/{self.bank.id}/')
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.content, b"Must be an employee of the bank to see all the LCs this bank has issued")
        response = self.client.post(f'/lc/by_bank/{self.bank.id}/')
        self.assertEquals(response.status_code, 400)
        self.assertEquals(response.content, b"missing or malformed request body")
        response = self.client.post(f'/lc/by_bank/{self.bank.id}/', {}, content_type="application/json")
        self.assertEquals(response.status_code, 403)
        self.assertEquals(response.content,
                          b"You may only create LCs with the bank of the ID at this endpoint by being a member of "
                          b"this bank, or by being a business requesting an LC from this bank")

    def test_post(self):
        self.maxDiff = None
        self.client.login(username="emp@tempBank.com", password='emp')
        response = self.client.post(f"/lc/by_bank/{self.bank.id}/", {'applicant_name': 'New Applicant',
                                                                     'applicant_employee_contact': 'newApp@newApp.com'},
                                    content_type="application/json")
        self.assertEquals(len(DigitalLC.objects.filter(issuer=self.bank)), 1)
        created_lc = DigitalLC.objects.get(issuer=self.bank)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].subject, "Emp has started your LC for you on Bountium!")
        self.assertEquals(mail.outbox[0].from_email, "steve@bountium.org")
        self.assertEquals(mail.outbox[0].to, ["newApp@newApp.com"])
        self.assertEquals(mail.outbox[0].body,
                          f"1. Set your business up at https://app.bountium.org/business/register, 2. Fill out your "
                          f"app at https://app.bountium.org/business/finishApp/{created_lc.id}")
        self.assertEquals(response.status_code, 200)
        # self.assertEquals(json.loads(response.content)['created_lc'], created_lc.to_dict())
        self.assertEquals(json.loads(response.content),
                          json.loads(JsonResponse({'success': True, 'created_lc': created_lc.to_dict()}).content))


class TestModels(TestCase):
    # @mock.patch('lc.views.datetime')
    def setUp(self):
        self.maxDiff = None
        # mocked_datetime.now.return_value = datetime.date(2020, 1, 1)
        self.sdn = SpeciallyDesignatedNational(name="testSDN", cleansed_name="testSDN", type="individual")
        self.sdn.save()
        self.sdn_address1 = SpeciallyDesignatedNationalAddress(sdn=self.sdn, address="1 Hey Way",
                                                               address_group="Bermuda", country="USA")
        self.sdn_address1.save()
        self.sdn_alternate1 = SpeciallyDesignatedNationalAlternate(sdn=self.sdn, type="aka", name="Broo",
                                                                   cleansed_name="Bro")
        self.sdn_alternate1.save()

        issuer = Bank(name="Best Bank")
        issuer.save()
        client = Business(name="Iona Imports", address="48 Sutton Road, Needham, MA")
        client.save()
        beneficiary = Business(name="Delvest", address="234 Main St, Bogota, Venezuela", country="Venezuela")
        beneficiary.save()
        account_party = Business(name="AccountParty McAccountParty's Accounts", address="366 Auburndale St, Newton, MA")
        account_party.save()
        advising_bank = Bank(name="Second Best Bank")
        advising_bank.save()

        lc_dict = {
            "issuer": issuer,
            "client": client,
            "beneficiary": beneficiary,
            "account_party": account_party,
            "advising_bank": advising_bank,
            "application_date": datetime.datetime(2020, 7, 7, 23, 23, 10, 981670),
            "credit_delivery_means": 'Courier',
            "credit_amt_verbal": 'Sixty Million',
            "credit_amt": 60000000,
            "cash_secure": 50,
            "currency_denomination": 'USD',
            "applicant_and_ap_j_and_s_obligated": True,
            "exchange_rate_tolerance": 0.01,
            "hts_code": "2204.10.11",
            "purchased_item": 'Champagne',
            "unit_of_measure": 'liters',
            "units_purchased": 600,
            "unit_error_tolerance": 0.0002,
            "confirmation_means": 'Confirmation by a bank selected by the beneficiary',
            "paying_other_banks_fees": client,
            "credit_expiry_location": advising_bank,
            "expiration_date": '2020-04-24',
            "draft_presentation_date": '2020-04-22',
            "drafts_invoice_value": 1.00,
            "credit_availability": 'Payment on sight',
            "paying_acceptance_and_discount_charges": client,
            "deferred_payment_date": '2020-04-26',
            "merch_charge_location": 'Boston',
            "late_charge_date": '2020-04-25',
            "charge_transportation_location": 'Needham',
            "incoterms_to_show": '["EXW", "CPT"]',
            "named_place_of_destination": 'Needham',
            "doc_reception_notifees": 'My customer Freddys Drinks in Newton',
            "other_instructions": 'No items from Israel.',
            "merch_description": 'Class A champagne aged for 200 years',
            "other_data": {
                'An extra question on the bank\'s application would go here': 'and this is what the applicant responded'
            }
        }

        self.lc = DigitalLC(**lc_dict)
        self.lc.save()
        client_emp = client.businessemployee_set.create(name="Steve", title="Owner", email="steve@ii.com")
        client_emp.save()
        self.lc.tasked_client_employees.add(client_emp)
        bene_emp = beneficiary.businessemployee_set.create(name="Steve", title="Owner", email="steve@delvest.com")
        bene_emp.save()
        self.lc.tasked_beneficiary_employees.add(bene_emp)
        issuer_emp = issuer.bankemployee_set.create(name="Steve", title="Owner", email="steve@bb.com")
        issuer_emp.save()
        self.lc.tasked_issuer_employees.add(issuer_emp)
        ap_emp = account_party.businessemployee_set.create(name="AccountParty McAccountParty", title="Owner",
                                                           email="accountparty@ama.com")
        ap_emp.save()
        self.lc.tasked_account_party_employees.add(ap_emp)
        ad_emp = advising_bank.bankemployee_set.create(name="Advisey McAdvisey", title="Owner", email="advisey@sbb.com")
        ad_emp.save()
        self.lc.tasked_advising_bank_employees.add(ad_emp)

        required_values = (
                "Version required: Original"
                + "\nIncoterms to show: " + self.lc.incoterms_to_show
                + "\nNamed place of destination: " + self.lc.named_place_of_destination
        )

        test_ci = CommercialInvoiceRequirement(
                for_lc=self.lc,
                doc_name="Commercial Invoice",
                type="commercial_invoice",
                required_values=required_values,
                due_date=self.lc.draft_presentation_date
        )
        test_ci.save()

        test_multiomodal_bl = MultimodalTransportDocumentRequirement(
                for_lc=self.lc,
                doc_name="Multimodal Bill of Lading",
                type="multimodal_bl",
                due_date=self.lc.draft_presentation_date,
                required_values="Marked EXW, CPT"
        )
        test_multiomodal_bl.save()

        self.lc.documentaryrequirement_set.create(
                doc_name="Packing List",
                required_values="600 Bottles packed, Incoterms are correct, named place is correct.",
                due_date="2020-04-21"
        )

        ofac(beneficiary.name, self.lc)
        self.lc.sanction_auto_message = sanction_approval(beneficiary.country, client.country)
        self.lc.import_license_message = import_license(self.lc)
        believable_price_of_goods(self.lc.hts_code, self.lc.unit_of_measure)
        boycott_phrases = boycott_language(self.lc.other_instructions)
        for phrase in boycott_phrases:
            BoycottLanguage(phrase=phrase, source='other_instructions', lc=self.lc).save()

        self.lc.save()

    def test_sdn(self):
        self.assertEquals(self.sdn.to_dict(),
                          {'id': self.sdn.id, 'name': "testSDN", 'cleansed_name': "testSDN", 'type': "individual",
                           'program': None, 'title': None, 'call_sign': None, 'vessel_type': None, 'tonnage': None,
                           'grt': None, 'vessel_flag': None, 'vessel_owner': None, 'remarks': None, 'addresses': [
                              {'id': self.sdn_address1.id, 'sdn_id': self.sdn.id, 'address': "1 Hey Way",
                               'address_group': "Bermuda", 'country': "USA", 'remarks': None}], 'aliases': [
                              {'id': self.sdn_alternate1.id, 'sdn_id': self.sdn.id, 'type': "aka", 'name': "Broo",
                               'cleansed_name': "Bro", 'remarks': None}]})

        self.assertEquals(len(self.sdn._meta.get_fields()), 16)

        self.assertEquals(self.sdn._meta.get_field("name").max_length, 350)
        self.assertEquals(self.sdn._meta.get_field("name").blank, True)
        self.assertEquals(self.sdn._meta.get_field("name").default, "")

        self.assertEquals(self.sdn._meta.get_field("cleansed_name").max_length, 350)
        self.assertEquals(self.sdn._meta.get_field("cleansed_name").blank, True)
        self.assertEquals(self.sdn._meta.get_field("cleansed_name").default, "")

        self.assertEquals(self.sdn._meta.get_field("type").max_length, 12)
        self.assertEquals(self.sdn._meta.get_field("type").blank, True)
        self.assertEquals(self.sdn._meta.get_field("type").default, None)
        self.assertEquals(self.sdn._meta.get_field("type").null, True)

        self.assertEquals(self.sdn._meta.get_field("program").max_length, 200)
        self.assertEquals(self.sdn._meta.get_field("program").blank, True)
        self.assertEquals(self.sdn._meta.get_field("program").default, None)
        self.assertEquals(self.sdn._meta.get_field("program").null, True)

        self.assertEquals(self.sdn._meta.get_field("title").max_length, 200)
        self.assertEquals(self.sdn._meta.get_field("title").blank, True)
        self.assertEquals(self.sdn._meta.get_field("title").default, None)
        self.assertEquals(self.sdn._meta.get_field("title").null, True)

        self.assertEquals(self.sdn._meta.get_field("call_sign").max_length, 8)
        self.assertEquals(self.sdn._meta.get_field("call_sign").blank, True)
        self.assertEquals(self.sdn._meta.get_field("call_sign").default, None)
        self.assertEquals(self.sdn._meta.get_field("call_sign").null, True)

        self.assertEquals(self.sdn._meta.get_field("vessel_type").max_length, 25)
        self.assertEquals(self.sdn._meta.get_field("vessel_type").blank, True)
        self.assertEquals(self.sdn._meta.get_field("vessel_type").default, None)
        self.assertEquals(self.sdn._meta.get_field("vessel_type").null, True)

        self.assertEquals(self.sdn._meta.get_field("tonnage").max_length, 14)
        self.assertEquals(self.sdn._meta.get_field("tonnage").blank, True)
        self.assertEquals(self.sdn._meta.get_field("tonnage").default, None)
        self.assertEquals(self.sdn._meta.get_field("tonnage").null, True)

        self.assertEquals(self.sdn._meta.get_field("grt").max_length, 8)
        self.assertEquals(self.sdn._meta.get_field("grt").blank, True)
        self.assertEquals(self.sdn._meta.get_field("grt").default, None)
        self.assertEquals(self.sdn._meta.get_field("grt").null, True)

        self.assertEquals(self.sdn._meta.get_field("vessel_flag").max_length, 40)
        self.assertEquals(self.sdn._meta.get_field("vessel_flag").blank, True)
        self.assertEquals(self.sdn._meta.get_field("vessel_flag").default, None)
        self.assertEquals(self.sdn._meta.get_field("vessel_flag").null, True)

        self.assertEquals(self.sdn._meta.get_field("vessel_owner").max_length, 150)
        self.assertEquals(self.sdn._meta.get_field("vessel_owner").blank, True)
        self.assertEquals(self.sdn._meta.get_field("vessel_owner").default, None)
        self.assertEquals(self.sdn._meta.get_field("vessel_owner").null, True)

        self.assertEquals(self.sdn._meta.get_field("remarks").max_length, 1000)
        self.assertEquals(self.sdn._meta.get_field("remarks").blank, True)
        self.assertEquals(self.sdn._meta.get_field("remarks").default, None)
        self.assertEquals(self.sdn._meta.get_field("remarks").null, True)

        self.assertEquals(len(self.sdn_address1._meta.get_fields()), 6)

        self.assertEquals(self.sdn_address1._meta.get_field("sdn").related_model, SpeciallyDesignatedNational)
        self.assertEquals(self.sdn_address1._meta.get_field("sdn").remote_field.on_delete, models.CASCADE)

        self.assertEquals(self.sdn_address1._meta.get_field("address").max_length, 750)
        self.assertEquals(self.sdn_address1._meta.get_field("address").blank, True)
        self.assertEquals(self.sdn_address1._meta.get_field("address").default, None)
        self.assertEquals(self.sdn_address1._meta.get_field("address").null, True)

        self.assertEquals(self.sdn_address1._meta.get_field("address_group").max_length, 116)
        self.assertEquals(self.sdn_address1._meta.get_field("address_group").blank, True)
        self.assertEquals(self.sdn_address1._meta.get_field("address_group").default, None)
        self.assertEquals(self.sdn_address1._meta.get_field("address_group").null, True)

        self.assertEquals(self.sdn_address1._meta.get_field("country").max_length, 250)
        self.assertEquals(self.sdn_address1._meta.get_field("country").blank, True)
        self.assertEquals(self.sdn_address1._meta.get_field("country").default, None)
        self.assertEquals(self.sdn_address1._meta.get_field("country").null, True)

        self.assertEquals(self.sdn_address1._meta.get_field("remarks").max_length, 200)
        self.assertEquals(self.sdn_address1._meta.get_field("remarks").blank, True)
        self.assertEquals(self.sdn_address1._meta.get_field("remarks").default, None)
        self.assertEquals(self.sdn_address1._meta.get_field("remarks").null, True)

        self.assertEquals(len(self.sdn_alternate1._meta.get_fields()), 6)

        self.assertEquals(self.sdn_alternate1._meta.get_field("sdn").related_model, SpeciallyDesignatedNational)
        self.assertEquals(self.sdn_alternate1._meta.get_field("sdn").remote_field.on_delete, models.CASCADE)

        self.assertEquals(self.sdn_alternate1._meta.get_field("type").max_length, 8)
        self.assertEquals(self.sdn_alternate1._meta.get_field("type").blank, True)
        self.assertEquals(self.sdn_alternate1._meta.get_field("type").default, None)
        self.assertEquals(self.sdn_alternate1._meta.get_field("type").null, True)

        self.assertEquals(self.sdn_alternate1._meta.get_field("name").max_length, 350)
        self.assertEquals(self.sdn_alternate1._meta.get_field("name").blank, True)
        self.assertEquals(self.sdn_alternate1._meta.get_field("name").default, None)
        self.assertEquals(self.sdn_alternate1._meta.get_field("name").null, True)

        self.assertEquals(self.sdn_alternate1._meta.get_field("cleansed_name").max_length, 350)
        self.assertEquals(self.sdn_alternate1._meta.get_field("cleansed_name").blank, True)
        self.assertEquals(self.sdn_alternate1._meta.get_field("cleansed_name").default, '')

        self.assertEquals(self.sdn_alternate1._meta.get_field("remarks").max_length, 200)
        self.assertEquals(self.sdn_alternate1._meta.get_field("remarks").blank, True)
        self.assertEquals(self.sdn_alternate1._meta.get_field("remarks").default, None)
        self.assertEquals(self.sdn_alternate1._meta.get_field("remarks").null, True)

    def test_status(self):
        self.assertEquals(Status.INC, "incomplete")
        self.assertEquals(Status.ACC, "accepted")
        self.assertEquals(Status.REJ, "rejected")
        self.assertEquals(Status.REQ, "requested")

    def test_lc(self):
        expected_lc = {'account_party': {'address': '366 Auburndale St, Newton, MA',
                                         'annual_cashflow': 0,
                                         'approved_credit': [],
                                         'balance_available': 0,
                                         'country': 'United States',
                                         'id': 3,
                                         'name': "AccountParty McAccountParty's Accounts"},
                       'advising_bank': {'digital_application': [],
                                         'id': 2,
                                         'name': 'Second Best Bank',
                                         'using_digital_app': False},
                       'applicant_and_ap_j_and_s_obligated': True,
                       'application_date': datetime.datetime(2020, 7, 7, 23, 23, 10, 981670),
                       'arranging_own_insurance': False,
                       'believable_price_of_goods_status': Status.INC,
                       'beneficiary': {'address': '234 Main St, Bogota, Venezuela',
                                       'annual_cashflow': 0,
                                       'approved_credit': [],
                                       'balance_available': 0,
                                       'country': 'Venezuela',
                                       'id': 2,
                                       'name': 'Delvest'},
                       'beneficiary_approved': False,
                       'boycott_language': {'other_instructions': [{'id': 1,
                                                                    'lc_id': 1,
                                                                    'phrase': 'No items from Israel.',
                                                                    'source': 'other_instructions'}]},
                       'boycott_language_status': Status.INC,
                       'cash_secure': 50,
                       'charge_transportation_location': 'Needham',
                       'client': {'address': '48 Sutton Road, Needham, MA',
                                  'annual_cashflow': 0,
                                  'approved_credit': [],
                                  'balance_available': 0,
                                  'country': 'United States',
                                  'id': 1,
                                  'name': 'Iona Imports'},
                       'client_approved': True,
                       'comments': [],
                       'confirmation_means': 'Confirmation by a bank selected by the beneficiary',
                       'credit_amt': 60000000,
                       'credit_amt_verbal': 'Sixty Million',
                       'credit_availability': 'Payment on sight',
                       'credit_delivery_means': 'Courier',
                       'credit_expiry_location': {'digital_application': [],
                                                  'id': 2,
                                                  'name': 'Second Best Bank',
                                                  'using_digital_app': False},
                       'currency_denomination': 'USD',
                       'deferred_payment_date': '2020-04-26',
                       'delegated_negotiating_banks': [],
                       'doc_reception_notifees': 'My customer Freddys Drinks in Newton',
                       'documentaryrequirement_set': [{'doc_name': 'Commercial Invoice',
                                                       'due_date': datetime.date(2020, 4, 22),
                                                       'id': 1,
                                                       'link_to_submitted_doc': None,
                                                       'modification_complaints': None,
                                                       'modified_and_awaiting_beneficiary_approval': False,
                                                       'rejected': False,
                                                       'required_values': 'Version required: '
                                                                          'Original\n'
                                                                          'Incoterms to show: '
                                                                          '["EXW", "CPT"]\n'
                                                                          'Named place of '
                                                                          'destination: Needham',
                                                       'satisfied': False,
                                                       'submitted_doc_complaints': None,
                                                       'type': 'commercial_invoice'},
                                                      {'doc_name': 'Multimodal Bill of Lading',
                                                       'due_date': datetime.date(2020, 4, 22),
                                                       'id': 2,
                                                       'link_to_submitted_doc': None,
                                                       'modification_complaints': None,
                                                       'modified_and_awaiting_beneficiary_approval': False,
                                                       'rejected': False,
                                                       'required_values': 'Marked EXW, CPT',
                                                       'satisfied': False,
                                                       'submitted_doc_complaints': None,
                                                       'type': 'multimodal_bl'},
                                                      {'doc_name': 'Packing List',
                                                       'due_date': datetime.date(2020, 4, 21),
                                                       'id': 3,
                                                       'link_to_submitted_doc': None,
                                                       'modification_complaints': None,
                                                       'modified_and_awaiting_beneficiary_approval': False,
                                                       'rejected': False,
                                                       'required_values': '600 Bottles packed, '
                                                                          'Incoterms are correct, '
                                                                          'named place is correct.',
                                                       'satisfied': False,
                                                       'submitted_doc_complaints': None,
                                                       'type': 'generic'}],
                       'draft_presentation_date': '2020-04-22',
                       'drafts_invoice_value': 1.0,
                       'drawn': False,
                       'exchange_rate_tolerance': 0.01,
                       'expiration_date': '2020-04-24',
                       'forex_contract_num': None,
                       'goods_info': {'created_date': datetime.datetime.now().date(),
                                      'hts_code': '220410',
                                      'id': 1,
                                      'mean': Decimal('1581.60'),
                                      'standard_deviation': Decimal('14353.07')},
                       'hts_code': '2204.10.11',
                       'id': 1,
                       'import_license_approval': Status.INC,
                       'import_license_message': None,
                       'incoterms_to_show': '["EXW", "CPT"]',
                       'issuer': {'digital_application': [],
                                  'id': 1,
                                  'name': 'Best Bank',
                                  'using_digital_app': False},
                       'issuer_approved': False,
                       'late_charge_date': '2020-04-25',
                       'latest_version_notes': None,
                       'merch_charge_location': 'Boston',
                       'merch_description': 'Class A champagne aged for 200 years',
                       'named_place_of_destination': 'Needham',
                       'ofac_bank_approval': Status.INC,
                       'ofac_sanctions': [],
                       'other_data': {"An extra question on the bank's application would go here": 'and '
                                                                                                   'this '
                                                                                                   'is '
                                                                                                   'what '
                                                                                                   'the '
                                                                                                   'applicant '
                                                                                                   'responded'},
                       'other_instructions': 'No items from Israel.',
                       'paid_out': False,
                       'partial_shipment_allowed': False,
                       'paying_acceptance_and_discount_charges': {'address': '48 Sutton Road, '
                                                                             'Needham, MA',
                                                                  'annual_cashflow': 0,
                                                                  'approved_credit': [],
                                                                  'balance_available': 0,
                                                                  'country': 'United States',
                                                                  'id': 1,
                                                                  'name': 'Iona Imports'},
                       'paying_other_banks_fees': {'address': '48 Sutton Road, Needham, MA',
                                                   'annual_cashflow': 0,
                                                   'approved_credit': [],
                                                   'balance_available': 0,
                                                   'country': 'United States',
                                                   'id': 1,
                                                   'name': 'Iona Imports'},
                       'purchased_item': 'Champagne',
                       'requested': False,
                       'sanction_auto_message':
                           'https://www.treasury.gov/resource-center/sanctions/Programs/pages/venezuela.aspx',
                       'sanction_bank_approval': Status.INC,
                       'tasked_account_party_employees': [{'email': 'accountparty@ama.com',
                                                           'employer_id': 3,
                                                           'id': 3,
                                                           'name': 'AccountParty McAccountParty',
                                                           'title': 'Owner'}],
                       'tasked_advising_bank_employees': [{'bank_id': 2,
                                                           'email': 'advisey@sbb.com',
                                                           'id': 2,
                                                           'name': 'Advisey McAdvisey',
                                                           'title': 'Owner'}],
                       'tasked_beneficiary_employees': [{'email': 'steve@delvest.com',
                                                         'employer_id': 2,
                                                         'id': 2,
                                                         'name': 'Steve',
                                                         'title': 'Owner'}],
                       'tasked_client_employees': [{'email': 'steve@ii.com',
                                                    'employer_id': 1,
                                                    'id': 1,
                                                    'name': 'Steve',
                                                    'title': 'Owner'}],
                       'tasked_issuer_employees': [{'bank_id': 1,
                                                    'email': 'steve@bb.com',
                                                    'id': 1,
                                                    'name': 'Steve',
                                                    'title': 'Owner'}],
                       'terms_satisfied': False,
                       'transferable_to_applicant': False,
                       'transferable_to_beneficiary': False,
                       'transshipment_allowed': False,
                       'type': 'Commercial',
                       'unit_error_tolerance': 0.0002,
                       'unit_of_measure': 'liters',
                       'units_purchased': 600}
        self.assertEquals(self.lc.to_dict(), expected_lc)

        self.assertTrue(isinstance(self.lc._meta.get_field("type"), models.CharField))
