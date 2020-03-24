from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.http import HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import LC, PdfLC, DigitalLC, LCAppQuestionResponse, DocumentaryRequirement
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
import json, datetime

# TODO only handling DigitalLCs for now

# 1. GET all the lcs from this bank
# 2. POST
# TODO keyerrors... unhandled key errors everywhere
@csrf_exempt
def cr_lcs(request, bank_id):
    if request.method == "GET":
        this_banks_lcs = LC.objects.filter(issuer=bank_id)
        return JsonResponse(list(this_banks_lcs.values()), safe=False)
    elif request.method == "POST":
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Http404("No bank with id " + bank_id + " found")
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if bank.bankemployee_set.filter(email=request.user.username).exists():
                # 1. create the initial LC instance with parties, creating new
                #    accounts/inviting registrants where applicable
                lc = LC(issuer = bank)
                lc.tasked_issuer_employees.add(bank.bankemployee_set.get(email=request.user.username))
                if Business.objects.filter(name=json_data['applicant']).exists():
                    if lc.client.businessemployee_set.filter(email=json_data['applicant_employee_contact']).exists():
                        lc.tasked_client_employees.add(Business.businessemployee_set.get(email=json_data['applicant_employee_contact']))
                    else:
                        # TODO decide - either
                            # send an email 'set your employee account up at <insert employee registration link>'
                        # or return an error, since the business exists, so it
                        # was probably a mistyped email
                        pass
                lc.save()
                # 2. mail the applicant_employee_contact with a link to fill out
                #    the rest of the LC via:
                send_mail(
                    bank.bankemployee_set.get(email=request.user.username).name + " has started your LC for you on Bountium!",
                    "1. Set your business up at https://bountium.org/register_business, 2. fill out your app at https://bountium.org/lc/" + lc.id,
                    "steve@bountium.org",
                    [json_data['applicant_employee_contact']],
                    fail_silently=False,
                )
                # 3. return... TODO something
                return HttpResponse("nice")
            elif BusinessEmployee.objects.filter(email=request.user.username).exists():
                employee_applying = BusinessEmployee.objects.get(email=request.user.username)
                # 1. for each of the default questions,
                #   a. get the value and
                #   b. do something with it
                #   c. remove it from the list

                # Questions 1 and 2
                applicant_name = json_data['applicant_name']
                applicant_address = json_data['applicant_address']
                # TODO check if applicant_name == employee_applying.employer.name &&
                #               applicant_address == employee_applying.employer
                #               create the lc and proceed
                #            else
                #               return forbidden
                lc = LC(issuer = bank)
                lc.client = employee_applying.employer
                del json_data['applicant_name']
                del json_data['applicant_address']

                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                # TODO if beneficiary.found, add them as lc.beneficiary
                #      else, create the Business and send invite
                del json_data['beneficiary_name']
                del json_data['beneficiary_address']

                # Question 5-8
                lc.credit_delivery_means = json_data['credit_delivery_means']
                lc.credit_amt_verbal = json_data['credit_amt_verbal']
                lc.credit_amt = json_data['credit_amt']
                lc.currency_denomination = json_data['currency_denomination']
                del json_data['credit_delivery_means']
                del json_data['credit_amt_verbal']
                del json_data['credit_amt']
                del json_data['currency_denomination']

                # Question 9
                if json_data['account_party']:
                    # Question 10-12
                    lc.applicant_and_ap_j_and_s_obligated = json_data['applicant_and_ap_j_and_s_obligated']
                    account_party_name = json_data['account_party_name']
                    account_party_address = json_data['account_party_address']
                    # TODO if account_party.found, add them as lc.account_party
                    #      else, create the Business and send invite
                    del json_data['account_party']
                    del json_data['applicant_and_ap_j_and_s_obligated']
                    del json_data['account_party_name']
                    del json_data['account_party_address']

                # Question 13
                if 'advising_bank' in json_data:
                    bank_name = json_data['advising_bank']
                    # TODO if Bank.get(name=bank_name).found, add them as lc.advising_bank
                    #      else, create the Bank and send invite
                    del json_data['advising_bank']

                # Question 14
                if 'forex_contract_num' in json_data:
                    lc.forex_contract_num = json_data['forex_contract_num']
                    del json_data['forex_contract_num']

                # Question 15-20
                lc.exchange_rate_tolerance = json_data['exchange_rate_tolerance']
                lc.purchased_item = json_data['purchased_item']
                lc.unit_of_measure = json_data['unit_of_measure']
                lc.units_purchased = json_data['units_purchased']
                lc.unit_error_tolerance = json_data['unit_error_tolerance']
                lc.confirmation_means = json_data['confirmation_means']
                del json_data['exchange_rate_tolerance']
                del json_data['purchased_item']
                del json_data['unit_of_measure']
                del json_data['units_purchased']
                del json_data['unit_error_tolerance']
                del json_data['confirmation_means']

                # TODO error handling for q21-22 - really naive implementation below:
                # Question 21
                if json_data['paying_other_banks_fees'] == lc.beneficiary.name:
                    lc.paying_other_banks_fees = lc.beneficiary
                else:
                    lc.paying_other_banks_fees = lc.client
                del json_data['paying_other_banks_fees']

                # Question 22
                if json_data['credit_expiry_location'] == bank.name:
                    lc.credit_expiry_location = lc.issuer
                else:
                    lc.credit_expiry_location = lc.advising_bank
                del json_data['credit_expiry_location']


                # Question 23-24
                # TODO what format does a model.DateField have to be in?
                lc.expiration_date = json_data['expiration_date']
                del json_data['expiration_date']
                # TODO could shorten this with a ternary op
                if 'draft_presentation_date' in json_data:
                    lc.draft_presentation_date = json_data['draft_presentation_date']
                    del json_data['draft_presentation_date']
                else:
                    # TODO we're not asking for shipment date...
                    # theotically, this should be shipment_date + 21 days
                    # using expiration_date for now
                    lc.draft_presentation_date = lc.expiration_date

                # Question 25
                if 'drafts_invoice_value' in json_data:
                    lc.drafts_invoice_value = json_data['drafts_invoice_value']
                    del json_data['drafts_invoice_value']

                # Question 26
                lc.credit_availability = json_data['credit_availability']
                del json_data['credit_availability']

                # TODO error handling - really naive implementation below:
                # Question 27
                if json_data['paying_acceptance_and_discount_charges'] == lc.beneficiary.name:
                    lc.paying_acceptance_and_discount_charges = lc.beneficiary
                else:
                    lc.paying_acceptance_and_discount_charges = lc.client

                # Question 28
                lc.deferrerd_payment_date = json_data['deferred_payment_date']
                del json_data['deferred_payment_date']

                # Question 29
                # TODO do something with json_data['delegated_negotiating_banks']
                del json_data['delegated_negotiating_banks']

                # Question 30
                lc.partial_shipment_allowed = json_data['partial_shipment_allowed']
                del json_data['partial_shipment_allowed']

                # Question 31
                lc.transshipment_allowed = json_data['transshipment_allowed']
                del json_data['transshipment_allowed']

                # Question 32
                lc.merch_charge_location = json_data['merch_charge_location']
                del json_data['merch_charge_location']

                # Question 33
                if 'late_charge_date' in json_data:
                    lc.late_charge_date = json_data['late_charge_date']
                    del json_data['late_charge_date']

                # Question 34
                lc.charge_transportation_location = json_data['charge_transportation_location']
                del json_data['charge_transportation_location']

                # Question 35
                lc.incoterms_to_show = json_data['incoterms_to_show']
                del json_data['incoterms_to_show']

                # Question 36
                lc.named_place_of_destination = json_data['named_place_of_destination']
                del json_data['named_place_of_destination']

                # Question 27
                lc.draft_accompiant_invoice = json_data['draft_accompiant_invoice']
                del json_data['draft_accompiant_invoice']

                # Question 38
                if 'draft_accompiant_transport_docs' in json_data:
                    lc.draft_accompiant_transport_docs = json_data['draft_accompiant_transport_docs']
                    del json_data['draft_accompiant_transport_docs']

                # Question 39
                if 'doc_reception_notifees' in json_data:
                    lc.doc_reception_notifees = json_data['doc_reception_notifees']
                    del json_data['doc_reception_notifees']

                # Question 40
                if 'transport_doc_marking' in json_data:
                    lc.transport_doc_marking = json_data['transport_doc_marking']
                    del json_data['transport_doc_marking']

                # Question 41
                if 'copies_of_packing_list' in json_data:
                    lc.copies_of_packing_list = json_data['copies_of_packing_list']
                    del json_data['copies_of_packing_list']

                # Question 42
                if 'copies_of_certificate_of_origin' in json_data:
                    lc.copies_of_certificate_of_origin = json_data['copies_of_certificate_of_origin']
                    del json_data['copies_of_certificate_of_origin']

                # Question 43
                if 'insurance_percentage' in json_data:
                    lc.insurance_percentage = json_data['insurance_percentage']
                    del json_data['insurance_percentage']

                # Question 44
                if 'insurance_risks_covered' in json_data:
                    lc.insurance_risks_covered = json_data['insurance_risks_covered']
                    del json_data['insurance_risks_covered']

                # Question 45
                if 'other_draft_accompiants' in json_data:
                    lc.other_draft_accompiants = json_data['other_draft_accompiants']
                    del json_data['other_draft_accompiants']

                # Question 46
                lc.arranging_own_insurance = json_data['arranging_own_insurance']
                del json_data['arranging_own_insurance']

                # Question 47
                if 'other_instructions' in json_data:
                    lc.other_instructions = json_data['other_instructions']
                    del json_data['other_instructions']

                # Question 48
                lc.merch_description = json_data['merch_description']
                del json_data['merch_description']

                # Question 49
                lc.transferability = json_data['transferability']
                del json_data['transferability']

                # 2. for any other fields left in json_data, save them as a tuple
                #    in other_data
                lc.other_data = json_data

                # 3. notify a bank employee maybe? TODO decide

                # 4. save and return back!
                lc.save()
                return JsonResponse({
                    'success' : True,
                    'lc_id' : lc.id
                })

            else:
                # TODO minor, but, technically you can get to this branch by being
                # a BankEmployee of a bank other than bank_id.
                return HttpResponseForbidden("Only employees of businesses or banks on Bountium can create LCs")
        else:
            return HttpResponseForbidden("Must be logged in to create an LC")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

@csrf_exempt
def rud_lc(request, bank_id, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except Business.DoesNotExist:
        return Http404("No lc with id " + business_id)
    if request.method == "GET":
        return JsonResponse(model_to_dict(lc))
