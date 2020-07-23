import json
import re
import time
import uuid
from decimal import *
from json import JSONDecodeError

import numpy as np
import pycountry
import requests
import textract
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, \
    Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from business.models import ApprovedCredit, AuthorizedBanks
from lc.forms import BankInitiatedLC
from util import update_django_instance_with_subset_json
from .models import *
from .values import commercial_invoice_form, multimodal_bl_form, import_permits


# TODO only handling DigitalLCs for now
# TODO none of these distinguish between different employees within each party - only verifying that you are A
#  employee of the appropriate party to perform an action
# TODO keyerrors... unhandled key errors everywhere
# TODO currently only allowing the issuer, client, and beneficiary to do stuff - ignoring the account_party and
#  advising_bank, even though we are setting() them
# TODO for claiming beneficiary / advising_bank / account_party status, we should somehow ensure the claimant is the
#  party they claim to be.
# could check logged_in_user.employer.name == name submitted by applicant
# Could let client or issuer approve
# TODO ensure the links in all send_mail(s are accurate per ryan


@csrf_exempt
def cr_lcs(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404(f"No bank with id {bank_id} found")
    if request.method == "GET":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Must be logged in to see your bank's issued LCs")
        if not bank.bankemployee_set.filter(email=request.user.username).exists():
            return HttpResponseForbidden("Must be an employee of the bank to see all the LCs this bank has issued")
        to_return = []
        for lc in DigitalLC.objects.filter(issuer=bank):
            to_return.append(lc.to_dict())
        return JsonResponse(to_return, safe=False)
    elif request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Must be logged in to create an LC")
        try:
            json_data = json.loads(request.body)
        except JSONDecodeError:
            return HttpResponseBadRequest("missing or malformed request body")
        if bank.bankemployee_set.filter(email=request.user.username).exists():
            validator = BankInitiatedLC(json_data)
            if not validator.is_valid():
                return HttpResponseBadRequest(validator.errors.as_json())
            # 1. create the initial LC instance with parties, creating new
            #    accounts/inviting registrants where applicable
            lc = DigitalLC(issuer=bank)
            lc.save()
            lc.tasked_issuer_employees.add(bank.bankemployee_set.get(email=request.user.username))
            business_exists = Business.objects.filter(name=json_data['applicant_name']).exists()
            if business_exists:
                if lc.client.businessemployee_set.filter(email=json_data['applicant_employee_contact']).exists():
                    lc.tasked_client_employees.add(
                            Business.objects.businessemployee_set.get(email=json_data['applicant_employee_contact']))
                else:
                    # TODO decide - either
                    # send an email 'set your employee account up at <insert employee registration link>'
                    # or return an error, since the business exists, so it
                    # was probably a mistyped email
                    pass
                # TODO mail the business inviting them to fill the app out
                # TODO create the business, and invite applicant_employee_contact to register then fill out the
                # LC app
            send_mail(
                    f"{bank.bankemployee_set.get(email=request.user.username).name} has started your LC for you on "
                    f"Bountium!",
                    f"{'' if business_exists else '1. Set your business up at https://app.bountium.org/business/register, 2.'} Fill out your app at https://app.bountium.org/business/finishApp/{lc.id}",
                    "steve@bountium.org",
                    [json_data['applicant_employee_contact']],
                    fail_silently=False,
            )
            # 3. return success & the created lc
            return JsonResponse({
                'success': True,
                'created_lc': lc.to_dict()
            })
        elif BusinessEmployee.objects.filter(email=request.user.username).exists():

            employee_applying = BusinessEmployee.objects.get(email=request.user.username)
            # 1. for each of the default questions,
            #   a. get the value and
            #   b. do something with it
            #   c. remove it from the list

            if not employee_applying.authorized_banks.filter(bank=bank).exists():
                bank_auth = AuthorizedBanks(bank=bank)
                bank_auth.save()
                employee_applying.authorized_banks.add(bank_auth)
                employee_applying.save()
            # Questions 1 and 2
            applicant = json_data.pop('applicant')
            if (applicant['name'] != employee_applying.employer.name
                    or applicant['address'] != employee_applying.employer.address):
                return HttpResponseForbidden(
                        "You may only apply for an LC on behalf of your own business. Check the submitted "
                        "applicant name and applicant address for correctness - one or both differed from the "
                        "business name and address associated with this user\'s employer")
            lc = DigitalLC(issuer=bank, client=employee_applying.employer,
                           application_date=datetime.datetime.now().date())
            lc.save()
            lc.tasked_client_employees.add(employee_applying)

            set_lc_specifications(lc, json_data, employee_applying)

            # 3. notify a bank employee maybe? TODO decide

            # 4. save and return back!
            return JsonResponse({
                'success': True,
                'created_lc': lc.to_dict()
            })

        else:
            return HttpResponseForbidden(
                    "You may only create LCs with the bank of the ID at this endpoint by being a member of this "
                    "bank, or by being a business requesting an LC from this bank")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")


@csrf_exempt
def rud_lc(request, lc_id):
    # TODO, technically GET-ing this endpoint should equally support PdfLC and DigitalLC
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with that id")
    if request.method == "GET":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Must be logged in to view an LC")
        elif employed_by_main_party_to_lc(lc, request.user.username):
            lc_return = lc.to_dict()
            # filter if it is the client
            if lc.client.businessemployee_set.filter(email=request.user.username).exists():
                lc_return['beneficiary']['annual_cashflow'] = None
                lc_return['beneficiary']['balance_available'] = None
                lc_return['beneficiary']['approved_credit'] = None

            # filter if it is the beneficiary or advisor
            elif lc.beneficiary.businessemployee_set.filter(
                    email=request.user.username).exists() or lc.advising_bank.bankemployee_set.filter(
                    email=request.user.username).exists():
                lc_return['client']['annual_cashflow'] = None
                lc_return['client']['balance_available'] = None
                lc_return['client']['approved_credit'] = None
            return JsonResponse(lc_return)
        else:
            return HttpResponseForbidden(
                    'Only an employee of the issuer, the applicant, or the beneficiary to the LC may view it')
    elif request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Must be logged in to create an LC")
        try:
            json_data = json.loads(request.body)
        except JSONDecodeError:
            return HttpResponseBadRequest("missing or malformed request body")
        if not lc.client.businessemployee_set.filter(email=request.user.username).exists():
            return HttpResponseForbidden("Only employees of the business applying for this LC can create the LC")

        # The client's employee is responding to an LC application their bank started for them
        employee_applying = lc.client.businessemployee_set.get(email=request.user.username)
        if lc.issuer is None:
            return HttpResponseBadRequest("there is no issuer for this LC")
        lc.application_date = datetime.datetime.now().date()
        set_lc_specifications(lc, json_data, employee_applying)
        return JsonResponse({
            'success': True
        })
    elif request.method == "PUT":
        if not request.user.is_authenticated:
            return HttpResponseBadRequest("Must be logged in to update an LC")
        if lc.issuer_approved and lc.beneficiary_approved and lc.client_approved:
            return JsonResponse({
                'success': False,
                'reason': 'This LC has been approved by all parties, and may not be modified'
            })
        try:
            json_data = json.loads(request.body)
        except JSONDecodeError:
            return HttpResponseBadRequest("missing or malformed request body")
        if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
            update_lc(lc=lc, json_data=json_data, client_approved=False, beneficiary_approved=False,
                      issuer_approved=True, user_type="issuer")
        elif lc.beneficiary is not None and lc.beneficiary.businessemployee_set.filter(
                email=request.user.username).exists():
            update_lc(lc=lc, json_data=json_data, client_approved=False, beneficiary_approved=True,
                      issuer_approved=False, user_type="beneficiary")
        elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
            update_lc(lc=lc, json_data=json_data, client_approved=True, beneficiary_approved=False,
                      issuer_approved=False, user_type="client")
        else:
            return HttpResponseForbidden(
                    'Only an employee of the issuer, the applicant, or the beneficiary to the LC may modify it')
        return JsonResponse({
            'success': True,
            'updated_lc': lc.to_dict()
        })
    elif request.method == "DELETE":
        if not request.user.is_authenticated:
            return HttpResponseForbidden('Must be logged in to delete an LC')
        if not (lc.issuer.bankemployee_set.filter(
                email=request.user.username).exists() or lc.client.businessemployee_set.filter(
                email=request.user.username).exists()):
            return HttpResponseForbidden(
                    'Only an employee of either the issuer or applicant to the LC may delete it')
        if lc.issuer_approved and lc.beneficiary_approved and lc.client_approved:
            return JsonResponse({
                'success': False,
                'reason': 'This LC has been approved by all parties, and may not be revoked'
            })
        else:
            # TODO should probably notify everybody of this deletion
            lc.delete()
            return JsonResponse({
                'success': True
            })
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST, PUT, DELETE")


def update_lc(lc, json_data, client_approved, beneficiary_approved, issuer_approved, user_type):
    # TODO would be good to somehow mark changes from the prev version...
    update_django_instance_with_subset_json(json_data['lc'], lc)
    if 'hold_status' not in json_data or not json_data['hold_status']:
        lc.client_approved = client_approved,
        lc.beneficiary_approved = beneficiary_approved
        lc.issuer_approved = issuer_approved
        if 'other_instructions' in json_data and pycountry.countries.lookup(
                lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
                lc.client.country).alpha_2 == 'US':
            BoycottLanguage.objects.filter(lc=lc).delete()
        boycott_phrases = boycott_language(lc.other_instructions)
        for phrase in boycott_phrases:
            BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()
    if 'latest_version_notes' in json_data:
        lc.latest_version_notes = \
            f'On {str(datetime.datetime.now())} the {user_type} said: {json_data["latest_version_notes"]}'
    if 'comment' in json_data:
        comment = json_data['comment']
        if 'action' not in comment or 'message' not in comment:
            return HttpResponseBadRequest(
                    "The given comment must have an 'action' field and a 'message' field")
        if user_type == "issuer":
            respondable = "client"
        elif user_type == "client":
            respondable = "issuer"
        elif user_type == "beneficiary":
            respondable = "issuer"
        else:
            raise ValueError("invalid user_type")
        created = Comment(lc=lc, author_type=user_type, action=comment['action'],
                          date=datetime.datetime.now(), message=comment['message'],
                          issuer_viewable=True, client_viewable=True, respondable=respondable)
        created.save()
    lc.save()
    # TODO notify parties


@csrf_exempt
def get_filtered_lcs(request, bank_id, filter):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with that id")
    to_return = []
    filter_vals = {
        'live': Q(client_approved=True, issuer_approved=True, beneficiary_approved=True),
        'awaiting_issuer_approval': Q(issuer_approved=False),
        'awaiting_client_approval': Q(client_approved=False),
        'awaiting_beneficiary_approval': Q(beneficiary_approved=False)
    }
    for lc in DigitalLC.objects.filter(filter_vals[filter], issuer=bank, paid_out=False):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_filtered_lcs_advisor(request, bank_id, filter):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with that id")
    to_return = []
    filter_vals = {
        'live': Q(client_approved=True, issuer_approved=True, beneficiary_approved=True),
        'awaiting_issuer_approval': Q(issuer_approved=False),
        'awaiting_client_approval': Q(client_approved=False),
        'awaiting_beneficiary_approval': Q(beneficiary_approved=False)
    }
    for lc in DigitalLC.objects.filter(filter_vals[filter], advising_bank=bank, paid_out=False):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_by_client(request, business_id):
    return get_lcs_by(business_id, "client")


@csrf_exempt
def get_lcs_by_beneficiary(request, business_id):
    return get_lcs_by(business_id, "beneficiary")


def get_lcs_by(business_id, filter_type):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        raise Http404("No business with that id")
    to_return = []
    filtered_lcs = DigitalLC.objects.filter(
            beneficiary=business) if filter_type == "beneficiary" else DigitalLC.objects.filter(client=business)
    for lc in filtered_lcs:
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)


def form_note(lc, json_data, sending_user):
    note = sending_user.name + ' would like you to examine the LC at https://app.bountium.org/lc/' + lc.id
    if 'note' in json_data:
        note = json_data['note']
    send_mail(
            sending_user.name + ' sent a notification on Bountium',
            note,
            'steve@bountium.org',
            [json_data['to_notify']],
            fail_silently=False,
    )


# TODO the following 3 functions, claim_x, should be abstracted & parameterised
@csrf_exempt
def claim_relation_to_lc(request, lc_id, relation):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return HttpResponseForbidden('You must be logged in to claim an LC relation')
        if relation == 'beneficiary':
            if BusinessEmployee.objects.filter(email=request.user.username).exists():
                beneficiary_employee = BusinessEmployee.objects.get(email=request.user.username)
                lc.beneficiary = beneficiary_employee.employer
                lc.tasked_beneficiary_employees.add(beneficiary_employee)
                lc.save()
            else:
                return HttpResponseForbidden('Only a business registered on Bountium may claim beneficiary status')
        elif relation == 'account_party':
            if BusinessEmployee.objects.filter(email=request.user.username).exists():
                account_party_employee = BusinessEmployee.objects.get(email=request.user.username)
                lc.account_party = account_party_employee.employer
                lc.tasked_account_party_employees.add(account_party_employee)
                lc.save()
            else:
                return HttpResponseForbidden(
                        'Only a business registered on Bountium may claim account party status')
        elif relation == 'advising':
            if BankEmployee.objects.filter(email=request.user.username).exists():
                advising_bank_employee = BankEmployee.objects.get(email=request.user.username)
                lc.advising_bank = advising_bank_employee.bank
                lc.tasked_advising_bank_employees.add(advising_bank_employee)
                lc.save()
            else:
                return HttpResponseForbidden('Only a bank registered on Bountium may claim advising bank status')
        else:
            raise Http404(
                    'Bountium is only supporting the LC relations "beneficiary", "account_party", and "advising"')
        # TODO notify parties
        return JsonResponse({
            'success': True,
            'claimed_on': str(datetime.datetime.now())
        })
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")


@csrf_exempt
def cr_doc_reqs(request, lc_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Must be logged in to view an LC")
        elif employed_by_main_party_to_lc(lc, request.user.username):
            this_lcs_doc_reqs = LC.objects.get(id=lc_id).documentaryrequirement_set
            return JsonResponse(list(this_lcs_doc_reqs.values()), safe=False)
        else:
            return HttpResponseForbidden(
                    'Only an employee of the issuer, the client, or the beneficiary to the LC may view its '
                    'documentary requirements')
    elif request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden("You must be logged in to create documentary requirements")
        elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
            try:
                json_data = json.loads(request.body)
            except JSONDecodeError:
                return HttpResponseBadRequest("missing or malformed request body")
            lc.documentaryrequirement_set.create(doc_name=json_data['doc_name'],
                                                 link_to_submitted_doc=json_data['link_to_submitted_doc'])
            lc.save()
            return JsonResponse({
                'doc_req_id': lc.documentaryrequirement_set.get(doc_name=json_data['doc_name']).id
            })
        else:
            return HttpResponseForbidden(
                    "Only an employee of the beneficiary to this LC may create documentary requirements")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")


# check the box saying bank approves the application


# TODO typed: allow users to update specific fields of required doc reqs
@csrf_exempt
def rud_doc_req(request, lc_id, doc_req_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        raise Http404("No doc req with id " + doc_req_id + " associated with the lc with id " + lc_id)
    if request.method == 'GET':
        if request.user.is_authenticated:
            if employed_by_main_party_to_lc(lc, request.user.username):
                return JsonResponse(promote_to_child(doc_req).to_dict())
            else:
                return HttpResponseForbidden(
                        'Only an employee of the issuer, the client, or the beneficiary to the LC may view its '
                        'documentary requirements')
        else:
            return HttpResponseForbidden("Must be logged in to view an LC")
    elif request.method == 'PUT':
        # TODO typed: update this to set fields that matter for typed doc reqs
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                json_data = json.loads(request.body)
                if 'due_date' in json_data:
                    if json_data['due_date'] > doc_req.due_date:
                        doc_req.modified_and_awaiting_beneficiary_approval = True
                    doc_req.due_date = json_data['due_date']
                if 'required_values' in json_data:
                    if json_data['required_values'] != doc_req.required_values:
                        doc_req.modified_and_awaiting_beneficiary_approval = True
                    doc_req.required_values = json_data['required_values']
                doc_req.save()
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success': True,
                    'modified_and_notified_on': str(datetime.datetime.now()),
                    'doc_req': doc_req.to_dict()
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                json_data = json.loads(request.body)
                if 'due_date' in json_data:
                    """ TODO we need something like this:
                    if json_data['due_date'] > doc_req.due_date:
                        doc_req.modified_and_awaiting_issuer_approval = True"""
                    doc_req.due_date = json_data['due_date']
                if 'required_values' in json_data:
                    """ TODO we need something like this:
                    if json_data['required_values'] != doc_req.required_values:
                        doc_req.modified_and_awaiting_issuer_approval = True"""
                    doc_req.required_values = json_data['required_values']
                doc_req.save()
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success': True,
                    'modified_and_notified_on': str(datetime.datetime.now()),
                    'doc_req': doc_req.to_dict()
                })
            else:
                return HttpResponseForbidden(
                        "Only an employee of the bank which issued this LC, or the beneficiary of this LC, may update "
                        "documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement redline")
    elif request.method == 'POST':
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                # issuer uploading on behalf of the bene (presumably a scan or something)
                if request.content_type == 'application/pdf':
                    s3 = boto3.resource('s3')
                    submitted_doc_name = lc.issuer.name + "-submitted-on-behalf-of-bene-on" + str(
                            datetime.datetime.now()) + ".pdf"
                    s3.Bucket('docreqs').put_object(Key=submitted_doc_name, Body=request.body)
                    doc_req.link_to_submitted_doc = "https://docreqs.s3.us-east-2.amazonaws.com/" + submitted_doc_name
                    doc_req.rejected = False
                    doc_req.save()
                    # TODO notify someone
                    return JsonResponse({
                        'success': True,
                        'submitted_and_notified_on': str(datetime.datetime.now()),
                        'doc_req': doc_req.to_dict()
                    })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                if request.content_type == 'application/pdf':
                    s3 = boto3.resource('s3')
                    submitted_doc_name = lc.beneficiary.name + "-submitted-on-" + str(datetime.datetime.now()) + ".pdf"
                    s3.Bucket('docreqs').put_object(Key=submitted_doc_name, Body=request.body)
                    doc_req.link_to_submitted_doc = "https://docreqs.s3.us-east-2.amazonaws.com/" + submitted_doc_name
                    doc_req.rejected = False
                    doc_req.save()
                    # TODO notify someone
                    return JsonResponse({
                        'success': True,
                        'submitted_and_notified_on': str(datetime.datetime.now()),
                        'doc_req': doc_req.to_dict()
                    })
                else:
                    json_data = json.loads(request.body)
                    doc_req = promote_to_child(doc_req)
                    update_django_instance_with_subset_json(json_data, doc_req)
                    doc_req.generate_pdf()
                    doc_req.save()
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'modified_and_notified_on': str(datetime.datetime.now()),
                        'doc_req': doc_req.to_dict()
                    })
            else:
                return HttpResponseForbidden(
                        "Only an employee of the bank which issued this LC, or the beneficiary of this LC, may submit "
                        "documentary requirement candidates")
        else:
            return HttpResponseForbidden("You must be logged in to submit a documentary requirement candidate")
    elif request.method == 'DELETE':
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                doc_req.delete()
                return JsonResponse({
                    'success': True,
                    'doc_reqs': lc.get_doc_reqs()
                })
            else:
                return HttpResponseForbidden(
                        "Only an employee of the bank which issued this LC may delete documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement deletion")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST, PUT, DELETE")


def promote_to_child(doc_req):
    if doc_req.type == 'commercial_invoice':
        return CommercialInvoiceRequirement.objects.get(id=doc_req.id)
    elif doc_req.type == 'multimodal_bill_of_lading':
        return MultimodalTransportDocumentRequirement.objects.get(id=doc_req.id)
    return doc_req


def employed_by_main_party_to_lc(lc, username):
    return (lc.issuer.bankemployee_set.filter(email=username).exists()
            or lc.client.businessemployee_set.filter(email=username).exists()
            or lc.beneficiary.businessemployee_set.filter(email=username).exists()
            or lc.advising_bank.bankemployee_set.filter(email=username).exists())


# TODO should we let clients evaluate doc reqs to or just the issuer?
@csrf_exempt
def evaluate_doc_req(request, lc_id, doc_req_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        raise Http404("No doc req with id " + doc_req_id + " associated with the lc with id " + lc_id)
    if request.method == 'POST':
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                doc_req.satisfied = json_data['approve']
                doc_req.rejected = (not json_data['approve'])
                if 'complaints' in json_data:
                    doc_req.submitted_doc_complaints = json_data['complaints']
                doc_req.save()
                lc.save()
                return JsonResponse({
                    'success': True,
                    'doc_reqs': lc.get_doc_reqs()
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                doc_req.modified_and_awaiting_beneficiary_approval = json_data['approve']
                if 'complaints' in json_data:
                    doc_req.modification_complaints = json_data['complaints']
                doc_req.save()
                lc.save()
                return JsonResponse({
                    'success': True,
                    'doc_reqs': lc.get_doc_reqs()
                })
            # TODO to include status later
            elif lc.advising_bank is not None and lc.advising_bank.bankemployee_set.filter(
                    email=request.user.username).exists() and lc.confirmation_means == "Confirmation by a bank " \
                                                                                       "selected by the beneficiary" \
                    and lc.credit_expiry_location_id == lc.advising_bank_id:
                doc_req.satisfied = json_data['approve']
                doc_req.rejected = (not json_data['approve'])
                if 'complaints' in json_data:
                    doc_req.submitted_doc_complaints = json_data['complaints']
                doc_req.save()
                lc.save()
                return JsonResponse({
                    'success': True,
                    'doc_reqs': lc.get_doc_reqs()
                })
            else:
                return HttpResponseForbidden(
                        "Only an employee of the bank which issued this LC, an employee to the beneficiary of this "
                        "LC, or a special advisor may evaluate documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement evaluation")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")


@csrf_exempt
def mark_lc_something(request, lc_id, state_to_mark):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            if state_to_mark == 'request':
                if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                    lc.requested = True
                    lc.save()
                    return JsonResponse({
                        'success': True,
                        'requested_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only the beneficiary to an LC may request payment on it')
            elif state_to_mark == 'draw':
                if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                    lc.drawn = True
                    lc.save()
                    return JsonResponse({
                        'success': True,
                        'drawn_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only the beneficiary to an LC may request payment on it')
            elif state_to_mark == 'payout':
                if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                    lc.paid_out = True
                    lc.save()
                    return JsonResponse({
                        'success': True,
                        'marked_paid_out_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only the issuer of an LC may mark it paid out')
            elif state_to_mark == 'evaluate':
                json_data = json.loads(request.body)
                if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                    lc.issuer_approved = json_data['approve']
                    if 'complaints' in json_data and json_data['complaints'] != '':
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the issuer said: ' + \
                                                  json_data['complaints']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'evaluated_on': str(datetime.datetime.now())
                    })
                elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                    lc.beneficiary_approved = json_data['approve']
                    if 'complaints' in json_data and json_data['complaints'] != '':
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the beneficiary said: ' + \
                                                  json_data['complaints']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'evaluated_on': str(datetime.datetime.now())
                    })
                elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                    lc.client_approved = json_data['approve']
                    if 'complaints' in json_data and json_data['complaints'] != '':
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the client said: ' + \
                                                  json_data['complaints']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'evaluated_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only the issuer, beneficiary, or client to an LC may evaluate it')
            elif state_to_mark == 'notify':
                json_data = json.loads(request.body)
                if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                    form_note(lc, json_data, lc.issuer.bankemployee_set.get(email=request.user.username))
                    lc.tasked_issuer_employees.add(BankEmployee.objects.get(email=json_data['to_notify']))
                elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                    form_note(lc, json_data, lc.client.businessemployee_set.get(email=request.user.username))
                    lc.tasked_client_employees.add(BusinessEmployee.objects.get(email=json_data['to_notify']))
                elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                    form_note(lc, json_data, lc.beneficiary.businessemployee_set.get(email=request.user.username))
                    lc.tasked_beneficiary_employees.add(BusinessEmployee.objects.get(email=json_data['to_notify']))
                else:
                    return HttpResponseForbidden(
                            "Only employees of this LC's issuer, client, or beneficiary may notify teammates about it")
            else:
                raise Http404(
                        'Bountium only supports marking an LC\'s status with the actions "request", "draw", '
                        '"evaluate", '
                        'and "payout"')
        else:
            return HttpResponseForbidden('You must be logged in to update the status on an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")


@csrf_exempt
def get_dr_file(request, lc_id, doc_req_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        raise Http404("No doc req with that id associated with this lc")
    if request.method == 'GET':
        if request.user.is_authenticated:
            if employed_by_main_party_to_lc(lc, request.user.username):
                submitted_doc_name = doc_req.link_to_submitted_doc[
                                     doc_req.link_to_submitted_doc.index('aws.com/') + len('aws.com/'):]
                s3 = boto3.resource('s3')
                s3client = boto3.client('s3')
                file_size = s3client.head_object(Bucket='docreqs', Key=submitted_doc_name)['ContentLength']
                the_file = s3.Bucket('docreqs').download_file(Filename='/tmp/' + submitted_doc_name,
                                                              Key=submitted_doc_name)
                while os.path.getsize('/tmp/' + submitted_doc_name) < file_size:
                    time.sleep(1)
                res = HttpResponse(open('/tmp/' + submitted_doc_name, 'rb'))
                res['Content-Type'] = "binary/octet-stream"
                return res
            else:
                return HttpResponseForbidden(
                        'Only an employee of the issuer, the client, or the beneficiary to the LC may view its '
                        'documentary requirements\' submitted candidate docs')
        else:
            return HttpResponseForbidden('You must be logged in to get a documentary requirement\'s submitted file')
    else:
        return HttpResponseBadRequest("This endpoint only supports GET")


@csrf_exempt
def autopopulate_creatable_dr(request, lc_id, doc_req_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    try:
        doc_req = promote_to_child(lc.documentaryrequirement_set.get(id=doc_req_id))
    except DocumentaryRequirement.DoesNotExist:
        raise Http404("No doc req with that id associated with this lc")
    return JsonResponse(doc_req.suggested_field_vals())


@csrf_exempt
def supported_creatable_docs(request):
    return JsonResponse([
        'commercial_invoice', 'multimodal_bl'
    ], safe=False)


@csrf_exempt
def supported_creatable_doc(request, doc_type):
    if doc_type == 'commercial_invoice':
        return JsonResponse(commercial_invoice_form, safe=False)
    elif doc_type == 'multimodal_bl':
        return JsonResponse(multimodal_bl_form, safe=False)
    else:
        raise Http404("No supported creatable document with that doc_type")


@csrf_exempt
def digital_app_templates(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            try:
                user = BusinessEmployee.objects.get(email=request.user.username)
                where = {k: v for k, v in request.GET.items()}
                where['user'] = user
                if 'beneficiary_name' in where:
                    where['beneficiary__contains'] = where.pop('beneficiary_name')
                templates = DigitalLCTemplate.objects.filter(**where).values('id', 'template_name')
                return JsonResponse(list(templates), safe=False)
            except BusinessEmployee.DoesNotExist:
                return HttpResponseForbidden("Must be a business employee to see LC templates")
        else:
            return HttpResponseForbidden("Must be logged in to see your LC templates")
    elif request.method == "POST":
        if request.user.is_authenticated:
            try:
                user = BusinessEmployee.objects.get(email=request.user.username)
                json_data = json.loads(request.body)
                if 'template_name' not in json_data:
                    return HttpResponseBadRequest("Must provide a template name")
                template = DigitalLCTemplate(user=user, template_name=json_data['template_name'])
                template.to_model(json_data)
                try:
                    template.save()
                    return JsonResponse({
                        'success': True,
                        'created_lc_template': model_to_dict(template)
                    })
                except IntegrityError as e:
                    return HttpResponseBadRequest("A template with this name already exists")
            except BusinessEmployee.DoesNotExist:
                return HttpResponseForbidden("Must be a business employee to create an LC template")
        else:
            return HttpResponseForbidden("Must be logged in to create an LC template")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")


@csrf_exempt
def digital_app_template(request, template_id):
    if request.method == "GET":
        if request.user.is_authenticated:
            try:
                user = BusinessEmployee.objects.get(email=request.user.username)
                try:
                    template = DigitalLCTemplate.objects.get(id=template_id)
                    if user != template.user:
                        return HttpResponseForbidden("Must be an authorized user for this template")
                    return JsonResponse(model_to_dict(template))
                except DigitalLCTemplate.DoesNotExist:
                    return HttpResponseBadRequest("The template ID given does not exist")
            except BusinessEmployee.DoesNotExist:
                return HttpResponseForbidden("Must be a business employee to see an LC template")
        else:
            return HttpResponseForbidden("Must be logged in to see an LC template")
    elif request.method == "PUT":
        if request.user.is_authenticated:
            try:
                user = BusinessEmployee.objects.get(email=request.user.username)
                try:
                    template = DigitalLCTemplate.objects.get(id=template_id)
                    if user != template.user:
                        return HttpResponseForbidden("Must be an authorized user for this template")
                    json_data = json.loads(request.body)
                    template.to_model(json_data)
                    template.save()
                    return JsonResponse({
                        'success': True,
                        'updated_lc_template': model_to_dict(template)
                    })
                except DigitalLCTemplate.DoesNotExist:
                    return HttpResponseBadRequest("The template ID given does not exist")
            except BusinessEmployee.DoesNotExist:
                return HttpResponseForbidden("Must be a business employee to update an LC template")
        else:
            return HttpResponseForbidden("Must be logged in to update an LC template")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, PUT")


@csrf_exempt
def total_credit(request, business_id):
    if request.method == "GET":
        if request.user.is_authenticated:
            try:
                user = BankEmployee.objects.get(email=request.user.username)
                business = Business.objects.get(id=business_id)
                apps = list(DigitalLC.objects.filter(issuer=user.bank, client=business, issuer_approved=True).values(
                        'credit_amt', 'cash_secure'))
                sum = Decimal(0)
                for app in apps:
                    credit = app['credit_amt']
                    cash_secure = app['cash_secure']
                    if credit is not None:
                        sum += credit
                    if cash_secure is not None:
                        sum -= cash_secure
                return JsonResponse(sum, safe=False)
            except BankEmployee.DoesNotExist:
                return HttpResponseForbidden("Must be a bank employee to see a business's total credit")
            except BusinessEmployee.DoesNotExist:
                return HttpResponseForbidden("No business found for the given id")
        else:
            return HttpResponseForbidden("Must be logged in to see a business's total credit")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, PUT")


@csrf_exempt
def ofac(beneficiary_name, lc):
    combos = business_name_combinations(beneficiary_name)
    combo_chunks = [combos[i:i + 200] for i in range(0, len(combos), 200)]
    sdn_matches = []
    for chunk in combo_chunks:
        sdn_matches += list(SpeciallyDesignatedNational.objects.filter(
                Q(cleansed_name__in=chunk) | Q(speciallydesignatednationalalternate__cleansed_name__in=chunk,
                                               speciallydesignatednationalalternate__type__in=["aka", "fka"])))
    sdn_matches = set(sdn_matches)
    for match in sdn_matches:
        lc.ofac_sanctions.add(match)
        lc.save()


@csrf_exempt
def check_file_for_boycott(request):
    file_name = str(uuid.uuid4()) + ".pdf"
    with open("/tmp/" + file_name, "wb+") as received_file:
        received_file.write(request.body)
    text = textract.process("/tmp/" + file_name)
    print(text)
    return JsonResponse(list(map(lambda bytes: str(bytes), boycott_language(str(text)))), safe=False)


@csrf_exempt
def clients_by_bank(request, bank_id):
    try:
        Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with that ID")
    to_return = []
    for lc in DigitalLC.objects.filter(issuer_id=bank_id):
        if lc.client.to_dict() not in to_return:
            to_return.append(lc.client.to_dict())
    return JsonResponse(to_return, safe=False)


@csrf_exempt
def check_text_for_boycott(request):
    json_data = json.loads(request.body)
    return JsonResponse(boycott_language(json_data.lc_text), safe=False)


def boycott_language(string):
    combos = ['Israel', 'Arab', 'boycott', 'blacklist']
    combos += combinations([['vessel', 'airplane', 'ship', 'craft', 'carrier', 'ship', 'port'],
                            ['allow', 'prohibit', 'authorize', 'permit', 'sanction', 'grant', 'license', 'admit',
                             'forbid', 'banned', 'barred', 'disallow']])
    regex = '|'.join(combos)
    matches = list(re.finditer(regex, string, re.IGNORECASE))
    index_set = set()
    for match in matches:
        beg = string.rfind('.', 0, match.start())
        beg = 0 if beg == -1 else beg + 2
        end = string.find('.', match.end())
        end = len(string) if end == -1 else end + 1
        index_set.add((beg, end))
    return list(map(lambda index: string[index[0]: index[1]], index_set))


def combinations(words):
    combos = []
    for outerWord in words[0]:
        for innerWord in words[1]:
            combos.append(outerWord + "(.)*" + innerWord)
            combos.append(innerWord + "(.)*" + outerWord)
    return combos


@csrf_exempt
def import_license(lc):
    hts_code = lc.hts_code
    # first check the entire code
    full_search = search_dict(hts_code)
    if full_search != '':
        lc.import_license_message = full_search
        lc.save()
        return
    # check the six code (more general code)
    six_search = search_dict(hts_code[:7])
    if six_search != '':
        lc.import_license_message = six_search
        lc.save()
        return

    # check the six code (more general code)
    four_search = search_dict(hts_code[:3])
    if four_search != '':
        lc.import_license_message = four_search
        lc.save()
        return
    # check the chapter
    chapter_search = search_dict(hts_code[:2])
    if chapter_search != '':
        lc.import_license_message = chapter_search
        lc.save()
        return
    lc.import_license_message = ''
    lc.save()
    return


def search_dict(abbrev_code):
    for k, v in import_permits.items():
        if abbrev_code in k:
            return v[0] + ': ' + v[1]
    return ''


def business_name_combinations(business_name):
    business_name = business_name.upper()
    combos = {business_name}
    suffixes = list(map(lambda suffix: suffix.upper(),
                        ['Agency', 'Gmbh', 'PA',
                         'and', 'Group', 'PC',
                         'Assn', 'Hotel', 'Pharmacy',
                         'Assoc', 'Hotels', 'PLC',
                         'Associates', 'Inc', 'PLLC',
                         'Association', 'Incorporated', 'Restaurant',
                         'Bank', 'International', 'SA',
                         'BV', 'Intl', 'Sales',
                         'Co', 'Limited', 'Service',
                         'Comp', 'LLC', 'Services',
                         'Company', 'LLP', 'Store',
                         'Corp', 'LP', 'Svcs',
                         'Corporation', 'Ltd', 'Travel',
                         'DMD', 'Manufacturing', 'Unlimited',
                         'Enterprises', 'Mfg', 'Holding']))
    for suffix in suffixes:
        to_remove = re.compile('(\s*)' + suffix)
        combos.add(to_remove.sub('', business_name).strip())
    additions = suffixes.copy()
    for outerSuffix in suffixes:
        for innerSuffix in suffixes:
            additions.append(outerSuffix + " " + innerSuffix)
    for addition in additions:
        combos.add(business_name + " " + addition)
    return list(combos)


def believable_price_of_goods(hts_code, unit_of_measure):
    hts_code = hts_code.replace(".", "")[:6]
    if GoodsInfo.objects.filter(hts_code=hts_code).exists():
        return
    unit_map = {
        "m^2": 2,
        "area in square meters": 2,
        "square meters": 2,
        "meters squared": 2,
        "thousands of kilowatt-hours": 3,
        "electrical energy in thousands of kilowatt-hours": 3,
        "1000 kwh": 3,
        "meters": 4,
        "m": 4,
        "length in meters": 4,
        "u": 5,
        "items": 5,
        "number of items": 5,
        "2u": 6,
        "pairs": 6,
        "number of pairs": 6,
        "l": 7,
        "liters": 7,
        "volume in liters": 7,
        "kg": 8,
        "kilograms": 8,
        "weight in kilograms": 8,
        "weight in kg": 8,
        "1000u": 9,
        "thousands of items": 9,
        "jeu": 10,
        "pack": 10,
        "packages": 10,
        "number of packages": 10,
        "12u": 11,
        "dozen of items": 11,
        "dozen": 11,
        "dozens": 11,
        "m3": 12,
        "cubic meters": 12,
        "meters cubed": 12,
        "volume in cubic meters": 12,
        "carat": 13,
        "carats": 13,
        "weight in carats": 13
    }
    unit_of_measure = unit_map[unit_of_measure.lower()]
    res = requests.get(
            "https://comtrade.un.org/api/get?max=500&type=C&freq=A&px=HS&ps=now&r=all&p=0&rg=1%2C2&cc=" +
            hts_code).json()
    data = []
    for trade in res['dataset']:
        if trade['qtCode'] == unit_of_measure and trade['TradeValue'] is not None and trade['TradeValue'] > 0:
            data.append(trade['TradeQuantity'] / trade['TradeValue'])
    if len(data) < 50:
        return
    GoodsInfo(hts_code=hts_code, standard_deviation=np.std(data), mean=np.mean(data),
              created_date=datetime.datetime.now()).save()


def sanction_approval(beneficiary_country, applicant_country):
    # convert common names one could input to standard country name
    # ISO codes https://gist.github.com/radcliff/f09c0f88344a7fcef373
    country_convert = {'Iran': 'IRAN, ISLAMIC REPUBLIC OF',
                       'Libya': 'LIBYAN ARAB JAMAHIRIYA',
                       'Palestine': 'Palestinian Territory, Occupied',
                       'Russia': 'RUSSIAN FEDERATION',
                       'Vatican City': 'Holy See (Vatican City State)',
                       'Venezuela': 'Venezuela, Bolivarian Republic of',
                       'Tanzania': 'Tanzania, United Republic of',
                       'Taiwan': 'Taiwan, Province of China',
                       'Macedonia': 'Macedonia, the former Yugoslav Republic of',
                       'South Korea': 'Korea, Republic of',
                       'North Korea': 'Korea, Democratic People\'s Republic of',
                       'Syria': 'Syrian Arab Republic',
                       'Bolivia': 'Bolivia, Plurinational State of'}
    if beneficiary_country in country_convert:
        beneficiary_country = country_convert[beneficiary_country]
    if applicant_country in country_convert:
        applicant_country = country_convert[applicant_country]

    # check if either of the countries were inputted incorrectly
    # TODO write a script that can convert common different spellings of countries to ones that can be looked up by
    #  pycountry
    try:
        beneficiary_country = pycountry.countries.lookup(beneficiary_country)
    except:
        return None
    try:
        applicant_country = pycountry.countries.lookup(applicant_country)
    except:
        return None
        # check that the bank is the US first and handle that case
    if applicant_country.alpha_2 == 'US':
        # catch violations
        violating_countries = {
            'MK': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'RS': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'BA': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'HR': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'ME': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'SI': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'AL': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'XK': 'https://www.treasury.gov/resource-center/sanctions/Documents/balkans.pdf',
            'BY': 'https://www.treasury.gov/resource-center/sanctions/Documents/belarus.pdf',
            'BI': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/burundi.aspx',
            'CF': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/car.aspx',
            'CO': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/drugs.pdf',
            'PS': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/pal_guide.pdf',
            'CU': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/cuba.aspx',
            'CD': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/drcongo.pdf',
            'IR': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/iran.aspx',
            'IQ': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/iraq.pdf',
            'LB': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/lebanon.pdf',
            'LY': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/libya.aspx',
            'ML': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/mali.aspx',
            'NI': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/nicaragua.aspx',
            'KP': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/nkorea.aspx',
            'SO': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/somalia.pdf',
            'SD': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/sudan.aspx',
            'SS': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/southsudan.pdf',
            'SY': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/syria.pdf',
            'UA': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/ukraine.pdf',
            'RU': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/ukraine.pdf',
            'VE': 'https://www.treasury.gov/resource-center/sanctions/Programs/pages/venezuela.aspx',
            'YE': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/yemen.pdf',
            'ZW': 'https://www.treasury.gov/resource-center/sanctions/Programs/Documents/zimb.pdf'
        }
        for country in violating_countries:
            if country == beneficiary_country.alpha_2:
                return violating_countries[beneficiary_country.alpha_2]

        # no country violations found
        return ''

        # check if they are in the EU and act accordingly
    COUNTRY_CODES_EU = [
        'AT', 'BE', 'BG', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR', 'DE', 'GR', 'HU',
        'IE', 'IT',
        'LV', 'LT', 'LU', 'MT', 'NL', 'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE',
        'GB']
    if applicant_country.alpha_2 in COUNTRY_CODES_EU:
        # check EU violations https://www.sanctionsmap.eu/#/main
        violating_countries = {
            'AF': 'https://www.sanctionsmap.eu/#/main/details/1/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'BY': 'https://www.sanctionsmap.eu/#/main/details/2/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'BA': 'https://www.sanctionsmap.eu/#/main/details/4/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'BI': 'https://www.sanctionsmap.eu/#/main/details/7/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'CF': 'https://www.sanctionsmap.eu/#/main/details/9/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'CN': 'https://www.sanctionsmap.eu/#/main/details/10/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'CD': 'https://www.sanctionsmap.eu/#/main/details/11/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'EG': 'https://www.sanctionsmap.eu/#/main/details/12/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'GN': 'https://www.sanctionsmap.eu/#/main/details/14/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'GW': 'https://www.sanctionsmap.eu/#/main/details/15/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'HT': 'https://www.sanctionsmap.eu/#/main/details/16/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'IR': 'https://www.sanctionsmap.eu/#/main/details/17/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'IQ': 'https://www.sanctionsmap.eu/#/main/details/19/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'LB': 'https://www.sanctionsmap.eu/#/main/details/21/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'LY': 'https://www.sanctionsmap.eu/#/main/details/23/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'ML': 'https://www.sanctionsmap.eu/#/main/details/42/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'MD': 'https://www.sanctionsmap.eu/#/main/details/25/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'ME': 'https://www.sanctionsmap.eu/#/main/details/28/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'MM': 'https://www.sanctionsmap.eu/#/main/details/8/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'NI': 'https://www.sanctionsmap.eu/#/main/details/48/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'KP': 'https://www.sanctionsmap.eu/#/main/details/20/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'RU': 'https://www.sanctionsmap.eu/#/main/details/26/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'RS': 'https://www.sanctionsmap.eu/#/main/details/27/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'SO': 'https://www.sanctionsmap.eu/#/main/details/29/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'SS': 'https://www.sanctionsmap.eu/#/main/details/30/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'SD': 'https://www.sanctionsmap.eu/#/main/details/31/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'SY': 'https://www.sanctionsmap.eu/#/main/details/32/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'TN': 'https://www.sanctionsmap.eu/#/main/details/33/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'TR': 'https://www.sanctionsmap.eu/#/main/details/49/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'UA': 'https://www.sanctionsmap.eu/#/main/details/37/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'VE': 'https://www.sanctionsmap.eu/#/main/details/44/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'YE': 'https://www.sanctionsmap.eu/#/main/details/39/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D',
            'ZW': 'https://www.sanctionsmap.eu/#/main/details/40/?search=%7B%22value%22:%22%22,'
                  '%22searchType%22:%7B%7D%7D'}

        for country in violating_countries:
            if country == beneficiary_country.alpha_2:
                return violating_countries[beneficiary_country.alpha_2]

        # no country violations found
        return ''

    return None


# TODO should probably log received checkbox or radio values that are not one
# of the options they're supposed to be - thats an error, but easily fixable if
# we know thats what happened
def set_lc_specifications(lc, json_data, employee_applying):
    # Questions 3 and 4
    beneficiary = json_data.pop('beneficiary', None)
    beneficiary_name = beneficiary.pop('name', None)
    beneficiary_address = beneficiary.pop('address', None)
    beneficiary_country = beneficiary.pop('country', None)
    if Business.objects.filter(name=beneficiary_name).exists():
        lc.beneficiary = Business.objects.get(name=beneficiary_name)
    else:
        lc.beneficiary = Business(name=beneficiary_name, address=beneficiary_address,
                                  country=beneficiary_country)
        lc.beneficiary.save()
        ApprovedCredit(bank=lc.issuer, business=lc.beneficiary).save()
        send_mail(
                employee_applying.employer.name + " has created their LC to work with you on Bountium",
                employee_applying.employer.name + ": Forward these instructions to a contact at your "
                                                  "beneficiary, so that they can upload documentary "
                                                  "requirements and request payment on Bountium. "
                                                  "\nInstructions for beneficiary: 1. Set your business up "
                                                  "at https://bountium.org/business/register/" +
                str(lc.beneficiary.id) + "/" + str(
                        lc.id) + ". 2. Navigate to your home page to see the newly created LC.",
                "steve@bountium.org",
                [employee_applying.email],
                fail_silently=False,
        )

    # set the sanctions message
    lc.sanction_auto_message = sanction_approval(beneficiary_country, lc.client.country)
    ofac(beneficiary_name, lc)

    # Question 5-8
    lc.credit_delivery_means = json_data.pop('credit_delivery_means', None)
    lc.credit_amt_verbal = json_data.pop('credit_amt_verbal', None)
    credit_amt = json_data.pop('credit_amt', None)
    lc.credit_amt = credit_amt if credit_amt is None else decimal.Decimal(credit_amt)
    lc.currency_denomination = json_data.pop('currency_denomination', None)

    # Question 9
    account_party_name = json_data.pop('account_party_name', None)
    json_data.pop('account_party_address', None)
    if json_data.pop('account_party', None):
        # Question 10-12
        lc.applicant_and_ap_j_and_s_obligated = json_data.pop('applicant_and_ap_j_and_s_obligated', None)
        if Business.objects.filter(name=account_party_name).exists():
            lc.account_party = Business.objects.get(name=account_party_name)
        else:
            send_mail(
                    lc.client.name + " has created their LC to work with you on Bountium",
                    lc.client.name + ": Forward these instructions to a contact at your account party, so that they "
                                     "can "
                                     "view the LC on Bountium. \nInstructions for account party: 1. Set your business "
                                     "up at https://app.bountium.org/business/register, 2. Claim your acccount party "
                                     "status at https://app.bountium.org/business/claimAccountParty/" + str(
                            lc.id) + "/",
                    "steve@bountium.org",
                    [list(lc.tasked_client_employees.all())[0].email],
                    fail_silently=False,
            )

    # Question 13
    advising_bank = json_data.pop('advising_bank', None)
    if advising_bank is not None and advising_bank.get('name', None) is not None and len(advising_bank['name']) > 0:
        if Bank.objects.filter(name=advising_bank['name']).exists():
            lc.advising_bank = Bank.objects.get(name=advising_bank['name'])
        else:
            lc.advising_bank = Bank(name=advising_bank['name'], mailing_address=advising_bank['address'],
                                    country=advising_bank['country'], email_contact=advising_bank['email'])
            lc.advising_bank.save()
            send_mail(
                    lc.issuer.name + " has created an LC to work with you on Bountium",
                    f"Instructions for advising bank: 1. Set your bank "
                    f"up at https://app.bountium.org/bank/register/{lc.advising_bank.id}/{lc.id}.\n2. Navigate to"
                    f" your home page to view the newly created LC.",
                    "steve@bountium.org",
                    [advising_bank['email']],
                    fail_silently=False,
            )

    # Question 14
    lc.forex_contract_num = json_data.pop('forex_contract_num', None)

    # Question 15-20
    exchange_rate_tolerance = json_data.pop('exchange_rate_tolerance', None)
    lc.exchange_rate_tolerance = exchange_rate_tolerance if exchange_rate_tolerance is None else decimal.Decimal(
            exchange_rate_tolerance)
    lc.purchased_item = json_data.pop('purchased_item', None)
    lc.unit_of_measure = json_data.pop('unit_of_measure', None)
    units_purchased = json_data.pop('units_purchased', None)
    lc.units_purchased = units_purchased if units_purchased is None else decimal.Decimal(units_purchased)
    unit_error_tolerance = json_data.pop('unit_error_tolerance', None)
    lc.unit_error_tolerance = unit_error_tolerance if unit_error_tolerance is None else decimal.Decimal(
            unit_error_tolerance)
    lc.confirmation_means = json_data.pop('confirmation_means', None)
    lc.hts_code = json_data.pop('hts_code', None)
    import_license(lc)
    believable_price_of_goods(lc.hts_code, lc.unit_of_measure)

    # Question 21
    paying_other_banks_fees = json_data.pop('paying_other_banks_fees', None)
    if paying_other_banks_fees == "The beneficiary":
        lc.paying_other_banks_fees = lc.beneficiary
    else:
        lc.paying_other_banks_fees = lc.client

    # Question 22
    credit_expiry_location = json_data.pop('credit_expiry_location', None)
    if credit_expiry_location == "Issuing bank\'s office":
        lc.credit_expiry_location = lc.issuer
    else:
        # TODO this assumes that the advising bank and confirming bank are one and the same.
        # See Justins email around March 20 or so... isnt always the case.
        lc.credit_expiry_location = lc.advising_bank

    # Question 23-24
    # TODO what format does a model.DateField have to be in?
    lc.expiration_date = json_data.pop('expiration_date', None)
    if 'draft_presentation_date' in json_data:
        lc.draft_presentation_date = json_data.pop('draft_presentation_date', None)
    else:
        # TODO we're not asking for shipment date...
        # theotically, this should be shipment_date + 21 days
        # using expiration_date for now
        lc.draft_presentation_date = lc.expiration_date

    # Question 25
    drafts_invoice_value = json_data.pop('drafts_invoice_value', None)
    lc.drafts_invoice_value = drafts_invoice_value if drafts_invoice_value is None else decimal.Decimal(
            drafts_invoice_value)

    # Question 26
    lc.credit_availability = json_data.pop('credit_availability', None)

    # Question 27
    paying_acceptance_and_discount_charges = json_data.pop('paying_acceptance_and_discount_charges', None)
    if paying_acceptance_and_discount_charges == "The beneficiary":
        lc.paying_acceptance_and_discount_charges = lc.beneficiary
    else:
        lc.paying_acceptance_and_discount_charges = lc.client

    # Question 28
    lc.deferred_payment_date = json_data.pop('deferred_payment_date', None)

    # Question 29
    for delegated_negotiating_bank in json_data.pop('delegated_negotiating_banks', None):
        # TODO look up each named bank;
        # if they're there, lc.delegated_negotiating_banks.add
        # otherwise, invite them and let them 'claim' it in the same fashion as other invitees to an LC
        pass

    # Question 30
    lc.partial_shipment_allowed = json_data.pop('partial_shipment_allowed', None)

    # Question 31
    lc.transshipment_allowed = json_data.pop('transshipment_allowed', None)

    # Question 32
    lc.merch_charge_location = json_data.pop('merch_charge_location', None)

    # Question 33
    lc.late_charge_date = json_data.pop('late_charge_date', None)

    # Question 34
    lc.charge_transportation_location = json_data.pop('charge_transportation_location', None)

    # Question 35
    lc.incoterms_to_show = json.dumps(json_data.pop('incoterms_to_show', []))

    # Question 36
    lc.named_place_of_destination = json_data.pop('named_place_of_destination', None)

    # TODO typed: when creating doc reqs, actually use all the fields in json_data, updating specifically typed doc
    #  reqs if some of them are missing. don't have to use in is_satisfied if you're scared of conflicting with ucp600

    # Question 37
    commercial_invoice = json_data.pop('commercial_invoice', None)
    if commercial_invoice['original'] or commercial_invoice['copies'] > 0:
        if commercial_invoice['original'] and commercial_invoice['copies'] > 0:
            version = "Original and Copies"
        elif commercial_invoice['original']:
            version = "Original"
        else:
            version = "Copies"
        required_values = (
                "Version required: " + version
                + "\nIncoterms to show: " + lc.incoterms_to_show
                + "\nNamed place of destination: " + lc.named_place_of_destination
        )
        required_values += "\nCopies: " + str(commercial_invoice['copies'])
        # TODO typed: test
        ci = CommercialInvoiceRequirement(
                for_lc=lc,
                doc_name="Commercial Invoice",
                required_values=required_values,
                due_date=lc.draft_presentation_date,
                type="commercial_invoice"
        )
        ci.save()

    # Question 38
    if 'required_transport_docs' in json_data:
        required_transport_docs = json_data.pop('required_transport_docs')
        required_values = ""
        # Question 39
        for transport_doc in required_transport_docs:
            required_values += "Marked " + transport_doc['required_values'] + "\n"
        required_values = required_values[:-1]
        # TODO typed:  convert this to if xxx in json_data for the 3 transport doc types
        # we support
        for required_transport_doc in required_transport_docs:
            lc.documentaryrequirement_set.create(
                    doc_name=required_transport_doc['name'],
                    due_date=lc.draft_presentation_date,
                    required_values=required_values
            )

    # TODO typed: implement the below classes

    # Question 40
    if 'packing_list' in json_data:
        packing_list = json_data.pop('packing_list')
        if packing_list['copies'] != 0:
            lc.documentaryrequirement_set.create(
                    doc_name="Packing List",
                    due_date=lc.draft_presentation_date
            )

    # Question 41
    if 'certificate_of_origin' in json_data:
        certificate_of_origin = json_data.pop('certificate_of_origin')
        if certificate_of_origin['copies'] != 0:
            lc.documentaryrequirement_set.create(
                    doc_name="Certificate of Origin",
                    due_date=lc.draft_presentation_date
            )

    # Question 42
    # TODO typed: use inspeciton certificate model
    if 'inspection_certificate' in json_data:
        inspection_certificate = json_data.pop('inspection_certificate')
        if inspection_certificate['copies'] != 0:
            lc.documentaryrequirement_set.create(
                    doc_name="Inspection Certificate",
                    due_date=lc.draft_presentation_date
            )

    # Question 43
    other_insurance_risks_covered = json_data.pop('other_insurance_risks_covered', None)
    if 'insurance_percentage' in json_data:
        insurance_percentage = json_data.pop('insurance_percentage')
        selected_insurance_risks_covered = json_data.pop('selected_insurance_risks_covered', None)
        if insurance_percentage != 0:
            # Queston 44 and 45
            risks_covered = selected_insurance_risks_covered
            if other_insurance_risks_covered is not None:
                risks_covered.append(other_insurance_risks_covered)
            required_values = "Insurance percentage: " + str(insurance_percentage)
            for risk_covered in risks_covered:
                required_values += "\nCovers " + risk_covered
            # TODO typed: use inspeciton certificate model
            lc.documentaryrequirement_set.create(
                    doc_name="Negotiable Insurance Policy or Certificate",
                    due_date=lc.draft_presentation_date,
                    required_values=required_values
            )

    # Question 46
    for doc_req in json_data.pop('other_draft_accompiants', []):
        lc.documentaryrequirement_set.create(
                doc_name=doc_req['name'],
                due_date=doc_req['due_date'],
                required_values=doc_req['required_values']
        )

    # Question 47
    # TODO this might be parsed into a OneToMany, LC->Business
    lc.doc_reception_notifees = json_data.pop('doc_reception_notifees', None)

    # Question 48
    lc.arranging_own_insurance = json_data.pop('arranging_own_insurance', None)

    # Question 49
    if 'other_instructions' in json_data:
        lc.other_instructions = json_data.pop('other_instructions')
        if pycountry.countries.lookup(lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
                lc.client.country).alpha_2 == 'US':
            boycott_phrases = boycott_language(lc.other_instructions)
            for phrase in boycott_phrases:
                BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()

    # Question 50
    lc.merch_description = json_data.pop('merch_description', None)

    # Question 51
    transferability = json_data.pop('transferability', None)
    if transferability == "Transferable, fees charged to the applicant\'s account":
        lc.transferable_to_applicant = True
    elif transferability == "Transferable, fees charged to the beneficiary\'s account":
        lc.transferable_to_beneficiary = True

    # Cash Secure Question
    cash_secure = json_data.pop("cash_secure", None)
    lc.cash_secure = cash_secure if cash_secure is None else decimal.Decimal(cash_secure)

    # 2. for any other fields left in json_data, save them as a tuple
    #    in other_data
    lc.other_data = json.dumps(json_data)

    # 3. save and return back!
    lc.save()


# get the LC's of which a bank is the advisor for
def get_advising(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404(f"No bank with id {bank_id} found")
    if request.method != "GET":
        return HttpResponseBadRequest("This endpoint only supports GET, POST, PUT, DELETE")
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Must be logged in to see your bank's issued LCs")
    if not bank.bankemployee_set.filter(email=request.user.username).exists():
        return HttpResponseForbidden("Must be an employee of the bank to see all the LCs this bank has issued")
    to_return = []
    for lc in DigitalLC.objects.filter(advising_bank_id=bank_id):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)
