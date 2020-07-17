from datetime import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase

from .views import *

decimal_set = set()
date_set = set()


def add_to_specific_set(field_name):
    if isinstance(field, models.DecimalField):
        decimal_set.add(field_name)
    elif isinstance(field, models.DateField) or isinstance(field, models.DateTimeField):
        date_set.add(field_name)


for field in DigitalLC._meta.get_fields():
    add_to_specific_set(field.name)
for field in Business._meta.get_fields():
    add_to_specific_set(field.name)
for field in Bank._meta.get_fields():
    add_to_specific_set(field.name)
for field in ApprovedCredit._meta.get_fields():
    add_to_specific_set(field.name)


def clean_lc_dict(value, key=None):
    if (isinstance(value, Decimal) or key in decimal_set) and value is not None:
        return float(value)
    elif (isinstance(value, datetime.date) or key in date_set) and value is not None:
        return str(value)
    elif isinstance(value, dict):
        for dict_key, dict_value in value.items():
            value[dict_key] = clean_lc_dict(value=dict_value, key=dict_key)
    elif isinstance(value, list):
        for list_index, list_value in enumerate(value):
            value[list_index] = clean_lc_dict(value=list_value)
    return value


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    if "https://comtrade.un.org/api/get?max=500&type=C&freq=A&px=HS&ps=now&r=all&p=0&rg=1%2C2&cc=" in args[0]:
        response_arr = []
        for x in range(50):
            response_arr.append({
                'qtCode': 7,
                'TradeValue': 5,
                'TradeQuantity': 10
            })
        return MockResponse({'dataset': response_arr}, 200)

    return MockResponse(None, 404)


class TestCrLcs(TestCase):
    def setUp(self):
        self.maxDiff = None
        get_user_model().objects.create_user('temporary', 'temporary@gmail.com', 'temporary')
        self.bank = Bank(name="tempBank")
        self.bank.save()
        self.bank_employee = BankEmployee(bank=self.bank, email="emp@tempBank.com", name="Emp")
        self.bank_employee.save()
        self.lc_client = Business(name="client", address="10 Test Rd")
        self.lc_client.save()
        self.lc_client_employee = BusinessEmployee(employer=self.lc_client, email="emp@client.com", name="EmpClient")
        self.lc_client_employee.save()
        get_user_model().objects.create_user('emp@tempBank.com', 'emp@tempBank.com', 'emp')
        get_user_model().objects.create_user('emp@client.com', 'emp@client.com', 'emp')

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

    def test_post_bank(self):
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
        self.assertEquals(json.loads(response.content),
                          json.loads(JsonResponse({'success': True, 'created_lc': created_lc.to_dict()}).content))

    def test_post_business_minimum(self):
        self.client.login(username="emp@client.com", password='emp')
        lc_input = {
            'applicant': {
              'name': "client",
              'address': "10 Test Rd",
              'country': "United States"
            },
            'beneficiary': {
                'name': "newBene",
                'address': "newBeneAddress",
                'country': "United States"
            },
            'credit_delivery_means': "SWIFT",
            'credit_amt_verbal': "One Thousand",
            'credit_amt': 1000,
            'cash_secure': 100,
            'currency_denomination': "USD",
            'account_party': False,
            'forex_contract_num': "testForex",
            'purchased_item': "testItem",
            'hts_code': "123456",
            'unit_of_measure': "liters",
            'units_purchased': 100,
            'unit_error_tolerance': 1,
            'confirmation_means': "No Confirmation",
            'paying_other_banks_fees': "The beneficiary",
            'credit_expiry_location': "Issuing bank\'s office",
            'expiration_date': datetime.date(2020, 1, 1),
            'credit_availability': "testCredit",
            'paying_acceptance_and_discount_charges': "The beneficiary",
            'deferred_payment_date': datetime.date(2020, 1, 1),
            'delegated_negotiating_banks': "delegatedBank",
            'partial_shipment_allowed': True,
            'transshipment_allowed': True,
            'merch_charge_location': "testMerchChange",
            'charge_transportation_location': "testChargeLocation",
            'named_place_of_destination': "testNamedPlace",
            'arranging_own_insurance': True,
            'commercial_invoice': {'original': False, 'copies': 0},
            'merch_description': "testDescription",
            'transferability': "Transferable, fees charged to the applicant\'s account"
        }
        response = self.client.post(f"/lc/by_bank/{self.bank.id}/", lc_input, content_type="application/json")
        self.assertEquals(len(DigitalLC.objects.filter(issuer=self.bank)), 1)
        created_lc = DigitalLC.objects.get(issuer=self.bank)
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content)
        self.assertEquals(response_dict['success'], True)
        self.assertEquals(clean_lc_dict(response_dict['created_lc']), clean_lc_dict(created_lc.to_dict()))


class TestModels(TestCase):
    @mock.patch('lc.views.requests.get', side_effect=mocked_requests_get)
    def setUp(self, mocked):
        self.maxDiff = None
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
        bank_auth = AuthorizedBanks(bank=issuer)
        bank_auth.save()
        client_emp.authorized_banks.add(bank_auth)
        client_emp.save()
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
                                         'id': Business.objects.get(name="AccountParty McAccountParty's Accounts").id,
                                         'name': "AccountParty McAccountParty's Accounts"},
                       'advising_bank': {'digital_application': [],
                                         'id': Bank.objects.get(name='Second Best Bank').id,
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
                                       'id': Business.objects.get(name='Delvest').id,
                                       'name': 'Delvest'},
                       'beneficiary_approved': False,
                       'boycott_language': {'other_instructions': [{'id': BoycottLanguage.objects.get(
                               phrase='No items from Israel.', source='other_instructions', lc=self.lc).id,
                                                                    'lc_id': self.lc.id,
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
                                  'id': Business.objects.get(name="Iona Imports").id,
                                  'name': 'Iona Imports'},
                       'client_approved': True,
                       'comments': [],
                       'confirmation_means': 'Confirmation by a bank selected by the beneficiary',
                       'credit_amt': 60000000,
                       'credit_amt_verbal': 'Sixty Million',
                       'credit_availability': 'Payment on sight',
                       'credit_delivery_means': 'Courier',
                       'credit_expiry_location': {'digital_application': [],
                                                  'id': Bank.objects.get(name="Second Best Bank").id,
                                                  'name': 'Second Best Bank',
                                                  'using_digital_app': False},
                       'currency_denomination': 'USD',
                       'deferred_payment_date': '2020-04-26',
                       'delegated_negotiating_banks': [],
                       'doc_reception_notifees': 'My customer Freddys Drinks in Newton',
                       'documentaryrequirement_set': [{'doc_name': 'Commercial Invoice',
                                                       'due_date': datetime.date(2020, 4, 22),
                                                       'id': DocumentaryRequirement.objects.get(
                                                               doc_name='Commercial Invoice', for_lc=self.lc).id,
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
                                                       'id': DocumentaryRequirement.objects.get(
                                                               doc_name='Multimodal Bill of Lading', for_lc=self.lc).id,
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
                                                       'id': DocumentaryRequirement.objects.get(doc_name='Packing List',
                                                                                                for_lc=self.lc).id,
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
                                      'id': GoodsInfo.objects.get(hts_code='220410').id,
                                      'mean': Decimal('2.00'),
                                      'standard_deviation': Decimal('0.00')},
                       'hts_code': '2204.10.11',
                       'id': self.lc.id,
                       'import_license_approval': Status.INC,
                       'import_license_message': None,
                       'incoterms_to_show': '["EXW", "CPT"]',
                       'issuer': {'digital_application': [],
                                  'id': Bank.objects.get(name="Best Bank").id,
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
                                                                  'id': Business.objects.get(name="Iona Imports").id,
                                                                  'name': 'Iona Imports'},
                       'paying_other_banks_fees': {'address': '48 Sutton Road, Needham, MA',
                                                   'annual_cashflow': 0,
                                                   'approved_credit': [],
                                                   'balance_available': 0,
                                                   'country': 'United States',
                                                   'id': Business.objects.get(name="Iona Imports").id,
                                                   'name': 'Iona Imports'},
                       'purchased_item': 'Champagne',
                       'requested': False,
                       'sanction_auto_message':
                           'https://www.treasury.gov/resource-center/sanctions/Programs/pages/venezuela.aspx',
                       'sanction_bank_approval': Status.INC,
                       'tasked_account_party_employees': [{'email': 'accountparty@ama.com',
                                                           'employer': Business.objects.get(
                                                                   name="AccountParty McAccountParty's "
                                                                        "Accounts").to_dict(),
                                                           'id': BusinessEmployee.objects.get(
                                                                   name='AccountParty McAccountParty',
                                                                   employer=Business.objects.get(
                                                                           name="AccountParty McAccountParty's "
                                                                                "Accounts")).id,
                                                           'name': 'AccountParty McAccountParty',
                                                           'title': 'Owner',
                                                           'authorized_banks': []}],
                       'tasked_advising_bank_employees': [{'bank_id': Bank.objects.get(name="Second Best Bank").id,
                                                           'email': 'advisey@sbb.com',
                                                           'id': BankEmployee.objects.get(name="Advisey McAdvisey",
                                                                                          bank=Bank.objects.get(
                                                                                                  name="Second Best "
                                                                                                       "Bank")).id,
                                                           'name': 'Advisey McAdvisey',
                                                           'title': 'Owner'}],
                       'tasked_beneficiary_employees': [{'email': 'steve@delvest.com',
                                                         'employer': Business.objects.get(name="Delvest").to_dict(),
                                                         'id': BusinessEmployee.objects.get(name="Steve",
                                                                                            employer=Business.objects.get(
                                                                                                    name="Delvest")).id,
                                                         'name': 'Steve',
                                                         'title': 'Owner',
                                                         'authorized_banks': []}],
                       'tasked_client_employees': [{'email': 'steve@ii.com',
                                                    'employer': Business.objects.get(name="Iona Imports").to_dict(),
                                                    'id': BusinessEmployee.objects.get(name="Steve",
                                                                                       employer=Business.objects.get(
                                                                                               name="Iona Imports")).id,
                                                    'name': 'Steve',
                                                    'title': 'Owner',
                                                    'authorized_banks':
                                                        list(map(lambda b: b.to_dict(),
                                                                 BusinessEmployee.objects.get(
                                                                         name="Steve",
                                                                         employer=Business.objects.get(
                                                                                 name="Iona "
                                                                                      "Imports")).authorized_banks.all()))}],
                       'tasked_issuer_employees': [
                           {'bank_id': Bank.objects.get(name="Best Bank").id,
                            'email': 'steve@bb.com',
                            'id': BankEmployee.objects.get(name="Steve",
                                                           bank=Bank.objects.get(
                                                                   name="Best Bank")).id,
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

        self.assertEquals(len(self.lc._meta.get_fields()), 71)

        client = self.lc._meta.get_field('client')
        self.assertTrue(isinstance(client, models.ForeignKey))
        self.assertEquals(client.related_model, Business)
        self.assertEquals(client.remote_field.on_delete, models.CASCADE)
        self.assertEquals(client.remote_field.related_name, "lc_lc_client")
        self.assertEquals(client.null, True)
        self.assertEquals(client.blank, True)

        beneficiary = self.lc._meta.get_field('beneficiary')
        self.assertTrue(isinstance(beneficiary, models.ForeignKey))
        self.assertEquals(beneficiary.related_model, Business)
        self.assertEquals(beneficiary.remote_field.on_delete, models.CASCADE)
        self.assertEquals(beneficiary.remote_field.related_name, "lc_lc_beneficiary")
        self.assertEquals(beneficiary.null, True)
        self.assertEquals(beneficiary.blank, True)

        issuer = self.lc._meta.get_field('issuer')
        self.assertTrue(isinstance(issuer, models.ForeignKey))
        self.assertEquals(issuer.related_model, Bank)
        self.assertEquals(issuer.remote_field.on_delete, models.CASCADE)
        self.assertEquals(issuer.remote_field.related_name, "lc_lc_issuer")

        account_party = self.lc._meta.get_field('account_party')
        self.assertTrue(isinstance(account_party, models.ForeignKey))
        self.assertEquals(account_party.related_model, Business)
        self.assertEquals(account_party.remote_field.on_delete, models.CASCADE)
        self.assertEquals(account_party.remote_field.related_name, "lc_lc_account_party")
        self.assertEquals(account_party.null, True)
        self.assertEquals(account_party.blank, True)

        advising_bank = self.lc._meta.get_field('advising_bank')
        self.assertTrue(isinstance(advising_bank, models.ForeignKey))
        self.assertEquals(advising_bank.related_model, Bank)
        self.assertEquals(advising_bank.remote_field.on_delete, models.CASCADE)
        self.assertEquals(advising_bank.remote_field.related_name, "lc_lc_advising_bank")
        self.assertEquals(advising_bank.null, True)
        self.assertEquals(advising_bank.blank, True)

        tasked_client_employees = self.lc._meta.get_field('tasked_client_employees')
        self.assertTrue(isinstance(tasked_client_employees, models.ManyToManyField))
        self.assertEquals(tasked_client_employees.related_model, BusinessEmployee)
        self.assertEquals(tasked_client_employees.remote_field.related_name, "lc_lc_tasked_client_employees")

        tasked_beneficiary_employees = self.lc._meta.get_field('tasked_beneficiary_employees')
        self.assertTrue(isinstance(tasked_beneficiary_employees, models.ManyToManyField))
        self.assertEquals(tasked_beneficiary_employees.related_model, BusinessEmployee)
        self.assertEquals(tasked_beneficiary_employees.remote_field.related_name, "lc_lc_tasked_beneficiary_employees")

        tasked_issuer_employees = self.lc._meta.get_field('tasked_issuer_employees')
        self.assertTrue(isinstance(tasked_issuer_employees, models.ManyToManyField))
        self.assertEquals(tasked_issuer_employees.related_model, BankEmployee)
        self.assertEquals(tasked_issuer_employees.remote_field.related_name, "lc_lc_tasked_issuer_employees")

        tasked_account_party_employees = self.lc._meta.get_field('tasked_account_party_employees')
        self.assertTrue(isinstance(tasked_account_party_employees, models.ManyToManyField))
        self.assertEquals(tasked_account_party_employees.related_model, BusinessEmployee)
        self.assertEquals(tasked_account_party_employees.remote_field.related_name,
                          "lc_lc_tasked_account_party_employees")

        tasked_advising_bank_employees = self.lc._meta.get_field('tasked_advising_bank_employees')
        self.assertTrue(isinstance(tasked_advising_bank_employees, models.ManyToManyField))
        self.assertEquals(tasked_advising_bank_employees.related_model, BankEmployee)
        self.assertEquals(tasked_advising_bank_employees.remote_field.related_name,
                          "lc_lc_tasked_advising_bank_employees")

        sanction_bank_approval = self.lc._meta.get_field('sanction_bank_approval')
        self.assertTrue(isinstance(sanction_bank_approval, models.CharField))
        self.assertEquals(sanction_bank_approval.max_length, 10)
        self.assertEquals(sanction_bank_approval.default, Status.INC)
        self.assertEquals(sanction_bank_approval.choices,
                          [(Status.INC, "incomplete"), (Status.ACC, "accepted"), (Status.REJ, "rejected"),
                           (Status.REQ, "requested")])

        sanction_auto_message = self.lc._meta.get_field('sanction_auto_message')
        self.assertTrue(isinstance(sanction_auto_message, models.CharField))
        self.assertEquals(sanction_auto_message.max_length, 1000)
        self.assertEquals(sanction_auto_message.null, True)
        self.assertEquals(sanction_auto_message.blank, True)

        ofac_bank_approval = self.lc._meta.get_field('ofac_bank_approval')
        self.assertTrue(isinstance(ofac_bank_approval, models.CharField))
        self.assertEquals(ofac_bank_approval.max_length, 10)
        self.assertEquals(ofac_bank_approval.default, Status.INC)
        self.assertEquals(ofac_bank_approval.choices,
                          [(Status.INC, "incomplete"), (Status.ACC, "accepted"), (Status.REJ, "rejected"),
                           (Status.REQ, "requested")])

        ofac_sanctions = self.lc._meta.get_field('ofac_sanctions')
        self.assertTrue(isinstance(ofac_sanctions, models.ManyToManyField))
        self.assertEquals(ofac_sanctions.related_model, SpeciallyDesignatedNational)

        import_license_approval = self.lc._meta.get_field('import_license_approval')
        self.assertTrue(isinstance(import_license_approval, models.CharField))
        self.assertEquals(import_license_approval.max_length, 10)
        self.assertEquals(import_license_approval.default, Status.INC)
        self.assertEquals(import_license_approval.choices,
                          [(Status.INC, "incomplete"), (Status.ACC, "accepted"), (Status.REJ, "rejected"),
                           (Status.REQ, "requested")])

        import_license_message = self.lc._meta.get_field('import_license_message')
        self.assertTrue(isinstance(import_license_message, models.TextField))
        self.assertEquals(import_license_message.default, " ")
        self.assertEquals(import_license_message.null, True)
        self.assertEquals(import_license_message.blank, True)

        boycott_language_status = self.lc._meta.get_field('boycott_language_status')
        self.assertTrue(isinstance(boycott_language_status, models.CharField))
        self.assertEquals(boycott_language_status.max_length, 10)
        self.assertEquals(boycott_language_status.default, Status.INC)
        self.assertEquals(boycott_language_status.choices,
                          [(Status.INC, "incomplete"), (Status.ACC, "accepted"), (Status.REJ, "rejected"),
                           (Status.REQ, "requested")])

        believable_price_of_goods_status = self.lc._meta.get_field('believable_price_of_goods_status')
        self.assertTrue(isinstance(believable_price_of_goods_status, models.CharField))
        self.assertEquals(believable_price_of_goods_status.max_length, 10)
        self.assertEquals(believable_price_of_goods_status.default, Status.INC)
        self.assertEquals(believable_price_of_goods_status.choices,
                          [(Status.INC, "incomplete"), (Status.ACC, "accepted"), (Status.REJ, "rejected"),
                           (Status.REQ, "requested")])

        client_approved = self.lc._meta.get_field('client_approved')
        self.assertTrue(isinstance(client_approved, models.BooleanField))
        self.assertEquals(client_approved.default, True)

        issuer_approved = self.lc._meta.get_field('issuer_approved')
        self.assertTrue(isinstance(issuer_approved, models.BooleanField))
        self.assertEquals(issuer_approved.default, False)

        beneficiary_approved = self.lc._meta.get_field('beneficiary_approved')
        self.assertTrue(isinstance(beneficiary_approved, models.BooleanField))
        self.assertEquals(beneficiary_approved.default, False)

        latest_version_notes = self.lc._meta.get_field('latest_version_notes')
        self.assertTrue(isinstance(latest_version_notes, models.CharField))
        self.assertEquals(latest_version_notes.max_length, 1000)
        self.assertEquals(latest_version_notes.null, True)
        self.assertEquals(latest_version_notes.blank, True)

        application_date = self.lc._meta.get_field('application_date')
        self.assertTrue(isinstance(application_date, models.DateField))
        self.assertEquals(application_date.null, True)
        self.assertEquals(application_date.blank, True)

        terms_satisfied = self.lc._meta.get_field('terms_satisfied')
        self.assertTrue(isinstance(terms_satisfied, models.BooleanField))
        self.assertEquals(terms_satisfied.default, False)

        requested = self.lc._meta.get_field('requested')
        self.assertTrue(isinstance(requested, models.BooleanField))
        self.assertEquals(requested.default, False)

        drawn = self.lc._meta.get_field('drawn')
        self.assertTrue(isinstance(drawn, models.BooleanField))
        self.assertEquals(drawn.default, False)

        paid_out = self.lc._meta.get_field('paid_out')
        self.assertTrue(isinstance(paid_out, models.BooleanField))
        self.assertEquals(paid_out.default, False)

        type = self.lc._meta.get_field('type')
        self.assertTrue(isinstance(type, models.CharField))
        self.assertEquals(type.max_length, 20)
        self.assertEquals(type.default, "Commercial")

        hts_code = self.lc._meta.get_field('hts_code')
        self.assertTrue(isinstance(hts_code, models.CharField))
        self.assertEquals(hts_code.max_length, 12)
        self.assertEquals(hts_code.default, "")

        credit_delivery_means = self.lc._meta.get_field('credit_delivery_means')
        self.assertTrue(isinstance(credit_delivery_means, models.CharField))
        self.assertEquals(credit_delivery_means.max_length, 250)
        self.assertEquals(credit_delivery_means.null, True)
        self.assertEquals(credit_delivery_means.blank, True)

        credit_amt_verbal = self.lc._meta.get_field('credit_amt_verbal')
        self.assertTrue(isinstance(credit_amt_verbal, models.CharField))
        self.assertEquals(credit_amt_verbal.max_length, 250)
        self.assertEquals(credit_amt_verbal.null, True)
        self.assertEquals(credit_amt_verbal.blank, True)

        credit_amt = self.lc._meta.get_field('credit_amt')
        self.assertTrue(isinstance(credit_amt, models.DecimalField))
        self.assertEquals(credit_amt.max_digits, 17)
        self.assertEquals(credit_amt.decimal_places, 2)
        self.assertEquals(credit_amt.blank, True)
        self.assertEquals(credit_amt.null, True)

        cash_secure = self.lc._meta.get_field('cash_secure')
        self.assertTrue(isinstance(cash_secure, models.DecimalField))
        self.assertEquals(cash_secure.max_digits, 17)
        self.assertEquals(cash_secure.decimal_places, 2)
        self.assertEquals(cash_secure.blank, True)
        self.assertEquals(cash_secure.null, True)
        self.assertEquals(cash_secure.default, decimal.Decimal('0.00'))

        currency_denomination = self.lc._meta.get_field('currency_denomination')
        self.assertTrue(isinstance(currency_denomination, models.CharField))
        self.assertEquals(currency_denomination.max_length, 5)
        self.assertEquals(currency_denomination.default, "USD")

        applicant_and_ap_j_and_s_obligated = self.lc._meta.get_field('applicant_and_ap_j_and_s_obligated')
        self.assertTrue(isinstance(applicant_and_ap_j_and_s_obligated, models.BooleanField))
        self.assertEquals(applicant_and_ap_j_and_s_obligated.default, False)

        forex_contract_num = self.lc._meta.get_field('forex_contract_num')
        self.assertTrue(isinstance(forex_contract_num, models.CharField))
        self.assertEquals(forex_contract_num.max_length, 250)
        self.assertEquals(forex_contract_num.null, True)
        self.assertEquals(forex_contract_num.blank, True)

        exchange_rate_tolerance = self.lc._meta.get_field('exchange_rate_tolerance')
        self.assertTrue(isinstance(exchange_rate_tolerance, models.DecimalField))
        self.assertEquals(exchange_rate_tolerance.max_digits, 8)
        self.assertEquals(exchange_rate_tolerance.decimal_places, 5)
        self.assertEquals(exchange_rate_tolerance.blank, True)
        self.assertEquals(exchange_rate_tolerance.null, True)

        purchased_item = self.lc._meta.get_field('purchased_item')
        self.assertTrue(isinstance(purchased_item, models.CharField))
        self.assertEquals(purchased_item.max_length, 1000)
        self.assertEquals(purchased_item.null, True)
        self.assertEquals(purchased_item.blank, True)

        unit_of_measure = self.lc._meta.get_field('unit_of_measure')
        self.assertTrue(isinstance(unit_of_measure, models.CharField))
        self.assertEquals(unit_of_measure.max_length, 1000)
        self.assertEquals(unit_of_measure.null, True)
        self.assertEquals(unit_of_measure.blank, True)

        units_purchased = self.lc._meta.get_field('units_purchased')
        self.assertTrue(isinstance(units_purchased, models.DecimalField))
        self.assertEquals(units_purchased.max_digits, 20)
        self.assertEquals(units_purchased.decimal_places, 2)
        self.assertEquals(units_purchased.blank, True)
        self.assertEquals(units_purchased.null, True)

        unit_error_tolerance = self.lc._meta.get_field('unit_error_tolerance')
        self.assertTrue(isinstance(unit_error_tolerance, models.DecimalField))
        self.assertEquals(unit_error_tolerance.max_digits, 8)
        self.assertEquals(unit_error_tolerance.decimal_places, 5)
        self.assertEquals(unit_error_tolerance.blank, True)
        self.assertEquals(unit_error_tolerance.null, True)

        confirmation_means = self.lc._meta.get_field('confirmation_means')
        self.assertTrue(isinstance(confirmation_means, models.CharField))
        self.assertEquals(confirmation_means.max_length, 1000)
        self.assertEquals(confirmation_means.default, "No Confirmation")

        paying_other_banks_fees = self.lc._meta.get_field('paying_other_banks_fees')
        self.assertTrue(isinstance(paying_other_banks_fees, models.ForeignKey))
        self.assertEquals(paying_other_banks_fees.related_model, Business)
        self.assertEquals(paying_other_banks_fees.remote_field.on_delete, models.CASCADE)
        self.assertEquals(paying_other_banks_fees.remote_field.related_name, 'lc_digitallc_paying_other_banks_fees')
        self.assertEquals(paying_other_banks_fees.blank, True)
        self.assertEquals(paying_other_banks_fees.null, True)

        credit_expiry_location = self.lc._meta.get_field('credit_expiry_location')
        self.assertTrue(isinstance(credit_expiry_location, models.ForeignKey))
        self.assertEquals(credit_expiry_location.related_model, Bank)
        self.assertEquals(credit_expiry_location.remote_field.on_delete, models.CASCADE)
        self.assertEquals(credit_expiry_location.remote_field.related_name, 'lc_digitallc_credit_expiry_location')
        self.assertEquals(credit_expiry_location.blank, True)
        self.assertEquals(credit_expiry_location.null, True)

        expiration_date = self.lc._meta.get_field('expiration_date')
        self.assertTrue(isinstance(expiration_date, models.DateField))
        self.assertEquals(expiration_date.null, True)
        self.assertEquals(expiration_date.blank, True)

        draft_presentation_date = self.lc._meta.get_field('draft_presentation_date')
        self.assertTrue(isinstance(draft_presentation_date, models.DateField))
        self.assertEquals(draft_presentation_date.null, True)
        self.assertEquals(draft_presentation_date.blank, True)

        drafts_invoice_value = self.lc._meta.get_field('drafts_invoice_value')
        self.assertTrue(isinstance(drafts_invoice_value, models.DecimalField))
        self.assertEquals(drafts_invoice_value.max_digits, 8)
        self.assertEquals(drafts_invoice_value.decimal_places, 5)
        self.assertEquals(drafts_invoice_value.null, True)
        self.assertEquals(drafts_invoice_value.blank, True)
        self.assertEquals(drafts_invoice_value.default, decimal.Decimal('100.00000'))

        credit_availability = self.lc._meta.get_field('credit_availability')
        self.assertTrue(isinstance(credit_availability, models.CharField))
        self.assertEquals(credit_availability.max_length, 250)
        self.assertEquals(credit_availability.null, True)
        self.assertEquals(credit_availability.blank, True)

        paying_acceptance_and_discount_charges = self.lc._meta.get_field('paying_acceptance_and_discount_charges')
        self.assertTrue(isinstance(paying_acceptance_and_discount_charges, models.ForeignKey))
        self.assertEquals(paying_acceptance_and_discount_charges.related_model, Business)
        self.assertEquals(paying_acceptance_and_discount_charges.remote_field.on_delete, models.CASCADE)
        self.assertEquals(paying_acceptance_and_discount_charges.remote_field.related_name,
                          'lc_digitallc_paying_acceptance_and_discount_charges')
        self.assertEquals(paying_acceptance_and_discount_charges.blank, True)
        self.assertEquals(paying_acceptance_and_discount_charges.null, True)

        deferred_payment_date = self.lc._meta.get_field('deferred_payment_date')
        self.assertTrue(isinstance(deferred_payment_date, models.DateField))
        self.assertEquals(deferred_payment_date.null, True)
        self.assertEquals(deferred_payment_date.blank, True)

        delegated_negotiating_banks = self.lc._meta.get_field('delegated_negotiating_banks')
        self.assertTrue(isinstance(delegated_negotiating_banks, models.ManyToManyField))
        self.assertEquals(delegated_negotiating_banks.related_model, Bank)

        partial_shipment_allowed = self.lc._meta.get_field('partial_shipment_allowed')
        self.assertTrue(isinstance(partial_shipment_allowed, models.BooleanField))
        self.assertEquals(partial_shipment_allowed.default, False)

        transshipment_allowed = self.lc._meta.get_field('transshipment_allowed')
        self.assertTrue(isinstance(transshipment_allowed, models.BooleanField))
        self.assertEquals(transshipment_allowed.default, False)

        merch_charge_location = self.lc._meta.get_field('merch_charge_location')
        self.assertTrue(isinstance(merch_charge_location, models.CharField))
        self.assertEquals(merch_charge_location.max_length, 250)
        self.assertEquals(merch_charge_location.null, True)
        self.assertEquals(merch_charge_location.blank, True)

        late_charge_date = self.lc._meta.get_field('late_charge_date')
        self.assertTrue(isinstance(late_charge_date, models.DateField))
        self.assertEquals(late_charge_date.null, True)
        self.assertEquals(late_charge_date.blank, True)

        charge_transportation_location = self.lc._meta.get_field('charge_transportation_location')
        self.assertTrue(isinstance(charge_transportation_location, models.CharField))
        self.assertEquals(charge_transportation_location.max_length, 250)
        self.assertEquals(charge_transportation_location.null, True)
        self.assertEquals(charge_transportation_location.blank, True)

        incoterms_to_show = self.lc._meta.get_field('incoterms_to_show')
        self.assertTrue(isinstance(incoterms_to_show, models.CharField))
        self.assertEquals(incoterms_to_show.max_length, 250)
        self.assertEquals(incoterms_to_show.null, True)
        self.assertEquals(incoterms_to_show.blank, True)

        named_place_of_destination = self.lc._meta.get_field('named_place_of_destination')
        self.assertTrue(isinstance(named_place_of_destination, models.CharField))
        self.assertEquals(named_place_of_destination.max_length, 250)
        self.assertEquals(named_place_of_destination.null, True)
        self.assertEquals(named_place_of_destination.blank, True)

        doc_reception_notifees = self.lc._meta.get_field('doc_reception_notifees')
        self.assertTrue(isinstance(doc_reception_notifees, models.CharField))
        self.assertEquals(doc_reception_notifees.max_length, 250)
        self.assertEquals(doc_reception_notifees.null, True)
        self.assertEquals(doc_reception_notifees.blank, True)

        arranging_own_insurance = self.lc._meta.get_field('arranging_own_insurance')
        self.assertTrue(isinstance(arranging_own_insurance, models.BooleanField))
        self.assertEquals(arranging_own_insurance.default, False)

        other_instructions = self.lc._meta.get_field('other_instructions')
        self.assertTrue(isinstance(other_instructions, models.CharField))
        self.assertEquals(other_instructions.max_length, 2000)
        self.assertEquals(other_instructions.null, True)
        self.assertEquals(other_instructions.blank, True)

        merch_description = self.lc._meta.get_field('merch_description')
        self.assertTrue(isinstance(merch_description, models.CharField))
        self.assertEquals(merch_description.max_length, 2000)
        self.assertEquals(merch_description.null, True)
        self.assertEquals(merch_description.blank, True)

        transferable_to_applicant = self.lc._meta.get_field('transferable_to_applicant')
        self.assertTrue(isinstance(transferable_to_applicant, models.BooleanField))
        self.assertEquals(transferable_to_applicant.default, False)

        transferable_to_beneficiary = self.lc._meta.get_field('transferable_to_beneficiary')
        self.assertTrue(isinstance(transferable_to_beneficiary, models.BooleanField))
        self.assertEquals(transferable_to_beneficiary.default, False)

        other_data = self.lc._meta.get_field('other_data')
        self.assertTrue(isinstance(other_data, models.CharField))
        self.assertEquals(other_data.max_length, 1000)
        self.assertEquals(other_data.default, "")
