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
# TODO none of these distinguish between different employees within each party - only verifying that you are A employee of the appropriate party to perform an action
# TODO keyerrors... unhandled key errors everywhere
# TODO a lot more of these should be authenticated, esp GETs

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

                set_lc_specifications(lc, json_data)

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
def rud_lc(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "GET":
        return JsonResponse(model_to_dict(lc))
    elif request.method == "POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            # The client's employee is responding to an LC application their bank started for them
            if lc.client.businessemployee_set.filter(email=request.user.username).exists():
                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                # TODO if beneficiary.found, add them as lc.beneficiary
                #      else, create the Business and send invite
                del json_data['beneficiary_name']
                del json_data['beneficiary_address']

                set_lc_specifications(lc, json_data)

                return JsonResponse({
                    'success' : True
                })
            else:
                return HttpResponseForbidden("Only employees of the business applying for this LC can create the LC")
        else:
            return HttpResponseForbidden("Must be logged in to create an LC")
    elif request.method == "PUT":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                # TODO would be good to somehow mark changes from the prev version...
                set_lc_specifications(lc, json_data)
                lc.issuer_approved = True
                lc.beneficiary_approved = False
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success' : True
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                # TODO would be good to somehow mark changes from the prev version...
                set_lc_specifications(lc, json_data)
                lc.issuer_approved = False
                lc.beneficiary_approved = True
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success' : True
                })
            elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                # TODO would be good to somehow mark changes from the prev version...
                set_lc_specifications(lc, json_data)
                lc.issuer_approved = False
                lc.beneficiary_approved = False
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success' : True
                })
            else:
                return HttpResponseForbidden('Only an employee of the issuer, the applicant, or the beneficiary to the LC may modify it')
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if lc.issuer_approved and lc.beneficiary_approved:
                return JsonResponse({
                    'success':False,
                    'reason':'This LC has been approved by both the issuer and beneficiary, and may not be revoked'
                })
            elif lc.issuer.bankemployee_set.filter(email=request.user.username).exists() or lc.client.businessemployee_set.filter(email=request.user.username).exists():
                # TODO should probably notify everybody of this deletion
                lc.delete()
                return JsonResponse({
                    'success':True
                })
            else:
                return HttpResponseForbidden('Only an employee of either the issuer or applicant to the LC may delete it')
        else:
            return HttpResponseForbidden('Must be logged in to delete an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST, PUT, DELETE")

@csrf_exempt
def notify_teammate(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                json_data = json.loads(request.body)
                note = lc.issuer.bankemployee_set.get(email=request.user.username).name + ' would you like to examine the LC at https://bountium.org/lc/' + lc_id
                if 'note' in json_data:
                    note = json_data['note']
                send_mail(
                    lc.issuer.bankemployee_set.get(email=request.user.username).name + ' sent a notification on Bountium',
                    note,
                    'steve@bountium.org',
                    [json_data['to_notify']],
                    fail_silently=False,
                )
            # TODO do we want to let the client or beneficiary notify their teammates to?
            #elif lc.client.businessemployee_set...
            else:
                return HttpResponseForbidden("Only employees of this LC's issuing bank may notify teammates about it")
        else:
            return HttpResponseForbidden("Must be logged in to notify teammates about an LC")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def evaluate_lc(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                lc.issuer_approved = json_data['approve']
                if 'complaints' in json_data:
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the issuer said: ' + json_data['complaints']
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'evaluated_on':datetime.datetime.now()
                })
            elif lc.beneficiary.businessemployee_set(email=request.user.username).exists():
                lc.beneficiary_approved = json_data['approve']
                if 'complaints' in json_data:
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the beneficiary said: ' + json_data['complaints']
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'evaluated_on':datetime.datetime.now()
                })
            else:
                return HttpResponseForbidden('Only the issuer or beneficiary to an LC may evaluate it')
        else:
            return HttpResponseForbidden('You must be logged in to evaluate an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# TODO authentication
@csrf_exempt
def cr_doc_reqs(request, lc_id):
    if request.method == 'GET':
        this_lcs_doc_reqs = LC.objects.get(id=lc_id)
        return JsonResponse(list(this_lcs_doc_reqs.values()), safe=False)
    elif request.method == 'POST':
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                try:
                    lc = LCs.objects.get(lc=lc_id)
                except LC.DoesNotExist:
                    return Http404("No lc with id " + lc_id)
                json_data = json.loads(request.body)
                lc.documentaryrequirement_set.create(doc_name=json_data['doc_name'], link_to_submitted_doc = json['link_to_submitted_doc'])
                return JsonResponse({
                    'doc_req_id' : lc.documentaryrequirement_set.get(doc_name=json_data['doc_name']).id
                })
            else:
                return HttpResponseForbidden("Only an employee of the beneficiary to this LC may create documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to create documentary requirements")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

@csrf_exempt
def rud_doc_req(request, lc_id, doc_req_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        return Http404("No doc req with id " + doc_req_id + " associated with the lc with id " + lc_id)
    if request.method == 'GET':
        return JsonResponse(model_to_dict(doc_req))
    elif request.method == 'PUT':
        json_data = json.loads(request.body)
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                if 'due_date' in json_date:
                    if json_data['due_date'] > lc.due_date:
                        doc_req.modified_and_awaiting_beneficiary_approval = True
                    doc_req.due_date = json_data['due_date']
                if 'required_values' in json_data:
                    if json_data['required_values'] != lc.required_values:
                        doc_req.modified_and_awaiting_beneficiary_approval = True
                    doc_req.required_values = json_data['required_values']
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'modified_and_notified_on':str(datetime.datetime.now()),
                    'doc_req':model_to_dict(doc_req)
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                doc_req.link_to_submitted_doc = json_data['link_to_submitted_doc']
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'submitted_and_notified_on':str(datetime.datetime.now()),
                    'doc_req':model_to_dict(doc_req)
                })
            else:
                return HttpResponseForbidden("Only an employee of the bank which issued this LC, or the beneficiary of this LC, may update documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement deletion")
    elif request.method == 'DELETE':
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                doc_req.delete()
                return JsonResponse({
                    'success':True,
                    'doc_reqs':list(lc.documentaryrequirement_set)
                })
            else:
                return HttpResponseForbidden("Only an employee of the bank which issued this LC may delete documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement deletion")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, PUT, DELETE")

# TODO should we let clients evaluate doc reqs to or just the issuer?
@csrf_exempt
def evaluate_doc_req(request, lc_id, doc_req_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        return Http404("No doc req with id " + doc_req_id + " associated with the lc with id " + lc_id)
    if request.method == 'POST':
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                doc_req.satisfied = json_data['approve']
                if 'complaints' in json_data:
                    doc_req.submitted_doc_complaints = json_data['complaints']
                return JsonResponse({
                    'success':True,
                    'doc_reqs':list(lc.documentaryrequirement_set)
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                doc_req.modified_and_awaiting_beneficiary_approval = json_data['approve']
                if 'complaints' in json_data:
                    doc_req.modification_complaints = json_data['complaints']
                return JsonResponse({
                    'success':True,
                    'doc_reqs':list(lc.documentaryrequirement_set)
                })
            else:
                return HttpResponseForbidden("Only an employee of the bank which issued this LC, or an employee to the beneficiary of thsi LC, may evaluate documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement evaluation")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def request_lc(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set(email=request.user.username).exists():
                lc.requested = True
                return JsonResponse({
                    'success':True,
                    'requested_on':datetime.datetime.now()
                })
            else:
                return HttpResponseForbidden('Only the beneficiary to an LC may request payment on it')
        else:
            return HttpResponseForbidden('You must be logged in to request payment on an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def draw_lc(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set(email=request.user.username).exists():
                lc.drawn = True
                return JsonResponse({
                    'success':True,
                    'drawn_on':datetime.datetime.now()
                })
            else:
                return HttpResponseForbidden('Only the beneficiary to an LC may request payment on it')
        else:
            return HttpResponseForbidden('You must be logged in to request payment on an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def payout_lc(request, lc_id):
    try:
        lc = LCs.objects.get(lc=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set(email=request.user.username).exists():
                lc.paid_out = True
                return JsonResponse({
                    'success':True,
                    'marked_paid_out_on':datetime.datetime.now()
                })
            else:
                return HttpResponseForbidden('Only the issuer of an LC may mark it paid out')
        else:
            return HttpResponseForbidden('You must be logged in to mark an LC as paid out')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# TODO handle doc reqs!
def set_lc_specifications(lc, json_data):
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

    # 3. save and return back!
    lc.save()
