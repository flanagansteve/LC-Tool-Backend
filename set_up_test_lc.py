from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
from lc.models import LC, DigitalLC, DocumentaryRequirement
from django.contrib.auth.models import User
import datetime

# You may not like it, but this is what peak trade finance looks like
def create_perfect_lc():
    client = Business(name = "Iona Imports", address = "48 Sutton Road, Needham, MA")
    client.save()
    client_emp = client.businessemployee_set.create(name="Steve", title="Owner", email="steve@ii.com")
    test_client_user = User.objects.create_user(username="steve@ii.com",
                             email="steve@ii.com",
                             password="password")
    beneficiary = Business(name = "Expert Exports", address = "234 Main St, Paris, France")
    beneficiary.save()
    bene_emp = beneficiary.businessemployee_set.create(name="Steve", title="Owner", email="steve@ee.com")
    test_bene_user = User.objects.create_user(username="steve@ee.com",
                             email="steve@ee.com",
                             password="password")
    issuer = Bank(name = "Best Bank")
    issuer.save()
    issuer_emp = issuer.bankemployee_set.create(name="Steve", title="Owner", email="steve@bb.com")
    test_issuer_user = User.objects.create_user(username="steve@bb.com",
                             email="steve@bb.com",
                             password="password")
    account_party = Business(name = "AccountParty McAccountParty's Accounts", address = "366 Auburndale St, Newton, MA")
    account_party.save()
    ap_emp = account_party.businessemployee_set.create(name="AccountParty McAccountParty", title="Owner", email="accountparty@ama.com")
    test_ap_user = User.objects.create_user(username="accountparty@ama.com",
                             email="accountparty@ama.com",
                             password="password")
    advising_bank = Bank(name = "Advisey McAdvisey's Bank")
    advising_bank.save()
    ad_emp = advising_bank.bankemployee_set.create(name="Advisey McAdvisey", title="Owner", email="advisey@amb.com")
    test_ad_user = User.objects.create_user(username="advisey@amb.com",
                             email="advisey@amb.com",
                             password="password")
    lc = DigitalLC(
        issuer = issuer,
        client = client,
        beneficiary = beneficiary,
        account_party = account_party,
        advising_bank = advising_bank,
        application_date = datetime.datetime.now(),
        credit_delivery_means = 'Courier',
        credit_amt_verbal = 'Sixty Thousand Euros',
        credit_amt = 60000,
        currency_denomination = 'EUR',
        applicant_and_ap_j_and_s_obligated = True,
        exchange_rate_tolerance = 0.01,
        purchased_item = 'Champagne',
        units_of_measure = 'Bottles',
        units_purchased = 600,
        unit_error_tolerance = 0.0002,
        confirmation_means = 'Confirmation by a bank selected by the beneficiary',
        paying_other_banks_fees = client,
        credit_expiry_location = advising_bank,
        expiration_date = '2020-04-24',
        draft_presentation_date = '2020-04-22',
        drafts_invoice_value = 1.00,
        credit_availability = 'Payment on sight',
        paying_acceptance_and_discount_charges = client,
        deferred_payment_date = '2020-04-26',
        merch_charge_location = 'Boston',
        late_charge_date = '2020-04-25',
        charge_transportation_location = 'Needham',
        incoterms_to_show = '["EXW", "CPT"]',
        named_place_of_destination = 'Needham',
        doc_reception_notifees = 'My customer Freddys Drinks in Newton',
        other_instructions = 'Please re-write the entire LC in french too',
        merch_description = 'Class A champagne aged for 200 years',
        other_data = {
            'An extra question on the bank\'s application would go here' : 'and this is what the applicant responded'
        }
    )
    lc.save()
    lc.tasked_client_employees.add(client_emp)
    lc.tasked_beneficiary_employees.add(bene_emp)
    lc.tasked_issuer_employees.add(issuer_emp)
    lc.tasked_account_party_employees.add(ap_emp)
    lc.tasked_advising_bank_employees.add(ad_emp)
    lc.delegated_negotiating_banks.add(issuer)
    required_values = (
        "Version required: Original"
        + "\nIncoterms to show: " + lc.incoterms_to_show
        + "\nNamed place of destination: " + lc.named_place_of_destination
    )
    lc.documentaryrequirement_set.create(
        doc_name="Commercial Invoice",
        type="Commercial Invoice",
        required_values=required_values,
        due_date=lc.draft_presentation_date
    )
    lc.documentaryrequirement_set.create(
        doc_name="Multimodal Bill of Lading",
        type="Multimodal Bill of Lading",
        due_date=lc.draft_presentation_date,
        required_values="Marked EXW, CPT"
    )
    lc.documentaryrequirement_set.create(
        doc_name="Packing List",
        required_values="600 Bottles packed, Incoterms are correct, named place is correct.",
        due_date="2020-04-21"
    )
    print(lc.to_dict())
