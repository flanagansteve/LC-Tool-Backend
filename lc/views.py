import json
import re
import time
from decimal import *

import pycountry
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, \
    Http404, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt

from business.models import ApprovedCredit
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
        raise Http404("No bank with that id found")
    if request.method == "GET":
        if request.user.is_authenticated:
            if bank.bankemployee_set.filter(email=request.user.username).exists():
                to_return = []
                for lc in DigitalLC.objects.filter(issuer=bank):
                    to_return.append(lc.to_dict())
                return JsonResponse(to_return, safe=False)
            else:
                return HttpResponseForbidden("Must be an employee of the bank to see all the LCs this bank has issued")
        else:
            return HttpResponseForbidden("Must be logged in to see your bank's issued LCs")
    elif request.method == "POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if bank.bankemployee_set.filter(email=request.user.username).exists():
                # 1. create the initial LC instance with parties, creating new
                #    accounts/inviting registrants where applicable
                lc = DigitalLC(issuer=bank)
                lc.save()
                lc.tasked_issuer_employees.add(bank.bankemployee_set.get(email=request.user.username))
                if Business.objects.filter(name=json_data['applicant_name']).exists():
                    if lc.client.businessemployee_set.filter(email=json_data['applicant_employee_contact']).exists():
                        lc.tasked_client_employees.add(
                              Business.businessemployee_set.get(email=json_data['applicant_employee_contact']))
                    else:
                        # TODO decide - either
                        # send an email 'set your employee account up at <insert employee registration link>'
                        # or return an error, since the business exists, so it
                        # was probably a mistyped email
                        pass
                    # TODO mail the business inviting them to fill the app out
                    send_mail(
                          bank.bankemployee_set.get(
                                email=request.user.username).name + " has started your LC for you on Bountium!",
                          "Fill out your app at https://app.bountium.org/business/finishApp/" + lc.id,
                          "steve@bountium.org",
                          [json_data['applicant_employee_contact']],
                          fail_silently=False,
                    )
                else:
                    # TODO create the business, and invite applicant_employee_contact to register then fill out the
                    #  LC app
                    send_mail(
                          bank.bankemployee_set.get(
                                email=request.user.username).name + " has started your LC for you on Bountium!",
                          "1. Set your business up at https://app.bountium.org/business/register, 2. fill out your "
                          "app at https://bountium.org/business/finishApp/" + lc.id,
                          "steve@bountium.org",
                          [json_data['applicant_employee_contact']],
                          fail_silently=False,
                    )
                    pass
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

                # Questions 1 and 2
                applicant_name = json_data['applicant_name']
                applicant_address = json_data['applicant_address']
                if (applicant_name != employee_applying.employer.name
                      or applicant_address != employee_applying.employer.address):
                    return HttpResponseForbidden(
                          "You may only apply for an LC on behalf of your own business. Check the submitted "
                          "applicant_name and applicant_address for correctness - one or both differed from the "
                          "business name and address associated with this user\'s employer")
                lc = DigitalLC(issuer=bank, client=employee_applying.employer, application_date=datetime.datetime.now())
                lc.save()
                lc.tasked_client_employees.add(employee_applying)
                del json_data['applicant_name']
                del json_data['applicant_address']

                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                beneficiary_country = json_data['beneficiary_country']
                if Business.objects.filter(name=beneficiary_name).exists():
                    lc.beneficiary = Business.objects.get(name=beneficiary_name)
                else:
                    lc.beneficiary = Business(name=beneficiary_name, address=beneficiary_address,
                                              country=beneficiary_country)
                    lc.beneficiary.save()
                    ApprovedCredit(bank=bank, business=lc.beneficiary).save()
                    send_mail(
                          employee_applying.employer.name + " has created their LC to work with you on Bountium",
                          employee_applying.employer.name + ": Forward these instructions to a contact at your "
                                                            "beneficiary, so that they can upload documentary "
                                                            "requirements and request payment on Bountium. "
                                                            "\nInstructions for beneficiary: 1. Set your business up "
                                                            "at https://bountium.org/business/register/" +
                          lc.beneficiary.id + ". 2. Navigate to you home page to see the newly created LC.",
                          "steve@bountium.org",
                          [employee_applying.email],
                          fail_silently=False,
                    )
                del json_data['beneficiary_name']
                del json_data['beneficiary_address']
                del json_data['beneficiary_country']

                # set the sanctions message
                lc.sanction_auto_message = sanction_approval(beneficiary_country, json_data['applicant_country'])
                ofac(beneficiary_name, lc)
                import_license(json_data['hts_code'], lc)

                lc.save()

                set_lc_specifications(lc, json_data)

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
            return HttpResponseForbidden("Must be logged in to create an LC")
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
        if request.user.is_authenticated:
            if (employed_by_main_party_to_lc(lc, request.user.username)):
                return JsonResponse(lc.to_dict())
            else:
                return HttpResponseForbidden(
                      'Only an employee of the issuer, the applicant, or the beneficiary to the LC may view it')
        else:
            return HttpResponseForbidden("Must be logged in to view an LC")
    elif request.method == "POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            # The client's employee is responding to an LC application their bank started for them
            if lc.client.businessemployee_set.filter(email=request.user.username).exists():
                lc.application_date = datetime.datetime.now()
                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                beneficiary_country = json_data['beneficiary_country']
                if Business.objects.filter(name=beneficiary_name).exists():
                    lc.beneficiary = Business.objects.get(name=beneficiary_name)
                else:
                    send_mail(
                          employee_applying.employer.name + " has created their LC to work with you on Bountium",
                          employee_applying.employer.name + ": Forward these instructions to a contact at your "
                                                            "beneficiary, so that they can upload documentary "
                                                            "requirements and request payment on Bountium. "
                                                            "\nInstructions for beneficiary: 1. Set your business up "
                                                            "at https://app.bountium.org/business/register, "
                                                            "2. Claim your beneficiary status at "
                                                            "https://bountium.org/business/claimBeneficiary/" + str(
                                lc.id) + "/",
                          "steve@bountium.org",
                          [request.user.username],
                          fail_silently=False,
                    )
                    pass
                del json_data['beneficiary_name']
                del json_data['beneficiary_address']
                set_lc_specifications(lc, json_data)
                return JsonResponse({
                    'success': True
                })
            else:
                return HttpResponseForbidden("Only employees of the business applying for this LC can create the LC")
        else:
            return HttpResponseForbidden("Must be logged in to create an LC")
    elif request.method == "PUT":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer_approved and lc.beneficiary_approved and lc.client_approved:
                return JsonResponse({
                    'success': False,
                    'reason': 'This LC has been approved by all parties, and may not be modified'
                })
            else:
                if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    update_django_instance_with_subset_json(json_data['lc'], lc)
                    if 'hold_status' not in json_data or not json_data['hold_status']:
                        lc.client_approved, lc.beneficiary_approved = False, False
                        lc.issuer_approved = True
                        if 'other_instructions' in json_data and pycountry.countries.lookup(
                              lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
                              lc.client.country).alpha_2 == 'US':
                            BoycottLanguage.objects.filter(lc=lc).delete()
                        boycott_phrases = boycott_language(lc.other_instructions)
                        for phrase in boycott_phrases:
                            BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()
                    if 'latest_version_notes' in json_data:
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the issuer said: ' + \
                                                  json_data['latest_version_notes']
                    if 'comment' in json_data:
                        comment = json_data['comment']
                        if 'action' not in comment or 'message' not in comment:
                            return HttpResponseBadRequest(
                                  "The given comment must have an 'action' field and a 'message' field")
                        created = Comment(lc=lc, author_type="issuer", action=comment['action'],
                                          date=datetime.datetime.now(), message=comment['message'],
                                          issuer_viewable=True, client_viewable=True, respondable='client')
                        created.save()
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'updated_lc': lc.to_dict()
                    })
                elif lc.beneficiary is not None and lc.beneficiary.businessemployee_set.filter(
                      email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    update_django_instance_with_subset_json(json_data['lc'], lc)
                    lc.issuer_approved, lc.client_approved = False, False
                    lc.beneficiary_approved = True
                    if 'other_instructions' in json_data and pycountry.countries.lookup(
                          lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
                          lc.client.country).alpha_2 == 'US':
                        BoycottLanguage.objects.filter(lc=lc).delete()
                    boycott_phrases = boycott_language(lc.other_instructions)
                    for phrase in boycott_phrases:
                        BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()
                    if 'latest_version_notes' in json_data:
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the beneficiary updated: ' \
                                                  + \
                                                  json_data['latest_version_notes']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'updated_lc': lc.to_dict()
                    })
                elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    update_django_instance_with_subset_json(json_data['lc'], lc)
                    lc.issuer_approved, lc.beneficiary_approved = False, False
                    lc.client_approved = True
                    if 'other_instructions' in json_data and pycountry.countries.lookup(
                          lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
                          lc.client.country).alpha_2 == 'US':
                        BoycottLanguage.objects.filter(lc=lc).delete()
                    boycott_phrases = boycott_language(lc.other_instructions)
                    for phrase in boycott_phrases:
                        BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()
                    if 'latest_version_notes' in json_data:
                        lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the client said: ' + \
                                                  json_data['latest_version_notes']
                    if 'comment' in json_data:
                        comment = json_data['comment']
                        if 'action' not in comment or 'message' not in comment:
                            return HttpResponseBadRequest(
                                  "The given comment must have an 'action' field and a 'message' field")
                        created = Comment(lc=lc, author_type="client", action=comment['action'],
                                          date=datetime.datetime.now(), message=comment['message'],
                                          issuer_viewable=True, client_viewable=True, respondable='issuer')
                        created.save()
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'updated_lc': lc.to_dict()
                    })
                else:
                    return HttpResponseForbidden(
                          'Only an employee of the issuer, the applicant, or the beneficiary to the LC may modify it')
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(
                  email=request.user.username).exists() or lc.client.businessemployee_set.filter(
                  email=request.user.username).exists():
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
                return HttpResponseForbidden(
                      'Only an employee of either the issuer or applicant to the LC may delete it')
        else:
            return HttpResponseForbidden('Must be logged in to delete an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST, PUT, DELETE")


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
def get_lcs_by_client(request, business_id):
    try:
        client = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        raise Http404("No business with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(client=client):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)


@csrf_exempt
def get_lcs_by_beneficiary(request, business_id):
    try:
        beneficiary = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        raise Http404("No business with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(beneficiary=beneficiary):
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
        if request.user.is_authenticated:
            if relation == 'beneficiary':
                if BusinessEmployee.objects.filter(email=request.user.username).exists():
                    beneficiary_employee = BusinessEmployee.objects.get(email=request.user.username)
                    lc.beneficiary = beneficiary_employee.employer
                    lc.tasked_beneficiary_employees.add(beneficiary_employee)
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'claimed_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only a business registered on Bountium may claim beneficiary status')
            elif relation == 'account_party':
                if BusinessEmployee.objects.filter(email=request.user.username).exists():
                    account_party_employee = BusinessEmployee.objects.get(email=request.user.username)
                    lc.account_party = account_party_employee.employer
                    lc.tasked_account_party_employees.add(account_party_employee)
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'claimed_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden(
                          'Only a business registered on Bountium may claim account party status')
            elif relation == 'advising':
                if BankEmployee.objects.filter(email=request.user.username).exists():
                    advising_bank_employee = BankEmployee.objects.get(email=request.user.username)
                    lc.advising_bank = advising_bank_employee.bank
                    lc.tasked_advising_bank_employees.add(advising_bank_employee)
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success': True,
                        'claimed_on': str(datetime.datetime.now())
                    })
                else:
                    return HttpResponseForbidden('Only a bank registered on Bountium may claim advising bank status')
            else:
                raise Http404(
                      'Bountium is only supporting the LC relations "beneficiary", "account_party", and "advising"')
        else:
            return HttpResponseForbidden('You must be logged in to claim an LC relation')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")


@csrf_exempt
def cr_doc_reqs(request, lc_id):
    try:
        lc = DigitalLC.objects.get(id=lc_id)
    except DigitalLC.DoesNotExist:
        raise Http404("No lc with id " + lc_id)
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (employed_by_main_party_to_lc(lc, request.user.username)):
                this_lcs_doc_reqs = LC.objects.get(id=lc_id).documentaryrequirement_set
                return JsonResponse(list(this_lcs_doc_reqs.values()), safe=False)
            else:
                return HttpResponseForbidden(
                      'Only an employee of the issuer, the client, or the beneficiary to the LC may view its '
                      'documentary requirements')
        else:
            return HttpResponseForbidden("Must be logged in to view an LC")
    elif request.method == 'POST':
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                json_data = json.loads(request.body)
                lc.documentaryrequirement_set.create(doc_name=json_data['doc_name'],
                                                     link_to_submitted_doc=json['link_to_submitted_doc'])
                lc.save()
                return JsonResponse({
                    'doc_req_id': lc.documentaryrequirement_set.get(doc_name=json_data['doc_name']).id
                })
            else:
                return HttpResponseForbidden(
                      "Only an employee of the beneficiary to this LC may create documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to create documentary requirements")
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
            if (employed_by_main_party_to_lc(lc, request.user.username)):
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
            or lc.beneficiary.businessemployee_set.filter(email=username).exists())


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
            else:
                return HttpResponseForbidden(
                      "Only an employee of the bank which issued this LC, or an employee to the beneficiary of this "
                      "LC, may evaluate documentary requirements")
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
                      'Bountium only supports marking an LC\'s status with the actions "request", "draw", "evaluate", '
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
def import_license(hts_code, lc):
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
def set_lc_specifications(lc, json_data):
    # Question 5-8
    lc.credit_delivery_means = json_data['credit_delivery_means']
    lc.credit_amt_verbal = json_data['credit_amt_verbal']
    lc.credit_amt = json_data['credit_amt']
    lc.currency_denomination = json_data['currency_denomination']
    del json_data['credit_delivery_means'], json_data['credit_amt_verbal'], json_data['credit_amt'], json_data[
        'currency_denomination']

    # Question 9
    if json_data['account_party']:
        # Question 10-12
        lc.applicant_and_ap_j_and_s_obligated = json_data['applicant_and_ap_j_and_s_obligated']
        account_party_name = json_data['account_party_name']
        account_party_address = json_data['account_party_address']
        if Business.objects.filter(name=account_party_name).exists():
            lc.account_party = Business.objects.get(name=account_party_name)
        else:
            send_mail(
                  lc.client.name + " has created their LC to work with you on Bountium",
                  lc.client.name + ": Forward these instructions to a contact at your account party, so that they can "
                                   "view the LC on Bountium. \nInstructions for account party: 1. Set your business "
                                   "up at https://app.bountium.org/business/register, 2. Claim your acccount party "
                                   "status at https://app.bountium.org/business/claimAccountParty/" + str(
                        lc.id) + "/",
                  "steve@bountium.org",
                  [list(lc.tasked_client_employees.all())[0].email],
                  fail_silently=False,
            )
            pass
    del json_data['account_party']
    json_data.pop('applicant_and_ap_j_and_s_obligated', None)
    json_data.pop('account_party_name', None)
    json_data.pop('account_party_address', None)

    # Question 13
    if 'advising_bank' in json_data:
        bank_name = json_data['advising_bank']
        if Bank.objects.filter(name=bank_name).exists():
            lc.advising_bank = Bank.objects.get(name=bank_name)
        else:
            # TODO this breaks for lcs where issuer empl has not yet been assigned
            """send_mail(
                lc.issuer.name + " has created an LC to work with you on Bountium",
                lc.issuer.name + ": Forward these instructions to a contact at the advising bank, so that they can 
                view the LC on Bountium. \nInstructions for advising bank: 1. Set your bank up at 
                https://app.bountium.org/bank/register, 2. Claim your advising bank status at 
                https://app.bountium.org/bank/claimAdvising/" + str(lc.id) + "/",
                "steve@bountium.org",
                [list(lc.tasked_issuer_employees.all())[0]],
                fail_silently=False,
            )"""
            pass
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
    del json_data['exchange_rate_tolerance'], json_data['purchased_item'], json_data['unit_of_measure'], json_data[
        'units_purchased'], json_data['unit_error_tolerance'], json_data['confirmation_means']

    # Question 21
    if json_data['paying_other_banks_fees'] == "The beneficiary":
        lc.paying_other_banks_fees = lc.beneficiary
    else:
        lc.paying_other_banks_fees = lc.client
    del json_data['paying_other_banks_fees']

    # Question 22
    if json_data['credit_expiry_location'] == "Issuing bank\'s office":
        lc.credit_expiry_location = lc.issuer
    else:
        # TODO this assumes that the advising bank and confirming bank are one and the same.
        # See Justins email around March 20 or so... isnt always the case.
        lc.credit_expiry_location = lc.advising_bank
    del json_data['credit_expiry_location']

    # Question 23-24
    # TODO what format does a model.DateField have to be in?
    lc.expiration_date = json_data['expiration_date']
    del json_data['expiration_date']
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

    # Question 27
    if json_data['paying_acceptance_and_discount_charges'] == "The beneficiary":
        lc.paying_acceptance_and_discount_charges = lc.beneficiary
    else:
        lc.paying_acceptance_and_discount_charges = lc.client
    del json_data['paying_acceptance_and_discount_charges']

    # Question 28
    lc.deferred_payment_date = json_data['deferred_payment_date']
    del json_data['deferred_payment_date']

    # Question 29
    for delegated_negotiating_bank in json_data['delegated_negotiating_banks']:
        # TODO look up each named bank;
        # if they're there, lc.delegated_negotiating_banks.add
        # otherwise, invite them and let them 'claim' it in the same fashion as other invitees to an LC
        pass
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
    lc.incoterms_to_show = json.dumps(json_data['incoterms_to_show'])
    del json_data['incoterms_to_show']

    # Question 36
    lc.named_place_of_destination = json_data['named_place_of_destination']
    del json_data['named_place_of_destination']

    # TODO typed: when creating doc reqs, actually use all the fields in json_data, updating specifically typed doc
    #  reqs if some of them are missing. don't have to use in is_satisfied if you're scared of conflicting with ucp600

    # Question 37
    if json_data['commercial_invoice']['original'] or json_data['commercial_invoice']['copies'] > 0:
        version = ""
        if json_data['commercial_invoice']['original'] and json_data['commercial_invoice']['copies'] > 0:
            version = "Original and Copies"
        elif json_data['commercial_invoice']['original']:
            version = "Original"
        else:
            version = "Copies"
        required_values = (
              "Version required: " + version
              + "\nIncoterms to show: " + lc.incoterms_to_show
              + "\nNamed place of destination: " + lc.named_place_of_destination
        )
        required_values += "\nCopies: " + str(json_data['commercial_invoice']['copies'])
        # TODO typed: test
        ci = CommercialInvoiceRequirement(
              for_lc=lc,
              doc_name="Commercial Invoice",
              required_values=required_values,
              due_date=lc.draft_presentation_date,
              type="commercial_invoice"
        )
        ci.save()
    del json_data['commercial_invoice']

    # Question 38
    if 'required_transport_docs' in json_data:
        required_values = ""
        # Question 39
        for transport_doc in json_data['required_transport_docs']:
            required_values += "Marked " + transport_doc['required_values'] + "\n"
        required_values = required_values[:-1]
        # TODO typed:  convert this to if xxx in json_data for the 3 transport doc types
        # we support
        for required_transport_doc in json_data['required_transport_docs']:
            lc.documentaryrequirement_set.create(
                  doc_name=required_transport_doc['name'],
                  due_date=lc.draft_presentation_date,
                  required_values=required_values
            )
        del json_data['required_transport_docs']

    # TODO typed: implement the below classes

    # Question 40
    if 'packing_list' in json_data:
        if json_data['packing_list']['copies'] != 0:
            lc.documentaryrequirement_set.create(
                  doc_name="Packing List",
                  due_date=lc.draft_presentation_date
            )
        del json_data['packing_list']

    # Question 41
    if 'certificate_of_origin' in json_data:
        if json_data['certificate_of_origin']['copies'] != 0:
            lc.documentaryrequirement_set.create(
                  doc_name="Certificate of Origin",
                  due_date=lc.draft_presentation_date
            )
        del json_data['certificate_of_origin']

    # Question 42
    # TODO typed: use inspeciton certificate model
    if 'inspection_certificate' in json_data:
        if json_data['inspection_certificate']['copies'] != 0:
            lc.documentaryrequirement_set.create(
                  doc_name="Inspection Certificate",
                  due_date=lc.draft_presentation_date
            )
        del json_data['inspection_certificate']

    # Question 43
    if 'insurance_percentage' in json_data:
        if json_data['insurance_percentage'] != 0:
            # Queston 44 and 45
            risks_covered = json_data['selected_insurance_risks_covered']
            if 'other_insurance_risks_covered' in json_data:
                risks_covered.append(json_data['other_insurance_risks_covered'])
            required_values = "Insurance percentage: " + str(json_data['insurance_percentage'])
            for risk_covered in risks_covered:
                required_values += "\nCovers " + risk_covered
            # TODO typed: use inspeciton certificate model
            lc.documentaryrequirement_set.create(
                  doc_name="Negotiable Insurance Policy or Certificate",
                  due_date=lc.draft_presentation_date,
                  required_values=required_values
            )
            del json_data['other_insurance_risks_covered']
            del json_data['selected_insurance_risks_covered']
        del json_data['insurance_percentage']

    # Question 46
    if 'other_draft_accompiants' in json_data:
        for doc_req in json_data['other_draft_accompiants']:
            lc.documentaryrequirement_set.create(
                  doc_name=doc_req['name'],
                  due_date=doc_req['due_date'],
                  required_values=doc_req['required_values']
            )
        del json_data['other_draft_accompiants']

    # Question 47
    # TODO this might be parsed into a OneToMany, LC->Business
    if 'doc_reception_notifees' in json_data:
        lc.doc_reception_notifees = json_data['doc_reception_notifees']
        del json_data['doc_reception_notifees']

    # Question 48
    lc.arranging_own_insurance = json_data['arranging_own_insurance']
    del json_data['arranging_own_insurance']

    # Question 49
    if 'other_instructions' in json_data:
        lc.other_instructions = json_data['other_instructions']
        if pycountry.countries.lookup(lc.beneficiary.country).alpha_2 == 'US' or pycountry.countries.lookup(
              lc.client.country).alpha_2 == 'US':
            boycott_phrases = boycott_language(json_data['other_instructions'])
        for phrase in boycott_phrases:
            BoycottLanguage(phrase=phrase, source='other_instructions', lc=lc).save()
        del json_data['other_instructions']

    # Question 50
    lc.merch_description = json_data['merch_description']
    del json_data['merch_description']

    # Question 51
    if json_data["transferability"] == "Transferable, fees charged to the applicant\'s account":
        lc.transferable_to_applicant = True
    elif json_data["transferability"] == "Transferable, fees charged to the beneficiary\'s account":
        lc.transferable_to_beneficiary = True
    del json_data['transferability']

    # Cash Secure Question
    lc.cash_secure = json_data["cash_secure"]
    del json_data["cash_secure"]

    # 2. for any other fields left in json_data, save them as a tuple
    #    in other_data
    lc.other_data = json_data

    # 3. save and return back!
    lc.save()
