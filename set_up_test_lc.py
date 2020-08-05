from django.contrib.auth.models import User

from bank.views import populate_application, add_default_questions
from business.models import AuthorizedBanks, AuthStatus
from lc.models import *
from lc.views import ofac, sanction_approval, import_license, believable_price_of_goods
from util import update_ofac


# You may not like it, but this is what peak trade finance looks like
def create_perfect_lc():
    print("Updating OFAC SDN database")
    #update_ofac()
    print("Adding fresh set of default LC questions")
    add_default_questions()

    client_name = "Iona Imports"
    if Business.objects.filter(name=client_name).exists():
        print(f"Business {client_name} is already in the database")
        client = Business.objects.get(name=client_name)
    else:
        print(f"Creating business '{client_name}'")
        client = Business(name=client_name, address="48 Sutton Road, Needham, MA")
        client.save()

    client_employee_name = "Steve"
    client_employee_email = "steve@ii.com"
    if client.businessemployee_set.filter(email=client_employee_email).exists():
        print(
                f"Business employee {client_employee_name} with email '{client_employee_email}' is already in the "
                f"database")
        client_emp = client.businessemployee_set.get(email=client_employee_email)
    else:
        print(f"Creating business employee {client_name} with email '{client_employee_email}'")
        client_emp = client.businessemployee_set.create(name=client_name, title="Owner", email=client_employee_email)

    if User.objects.filter(username=client_employee_email).exists():
        print(f"Employee {client_employee_name} with email '{client_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {client_name} with email '{client_employee_email}'")
        User.objects.create_user(username=client_employee_email, email=client_employee_email, password="password")

    beneficiary_name = "Delvest"
    if Business.objects.filter(name=beneficiary_name).exists():
        print(f"Business {beneficiary_name} is already in the database")
        beneficiary = Business.objects.get(name=beneficiary_name)
    else:
        print(f"Creating business '{beneficiary_name}'")
        beneficiary = Business(name=beneficiary_name, address="234 Main St, Bogota, Venezuela", country="Venezuela")
        beneficiary.save()

    bene_employee_name = "Steve"
    bene_employee_email = "steve@delvest.com"
    if beneficiary.businessemployee_set.filter(email=bene_employee_email).exists():
        print(f"Business employee {bene_employee_name} with email '{bene_employee_email}' is already in the database")
        bene_emp = beneficiary.businessemployee_set.get(email=bene_employee_email)
    else:
        print(f"Creating business employee {bene_employee_name} with email '{bene_employee_email}'")
        bene_emp = beneficiary.businessemployee_set.create(name=bene_employee_name, title="Owner",
                                                           email=bene_employee_email)

    if User.objects.filter(username=bene_employee_email).exists():
        print(f"Employee {bene_employee_name} with email '{bene_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {bene_employee_name} with email '{bene_employee_email}'")
        User.objects.create_user(username=bene_employee_email, email=bene_employee_email, password="password")

    issuer_name = "Best Bank"
    issuer_country = "United States"
    mailing_address = "337 Huntington Avenue Boston, MA"
    email_contact = "contact@bestbank.com"
    website = "bountium.org"
    if Bank.objects.filter(name=issuer_name).exists():
        print(f"Bank '{issuer_name}' already exists in the database, updating fields")
        issuer = Bank.objects.get(name=issuer_name)
        issuer.country = issuer_country
        issuer.mailing_address = mailing_address
        issuer.email_contact = email_contact
        issuer.website = website
        issuer.save()
    else:
        print(f"Creating bank '{issuer_name}'")
        issuer = Bank(name=issuer_name, website=website, country=issuer_country, mailing_address=mailing_address,
                      email_contact=email_contact)
        issuer.save()

    if client_emp.authorized_banks.filter(bank=issuer).exists():
        print(f"Client {client_employee_name} already has authorization with bank {issuer_name}")
    else:
        print(f"Adding authorization for client {client_employee_name} with bank {issuer_name}")
        bank_auth = AuthorizedBanks(bank=issuer)
        bank_auth.save()
        client_emp.authorized_banks.add(bank_auth)
        client_emp.save()

    populate_application(issuer)

    issuer_employee_name = "Steve"
    issuer_employee_email = "steve@bb.com"
    if issuer.bankemployee_set.filter(email=issuer_employee_email).exists():
        print(f"Bank employee {issuer_employee_name} with email '{issuer_employee_email}' is already in the database")
        issuer_emp = issuer.bankemployee_set.get(email=issuer_employee_email)
    else:
        print(f"Creating bank employee {issuer_employee_name} with email '{issuer_employee_email}'")
        issuer_emp = issuer.bankemployee_set.create(name=issuer_employee_name, title="Owner",
                                                    email=issuer_employee_email)

    if User.objects.filter(username=issuer_employee_email).exists():
        print(f"Employee {issuer_employee_name} with email '{issuer_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {issuer_employee_name} with email '{issuer_employee_email}'")
        User.objects.create_user(username=issuer_employee_email, email=issuer_employee_email, password="password")
    
    forwarding_name = "Third Bank"
    forwarding_country = "United States"
    forwarding_address = "337 Huntington Avenue Boston, MA"
    email_contact = "contact@bestbank.com"
    website = "bountium.org"
    if Bank.objects.filter(name=forwarding_name).exists():
        print(f"Bank '{forwarding_name}' already exists in the database, updating fields")
        forwarding = Bank.objects.get(name=forwarding_name)
        forwarding.country = forwarding_country
        forwarding.mailing_address = forwarding_address
        forwarding.email_contact = email_contact
        forwarding.website = website
        forwarding.save()
    else:
        print(f"Creating bank '{forwarding_name}'")
        forwarding = Bank(name=forwarding_name, website=website, country=forwarding_country, mailing_address=forwarding_address,
                      email_contact=email_contact)
        forwarding.save()

    if client_emp.authorized_banks.filter(bank=forwarding).exists():
        print(f"Client {client_employee_name} already has authorization with bank {forwarding_name}")
    else:
        print(f"Adding authorization for client {client_employee_name} with bank {forwarding_name}")
        bank_auth = AuthorizedBanks(bank=forwarding)
        bank_auth.save()
        client_emp.authorized_banks.add(bank_auth)
        client_emp.save()

    populate_application(forwarding)

    forwarding_employee_name = "Steve"
    forwarding_employee_email = "steve@3b.com"
    if forwarding.bankemployee_set.filter(email=forwarding_employee_name).exists():
        print(f"Bank employee {forwarding_employee_name} with email '{forwarding_employee_name}' is already in the database")
        forwarding_emp = forwarding.bankemployee_set.get(email=forwarding_employee_name)
    else:
        print(f"Creating bank employee {forwarding_employee_email} with email '{forwarding_employee_email}'")
        forwarding_emp = forwarding.bankemployee_set.create(name=forwarding_employee_name, title="Owner",
                                                    email=forwarding_employee_email)

    if User.objects.filter(username=forwarding_employee_email).exists():
        print(f"Employee {forwarding_employee_name} with email '{forwarding_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {forwarding_employee_name} with email '{forwarding_employee_email}'")
        User.objects.create_user(username=forwarding_employee_email, email=forwarding_employee_email, password="password")

    account_party_name = "AccountParty McAccountParty's Accounts"
    if Business.objects.filter(name=account_party_name).exists():
        print(f"Business {account_party_name} is already in the database")
        account_party = Business.objects.get(name=account_party_name)
    else:
        print(f"Creating business '{account_party_name}'")
        account_party = Business(name=account_party_name, address="366 Auburndale St, Newton, MA")
        account_party.save()

    ap_employee_name = "AccountParty McAccountParty"
    ap_employee_email = "accountparty@ama.com"
    if account_party.businessemployee_set.filter(email=ap_employee_email).exists():
        print(f"Business employee {ap_employee_name} with email '{ap_employee_email}' is already in the database")
        ap_emp = account_party.businessemployee_set.get(email=ap_employee_email)
    else:
        print(f"Creating business employee {ap_employee_name} with email '{ap_employee_email}'")
        ap_emp = account_party.businessemployee_set.create(name=ap_employee_name, title="Owner",
                                                           email=ap_employee_email)

    if User.objects.filter(username=ap_employee_email).exists():
        print(f"Employee {ap_employee_name} with email '{ap_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {ap_employee_name} with email '{ap_employee_email}'")
        User.objects.create_user(username=ap_employee_email, email=ap_employee_email, password="password")

    advising_bank_name = "Second Best Bank"
    advisor_country = "United States"
    advisor_address = "337 Huntington Avenue Boston, MA"
    advisor_email = "contact@bestbank.com"
    advisor_website = "bountium.org"
    if Bank.objects.filter(name=advising_bank_name).exists():
        print(f"Bank '{advising_bank_name}' already exists in the database, updating fields")
        advising_bank = Bank.objects.get(name=advising_bank_name)
        advising_bank.country = advisor_country
        advising_bank.mailing_address = advisor_address
        advising_bank.email_contact = advisor_email
        advising_bank.website = advisor_website
        advising_bank.save()
    else:
        print(f"Creating bank '{advising_bank_name}'")
        advising_bank = Bank(name=advising_bank_name, website=advisor_website, country=advisor_country,
                             mailing_address=advisor_address, email_contact=advisor_email)
        advising_bank.save()

    populate_application(advising_bank)

    ad_employee_name = "Advisey McAdvisey"
    ad_employee_email = "advisey@sbb.com"
    if advising_bank.bankemployee_set.filter(email=ad_employee_email).exists():
        print(f"Bank employee {ad_employee_name} with email '{ad_employee_email}' is already in the database")
        ad_emp = advising_bank.bankemployee_set.get(email=ad_employee_email)
    else:
        print(f"Creating bank employee {ad_employee_name} with email '{ad_employee_email}'")
        ad_emp = advising_bank.bankemployee_set.create(name=ad_employee_name, title="Owner", email=ad_employee_email)

    if User.objects.filter(username=ad_employee_email).exists():
        print(f"Employee {ad_employee_name} with email '{ad_employee_email}' is already an authorized user")
    else:
        print(f"Creating an authorized account for {ad_employee_name} with email '{ad_employee_email}'")
        User.objects.create_user(username=ad_employee_email, email=ad_employee_email, password="password")

    lc_dict = {
        "issuer": issuer,
        "client": client,
        "beneficiary": beneficiary,
        "account_party": account_party,
        "advising_bank": advising_bank,
        "type_3_advising_bank": forwarding,
        "application_date": datetime.datetime.now(),
        "credit_delivery_means": 'Courier',
        "credit_amt_verbal": 'Sixty Thousand Euros',
        "credit_amt": 60000,
        "cash_secure": 50,
        "currency_denomination": 'EUR',
        "applicant_and_ap_j_and_s_obligated": True,
        "exchange_rate_tolerance": 0.01,
        "hts_code": "2204.10.11",
        "purchased_item": 'Champagne',
        "unit_of_measure": 'kilograms',
        "units_purchased": 600,
        "unit_error_tolerance": 0.0002,
        "confirmation_means": 'Confirmation by a bank selected by the beneficiary',
        "paying_other_banks_fees": client,
        "credit_expiry_location": advising_bank,
        "beneficiary_selected_doc_req" : True,
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
        "other_instructions": 'Please re-write the entire LC in french too',
        "merch_description": 'Class A champagne aged for 200 years',
        "other_data": {
            'An extra question on the bank\'s application would go here': 'and this is what the applicant responded'
        }
    }

    if DigitalLC.objects.filter(**lc_dict).exists():
        print(
                f"LC with client {client_name}, beneficiary {beneficiary_name}, and issuer {issuer_name} with "
                f"{lc_dict['units_purchased']} {lc_dict['unit_of_measure']} of {lc_dict['purchased_item']} is already "
                f"in "
                f"the database; no new changes were made to it")
    else:
        print(
                f"Creating new LC with client {client_name}, beneficiary {beneficiary_name}, and issuer {issuer_name} "
                f"with {lc_dict['units_purchased']} {lc_dict['unit_of_measure']} of {lc_dict['purchased_item']}")
        lc = DigitalLC(**lc_dict)
        lc.save()

        if lc.tasked_client_employees.filter(id=client_emp.id).exists():
            print(
                    f"Client employee {client_employee_name} with email '{client_employee_email}' is already tasked to "
                    f"this LC")
        else:
            print(f"Tasking client employee {client_employee_name} with email '{client_employee_email}' to this LC")
            lc.tasked_client_employees.add(client_emp)

        if lc.tasked_beneficiary_employees.filter(id=bene_emp.id).exists():
            print(
                    f"Beneficiary employee {bene_employee_name} with email '{bene_employee_email}' is already tasked "
                    f"to "
                    f"this LC")
        else:
            print(f"Tasking beneficiary employee {bene_employee_name} with email '{bene_employee_email}' to this LC")
            lc.tasked_beneficiary_employees.add(bene_emp)

        if lc.tasked_issuer_employees.filter(id=issuer_emp.id).exists():
            print(
                    f"Issuer employee {issuer_employee_name} with email '{issuer_employee_email}' is already tasked to "
                    f"this LC")
        else:
            print(f"Tasking issuer employee {issuer_employee_name} with email '{issuer_employee_email}' to this LC")
            lc.tasked_issuer_employees.add(issuer_emp)

        if lc.tasked_account_party_employees.filter(id=ap_emp.id).exists():
            print(
                    f"Account party employee {ap_employee_name} with email '{ap_employee_email}' is already tasked to "
                    f"this LC")
        else:
            print(f"Tasking account party employee {ap_employee_name} with email '{ap_employee_email}' to this LC")
            lc.tasked_account_party_employees.add(ap_emp)

        if lc.tasked_advising_bank_employees.filter(id=ad_emp.id).exists():
            print(
                    f"Advising bank employee {ad_employee_name} with email '{ad_employee_email}' is already tasked to "
                    f"this LC")
        else:
            print(f"Tasking advising bank employee {ad_employee_name} with email '{ad_employee_email}' to this LC")
            lc.tasked_advising_bank_employees.add(ad_emp)

        if lc.delegated_negotiating_banks.filter(id=issuer.id).exists():
            print(f"Bank {issuer_name} is already tasked as a delegated negotiating bank for this LC")
        else:
            print(f"Tasking bank {issuer_name} as a delegated negotiating bank for this LC")
            lc.delegated_negotiating_banks.add(issuer)

        required_values = (
                "Version required: Original"
                + "\nIncoterms to show: " + lc.incoterms_to_show
                + "\nNamed place of destination: " + lc.named_place_of_destination
        )

        if lc.documentaryrequirement_set.filter(type="commercial_invoice").exists():
            print("LC already has a Commercial Invoice; skipping creation")
        else:
            print("Creating Commercial Invoice for LC")
            test_ci = CommercialInvoiceRequirement(
                    for_lc=lc,
                    doc_name="Commercial Invoice",
                    type="commercial_invoice",
                    required_values=required_values,
                    due_date=lc.draft_presentation_date
            )
            test_ci.save()

        if lc.documentaryrequirement_set.filter(type="multimodal_bl").exists():
            print("LC already has a Multimodal Bill of Lading; skipping creation")
        else:
            print("Creating Multimodal Bill of Lading for LC")
            test_multiomodal_bl = MultimodalTransportDocumentRequirement(
                    for_lc=lc,
                    doc_name="Multimodal Bill of Lading",
                    type="multimodal_bl",
                    due_date=lc.draft_presentation_date,
                    required_values="Marked EXW, CPT"
            )
            test_multiomodal_bl.save()

        if lc.documentaryrequirement_set.filter(doc_name="Packing List").exists():
            print("LC already has a Packing List; skipping creation")
        else:
            print("Creating Packing List for LC")
            lc.documentaryrequirement_set.create(
                    doc_name="Packing List",
                    required_values="600 Bottles packed, Incoterms are correct, named place is correct.",
                    due_date="2020-04-21"
            )
        lc.save()
        print("Running OFAC check for LC")
        ofac(beneficiary.name, lc)
        print("Running sanction checks for countries of LC")
        lc.sanction_auto_message = sanction_approval(beneficiary.country, client.country)
        print("Running licensing check for LC")
        lc.import_license_message = import_license(lc)
        if GoodsInfo.objects.filter(hts_code=lc.hts_code.replace(".", "")[:6]).exists():
            print(
                    f"There is already goods information for HTS code {lc.hts_code} through code "
                    f"{lc.hts_code.replace('.', '')[:6]}")
        else:
            print(f"Running believable price of goods check for HTS code {lc.hts_code}")
            believable_price_of_goods(lc.hts_code, lc.unit_of_measure)
    print("Finished setting up LC")
