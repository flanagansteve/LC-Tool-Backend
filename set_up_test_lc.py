from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
from lc.models import *
from bank.views import populate_application
from django.contrib.auth.models import User
import datetime

# You may not like it, but this is what peak trade finance looks like
def create_perfect_lc():
    # client = Business(name = "Ex business", address = "48 Sutton Road, Needham, MA", country = "France")
    # client.save()
    # client_emp = client.businessemployee_set.create(name="rohil", title="vp", email="rohil@ii.com")
    # test_client_user = User.objects.create_user(username="rohil@pp.com",
    #                          email="rohil@ii.com",
    #                          password="password2")
    # beneficiary = Business(name = "Expert Exports 2", address = "234 Main St, Paris, France", country = "Iran")
    # beneficiary.save()
    # bene_emp = beneficiary.businessemployee_set.create(name="rohil", title="vp", email="rohil@ee.com")
    # test_bene_user = User.objects.create_user(username="rohil@ee.com",
    #                          email="rohil@ee.com",
    #                          password="password2")
    # issuer = Bank(name = "Best Bank 3")
    # issuer.save()
    # populate_application(issuer)
    # issuer_emp = issuer.bankemployee_set.create(name="rohil", title="vp", email="rohil@bb.com")
    # test_issuer_user = User.objects.create_user(username="rohil@bb.com",
    #                          email="rohil@bb.com",
    #                          password="password2")
    # account_party = Business(name = "AccountParty McAccountParty's Accounts", address = "366 Auburndale St, Newton, MA")
    # account_party.save()
    # ap_emp = account_party.businessemployee_set.create(name="AccountParty McAccountParty", title="Owner", email="accountparty@ama.com")
    # test_ap_user = User.objects.create_user(username="accountparty@ama.com",
    #                          email="accountparty@ama.com",
    #                          password="password")
    # advising_bank = Bank(name = "Second Best Bank")
    # advising_bank.save()
    # populate_application(advising_bank)
    # ad_emp = advising_bank.bankemployee_set.create(name="Advisey McAdvisey", title="Owner", email="advisey@sbb.com")
    # test_ad_user = User.objects.create_user(username="advisey@sbb.com",
    #                          email="advisey@sbb.com",
    #                          password="password")
    
    lc = DigitalLC(
        issuer  = Bank.objects.get(id=1),
        client = Business.objects.get(id = 12),
        beneficiary = Business.objects.get(id = 13),
        # account_party = account_party,
        # advising_bank = advising_bank,
        application_date = datetime.datetime.now(),
        credit_delivery_means = 'Courier',
        credit_amt_verbal = 'Sixty Thousand Euros',
        credit_amt = 60000,
        currency_denomination = 'EUR',
        applicant_and_ap_j_and_s_obligated = True,
        exchange_rate_tolerance = 0.01,
        purchased_item = 'Champagne',
        unit_of_measure = 'Bottles',
        units_purchased = 600,
        unit_error_tolerance = 0.0002,
        confirmation_means = 'Confirmation by a bank selected by the beneficiary',
        paying_other_banks_fees = Business.objects.get(id = 12),
        # credit_expiry_location = advising_bank,
        expiration_date = '2020-04-24',
        draft_presentation_date = '2020-04-22',
        drafts_invoice_value = 1.00,
        credit_availability = 'Payment on sight',
        paying_acceptance_and_discount_charges = Business.objects.get(id = 12),
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
    # lc.tasked_client_employees.add(client_emp)
    # lc.tasked_beneficiary_employees.add(bene_emp)
    # lc.tasked_issuer_employees.add(issuer_emp)
    # lc.tasked_account_party_employees.add(ap_emp)
    # lc.tasked_advising_bank_employees.add(ad_emp)
    # lc.delegated_negotiating_banks.add(issuer)
    required_values = (
        "Version required: Original"
        + "\nIncoterms to show: " + lc.incoterms_to_show
        + "\nNamed place of destination: " + lc.named_place_of_destination
    )
    test_ci = CommercialInvoiceRequirement(
        for_lc=lc,
        doc_name="Commercial Invoice",
        type="commercial_invoice",
        required_values=required_values,
        due_date=lc.draft_presentation_date
    )
    test_multiomodal_bl = MultimodalTransportDocumentRequirement(
        for_lc=lc,
        doc_name="Multimodal Bill of Lading",
        type="multimodal_bl",
        due_date=lc.draft_presentation_date,
        required_values="Marked EXW, CPT"
    )
    test_ci.save()
    test_multiomodal_bl.save()
    lc.documentaryrequirement_set.create(
        doc_name="Packing List",
        required_values="600 Bottles packed, Incoterms are correct, named place is correct.",
        due_date="2020-04-21"
    )
    lc.save()
    print(lc.to_dict())
