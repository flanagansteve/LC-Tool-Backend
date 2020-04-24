from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, FileResponse
from django.http import HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.core import serializers
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import *
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
import json, datetime, boto3, os, time

# TODO only handling DigitalLCs for now
# TODO none of these distinguish between different employees within each party - only verifying that you are A employee of the appropriate party to perform an action
# TODO keyerrors... unhandled key errors everywhere
# TODO currently only allowing the issuer, client, and beneficiary to do stuff - ignoring the account_party and advising_bank, even though we are setting() them
# TODO for claiming beneficiary / advising_bank / account_party status, we should somehow ensure the claimant is the party they claim to be.
    # could check logged_in_user.employer.name == name submitted by applicant
    # Could let client or issuer approve
# TODO ensure the links in all send_mail(s are accurate per ryan

@csrf_exempt
def cr_lcs(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with that id found")
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
                lc = DigitalLC(issuer = bank)
                lc.save()
                lc.tasked_issuer_employees.add(bank.bankemployee_set.get(email=request.user.username))
                if Business.objects.filter(name=json_data['applicant_name']).exists():
                    if lc.client.businessemployee_set.filter(email=json_data['applicant_employee_contact']).exists():
                        lc.tasked_client_employees.add(Business.businessemployee_set.get(email=json_data['applicant_employee_contact']))
                    else:
                        # TODO decide - either
                            # send an email 'set your employee account up at <insert employee registration link>'
                        # or return an error, since the business exists, so it
                        # was probably a mistyped email
                        pass
                    # TODO mail the business inviting them to fill the app out
                    send_mail(
                        bank.bankemployee_set.get(email=request.user.username).name + " has started your LC for you on Bountium!",
                        "Fill out your app at https://app.bountium.org/business/finishApp/" + lc.id,
                        "steve@bountium.org",
                        [json_data['applicant_employee_contact']],
                        fail_silently=False,
                    )
                else:
                    # TODO create the business, and invite applicant_employee_contact to register then fill out the LC app
                    send_mail(
                        bank.bankemployee_set.get(email=request.user.username).name + " has started your LC for you on Bountium!",
                        "1. Set your business up at https://app.bountium.org/business/register, 2. fill out your app at https://bountium.org/business/finishApp/" + lc.id,
                        "steve@bountium.org",
                        [json_data['applicant_employee_contact']],
                        fail_silently=False,
                    )
                    pass
                # 3. return success & the created lc
                return JsonResponse({
                    'success':True,
                    'created_lc':lc.to_dict()
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
                    return HttpResponseForbidden("You may only apply for an LC on behalf of your own business. Check the submitted applicant_name and applicant_address for correctness - one or both differed from the business name and address associated with this user\'s employer")
                lc = DigitalLC(issuer = bank, client = employee_applying.employer, application_date = datetime.datetime.now())
                lc.save()
                lc.tasked_client_employees.add(employee_applying)
                del json_data['applicant_name']
                del json_data['applicant_address']

                # Questions 3 and 4
                beneficiary_name = json_data['beneficiary_name']
                beneficiary_address = json_data['beneficiary_address']
                if Business.objects.filter(name=beneficiary_name).exists():
                    lc.beneficiary = Business.objects.get(name=beneficiary_name)
                else:
                    send_mail(
                        employee_applying.employer.name + " has created their LC to work with you on Bountium",
                        employee_applying.employer.name + ": Forward these instructions to a contact at your beneficiary, so that they can upload documentary requirements and request payment on Bountium. \nInstructions for beneficiary: 1. Set your business up at https://bountium.org/business/register, 2. Claim your beneficiary status at https://bountium.org/business/claimBeneficiary/" + str(lc.id) + "/",
                        "steve@bountium.org",
                        [employee_applying.email],
                        fail_silently=False,
                    )
                    pass
                del json_data['beneficiary_name']
                del json_data['beneficiary_address']

                set_lc_specifications(lc, json_data)

                # 3. notify a bank employee maybe? TODO decide

                # 4. save and return back!
                return JsonResponse({
                    'success' : True,
                    'created_lc' : lc.to_dict()
                })

            else:
                return HttpResponseForbidden("You may only create LCs with the bank of the ID at this endpoint by being a member of this bank, or by being a business requesting an LC from this bank")
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
        return Http404("No lc with that id")
    if request.method == "GET":
        if request.user.is_authenticated:
            if (lc.issuer.bankemployee_set.filter(email=request.user.username).exists()
                or lc.client.businessemployee_set.filter(email=request.user.username).exists()
                or lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists()):
                return JsonResponse(lc.to_dict())
            else:
                return HttpResponseForbidden('Only an employee of the issuer, the applicant, or the beneficiary to the LC may view it')
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
                if Business.objects.filter(name=beneficiary_name).exists():
                    lc.beneficiary = Business.objects.get(name=beneficiary_name)
                else:
                    send_mail(
                        employee_applying.employer.name + " has created their LC to work with you on Bountium",
                        employee_applying.employer.name + ": Forward these instructions to a contact at your beneficiary, so that they can upload documentary requirements and request payment on Bountium. \nInstructions for beneficiary: 1. Set your business up at https://app.bountium.org/business/register, 2. Claim your beneficiary status at https://bountium.org/business/claimBeneficiary/" + str(lc.id) + "/",
                        "steve@bountium.org",
                        [request.user.username],
                        fail_silently=False,
                    )
                    pass
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
            json_data = json.loads(request.body)
            if lc.issuer_approved and lc.beneficiary_approved and lc.client_approved:
                return JsonResponse({
                    'success':False,
                    'reason':'This LC has been approved by all parties, and may not be modified'
                })
            else:
                if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    for key in json_data['lc']:
                        if key in dir(lc):
                            setattr(lc, key, json_data['lc'][key])
                        else:
                            # TODO log a bad field but dont flip out
                            pass
                    lc.issuer_approved = True
                    lc.client_approved = False
                    lc.beneficiary_approved = False
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the issuer said: ' + json_data['latest_version_notes']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success' : True
                    })
                elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    for key in json_data['lc']:
                        if key in dir(lc):
                            setattr(lc, key, json_data['lc'][key])
                        else:
                            # TODO log a bad field but dont flip out
                            pass
                    lc.issuer_approved = False
                    lc.client_approved = False
                    lc.beneficiary_approved = True
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the beneficiary updated: ' + json_data['latest_version_notes']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success' : True
                    })
                elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                    # TODO would be good to somehow mark changes from the prev version...
                    for key in json_data['lc']:
                        if key in dir(lc):
                            setattr(lc, key, json_data['lc'][key])
                        else:
                            # TODO log a bad field but dont flip out
                            pass
                    lc.issuer_approved = False
                    lc.client_approved = True
                    lc.beneficiary_approved = False
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the client said: ' + json_data['latest_version_notes']
                    lc.save()
                    # TODO notify parties
                    return JsonResponse({
                        'success' : True
                    })
                else:
                    return HttpResponseForbidden('Only an employee of the issuer, the applicant, or the beneficiary to the LC may modify it')
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists() or lc.client.businessemployee_set.filter(email=request.user.username).exists():
                if lc.issuer_approved and lc.beneficiary_approved and lc.client_approved:
                    return JsonResponse({
                        'success':False,
                        'reason':'This LC has been approved by all parties, and may not be revoked'
                    })
                else:
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

# TODO the following 6 functions, get_X_lcs, should be abstracted & parameterised
@csrf_exempt
def get_live_lcs(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(
            issuer=bank,
            client_approved=True, issuer_approved=True, beneficiary_approved=True,
            paid_out=False
        ):
        to_return.append(lc.to_dict())
    print(to_return)
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_awaiting_issuer(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(
            issuer=bank,
            issuer_approved=False
        ):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_awaiting_beneficiary(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(
            issuer=bank,
            beneficiary_approved=False,
            paid_out=False
        ):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_awaiting_client(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(
            issuer=bank,
            client_approved=False,
            paid_out=False
        ):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_by_client(request, business_id):
    try:
        client = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Http404("No business with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(client=client):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def get_lcs_by_beneficiary(request, business_id):
    try:
        beneficiary = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Http404("No business with that id")
    to_return = []
    for lc in DigitalLC.objects.filter(beneficiary=beneficiary):
        to_return.append(lc.to_dict())
    return JsonResponse(to_return, safe=False)

@csrf_exempt
def notify_teammate(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with that id")
    if request.method == "POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                note = lc.issuer.bankemployee_set.get(email=request.user.username).name + ' would like you to examine the LC at https://app.bountium.org/bank/lc/' + lc_id
                if 'note' in json_data:
                    note = json_data['note']
                send_mail(
                    lc.issuer.bankemployee_set.get(email=request.user.username).name + ' sent a notification on Bountium',
                    note,
                    'steve@bountium.org',
                    [json_data['to_notify']],
                    fail_silently=False,
                )
                lc.tasked_issuer_employees.add(json_data['to_notify'])
            elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                note = lc.client.businessemployee_set.get(email=request.user.username).name + ' would like you to examine the LC at https://app.bountium.org/business/lc/' + lc_id
                if 'note' in json_data:
                    note = json_data['note']
                send_mail(
                    lc.client.businessemployee_set.get(email=request.user.username).name + ' sent a notification on Bountium',
                    note,
                    'steve@bountium.org',
                    [json_data['to_notify']],
                    fail_silently=False,
                )
                lc.tasked_client_employees.add(json_data['to_notify'])
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                note = lc.beneficiary.businessemployee_set.get(email=request.user.username).name + ' would like you to examine the LC at https://app.bountium.org/business/lc/' + lc_id
                if 'note' in json_data:
                    note = json_data['note']
                send_mail(
                    lc.beneficiary.businessemployee_set.get(email=request.user.username).name + ' sent a notification on Bountium',
                    note,
                    'steve@bountium.org',
                    [json_data['to_notify']],
                    fail_silently=False,
                )
                lc.tasked_beneficiary_employees.add(json_data['to_notify'])
            else:
                return HttpResponseForbidden("Only employees of this LC's issuer, client, or beneficiary may notify teammates about it")
        else:
            return HttpResponseForbidden("Must be logged in to notify teammates about an LC")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# TODO the following 3 functions, claim_x, should be abstracted & parameterised
@csrf_exempt
def claim_beneficiary(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            if BusinessEmployee.objects.filter(email=request.user.username).exists():
                beneficiary_employee = BusinessEmployee.objects.get(email=request.user.username)
                lc.beneficiary = beneficiary_employee.employer
                lc.tasked_beneficiary_employees.add(beneficiary_employee)
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'claimed_on':str(datetime.datetime.now())
                })
            else:
                return HttpResponseForbidden('Only a business registered on Bountium may claim beneficiary status')
        else:
            return HttpResponseForbidden('You must be logged in to claim beneficiary status')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def claim_account_party(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            if BusinessEmployee.objects.filter(email=request.user.username).exists():
                account_party_employee = BusinessEmployee.objects.get(email=request.user.username)
                lc.account_party = account_party_employee.employer
                lc.tasked_account_party_employees.add(account_party_employee)
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'claimed_on':str(datetime.datetime.now())
                })
            else:
                return HttpResponseForbidden('Only a business registered on Bountium may claim account party status')
        else:
            return HttpResponseForbidden('You must be logged in to claim account party status')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def claim_advising(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            if BankEmployee.objects.filter(email=request.user.username).exists():
                advising_bank_employee = BankEmployee.objects.get(email=request.user.username)
                lc.advising_bank = advising_bank_employee.bank
                lc.tasked_advising_bank_employees.add(advising_bank_employee)
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'claimed_on':str(datetime.datetime.now())
                })
            else:
                return HttpResponseForbidden('Only a bank registered on Bountium may claim advising bank status')
        else:
            return HttpResponseForbidden('You must be logged in to claim advising bank status')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def evaluate_lc(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method == "POST":
        if request.user.is_authenticated:
            json_data = json.loads(request.body)
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                lc.issuer_approved = json_data['approve']
                if 'complaints' in json_data and json_data['complaints'] != '':
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the issuer said: ' + json_data['complaints']
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'evaluated_on':str(datetime.datetime.now())
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                lc.beneficiary_approved = json_data['approve']
                if 'complaints' in json_data and json_data['complaints'] != '':
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the beneficiary said: ' + json_data['complaints']
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'evaluated_on':str(datetime.datetime.now())
                })
            elif lc.client.businessemployee_set.filter(email=request.user.username).exists():
                lc.client_approved = json_data['approve']
                if 'complaints' in json_data and json_data['complaints'] != '':
                    lc.latest_version_notes = 'On ' + str(datetime.datetime.now()) + ' the client said: ' + json_data['complaints']
                lc.save()
                # TODO notify parties
                return JsonResponse({
                    'success':True,
                    'evaluated_on':str(datetime.datetime.now())
                })
            else:
                return HttpResponseForbidden('Only the issuer, beneficiary, or client to an LC may evaluate it')
        else:
            return HttpResponseForbidden('You must be logged in to evaluate an LC')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def cr_doc_reqs(request, lc_id):
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (lc.issuer.bankemployee_set.filter(email=request.user.username).exists()
                or lc.client.businessemployee_set.filter(email=request.user.username).exists()
                or lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists()):
                this_lcs_doc_reqs = LC.objects.get(id=lc_id).documentaryrequirement_set
                return JsonResponse(list(this_lcs_doc_reqs.values()), safe=False)
            else:
                return HttpResponseForbidden('Only an employee of the issuer, the client, or the beneficiary to the LC may view its documentary requirements')
        else:
            return HttpResponseForbidden("Must be logged in to view an LC")
    elif request.method == 'POST':
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                try:
                    lc = LC.objects.get(id=lc_id)
                except LC.DoesNotExist:
                    return Http404("No lc with id " + lc_id)
                json_data = json.loads(request.body)
                lc.documentaryrequirement_set.create(doc_name=json_data['doc_name'], link_to_submitted_doc = json['link_to_submitted_doc'])
                lc.save()
                return JsonResponse({
                    'doc_req_id' : lc.documentaryrequirement_set.get(doc_name=json_data['doc_name']).id
                })
            else:
                return HttpResponseForbidden("Only an employee of the beneficiary to this LC may create documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to create documentary requirements")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

# TODO typed: allow users to update specific fields of required doc reqs
@csrf_exempt
def rud_doc_req(request, lc_id, doc_req_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        return Http404("No doc req with id " + doc_req_id + " associated with the lc with id " + lc_id)
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (lc.issuer.bankemployee_set.filter(email=request.user.username).exists()
                or lc.client.businessemployee_set.filter(email=request.user.username).exists()
                or lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists()):
                return JsonResponse(doc_req.to_dict())
            else:
                return HttpResponseForbidden('Only an employee of the issuer, the client, or the beneficiary to the LC may view its documentary requirements')
        else:
            return HttpResponseForbidden("Must be logged in to view an LC")
    elif request.method == 'PUT':
        # TODO typed: update this to set fields that matter for typed doc reqs
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                # issuer uploading on behalf of the bene (presumably a scan or something)
                if request.content_type == 'application/pdf':
                    s3 = boto3.resource('s3')
                    submitted_doc_name = lc.issuer.name + "-submitted-on-behalf-of-bene-on" + str(datetime.datetime.now()) + ".pdf"
                    s3.Bucket('docreqs').put_object(Key=submitted_doc_name, Body=request.body)
                    doc_req.link_to_submitted_doc = "https://docreqs.s3.us-east-2.amazonaws.com/" + submitted_doc_name
                    doc_req.rejected = False
                    doc_req.save()
                    # TODO notify someone
                    return JsonResponse({
                        'success':True,
                        'submitted_and_notified_on':str(datetime.datetime.now()),
                        'doc_req':doc_req.to_dict()
                    })
                else: # presumably content-type == 'application/json'
                    json_data = json.loads(request.body)
                    if 'due_date' in json_date:
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
                        'success':True,
                        'modified_and_notified_on':str(datetime.datetime.now()),
                        'doc_req':doc_req.to_dict()
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
                        'success':True,
                        'submitted_and_notified_on':str(datetime.datetime.now()),
                        'doc_req':doc_req.to_dict()
                    })
                else: # presumably content-type == 'application/json'
                    json_data = json.loads(request.body)
                    if 'due_date' in json_date:
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
                        'success':True,
                        'modified_and_notified_on':str(datetime.datetime.now()),
                        'doc_req':doc_req.to_dict()
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
                    'doc_reqs':lc.get_doc_reqs()
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
        lc = LC.objects.get(id=lc_id)
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
                doc_req.rejected = (not json_data['approve'])
                if 'complaints' in json_data:
                    doc_req.submitted_doc_complaints = json_data['complaints']
                doc_req.save()
                lc.save()
                return JsonResponse({
                    'success':True,
                    'doc_reqs':lc.get_doc_reqs()
                })
            elif lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                doc_req.modified_and_awaiting_beneficiary_approval = json_data['approve']
                if 'complaints' in json_data:
                    doc_req.modification_complaints = json_data['complaints']
                doc_req.save()
                lc.save()
                return JsonResponse({
                    'success':True,
                    'doc_reqs':lc.get_doc_reqs()
                })
            else:
                return HttpResponseForbidden("Only an employee of the bank which issued this LC, or an employee to the beneficiary of thsi LC, may evaluate documentary requirements")
        else:
            return HttpResponseForbidden("You must be logged in to attempt a documentary requirement evaluation")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# TODO the following 3 functions, [make a boolean true]_lc, should be abstracted & parameterised
@csrf_exempt
def request_lc(request, lc_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                lc.requested = True
                lc.save()
                return JsonResponse({
                    'success':True,
                    'requested_on':str(datetime.datetime.now())
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
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists():
                lc.drawn = True
                lc.save()
                return JsonResponse({
                    'success':True,
                    'drawn_on':str(datetime.datetime.now())
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
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    if request.method=="POST":
        if request.user.is_authenticated:
            if lc.issuer.bankemployee_set.filter(email=request.user.username).exists():
                lc.paid_out = True
                lc.save()
                return JsonResponse({
                    'success':True,
                    'marked_paid_out_on':str(datetime.datetime.now())
                })
            else:
                return HttpResponseForbidden('Only the issuer of an LC may mark it paid out')
        else:
            return HttpResponseForbidden('You must be logged in to mark an LC as paid out')
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

@csrf_exempt
def get_dr_file(request, lc_id, doc_req_id):
    try:
        lc = LC.objects.get(id=lc_id)
    except LC.DoesNotExist:
        return Http404("No lc with id " + lc_id)
    try:
        doc_req = lc.documentaryrequirement_set.get(id=doc_req_id)
    except DocumentaryRequirement.DoesNotExist:
        return Http404("No doc req with that id associated with this lc")
    if request.method == 'GET':
        if request.user.is_authenticated:
            if (lc.issuer.bankemployee_set.filter(email=request.user.username).exists()
                or lc.client.businessemployee_set.filter(email=request.user.username).exists()
                or lc.beneficiary.businessemployee_set.filter(email=request.user.username).exists()):
                submitted_doc_name = lc.link_to_submitted_doc[lc.link_to_submitted_doc.index('aws.com/') + len('aws.com/'):]
                s3 = boto3.resource('s3')
                s3client = boto3.client('s3')
                file_size = s3client.head_object(Bucket='docreqs', Key=submitted_doc_name)['ContentLength']
                the_file = s3.Bucket('docreqs').download_file(Filename='/tmp/' + submitted_doc_name, Key=submitted_doc_name)
                while os.path.getsize('/tmp/' + submitted_doc_name) < file_size:
                    time.sleep(1)
                return FileResponse(open('/tmp/' + submitted_doc_name, 'rb'), content_type='application/pdf')
            else:
                return HttpResponseForbidden('Only an employee of the issuer, the client, or the beneficiary to the LC may view its documentary requirements\' submitted candidate docs')
        else:
            return HttpResponseForbidden('You must be logged in to get a documentary requirement\'s submitted file')
    else:
        return HttpResponseBadRequest("This endpoint only supports GET")

@csrf_exempt
def create_ci(request):
    ci_params = json.loads(request.body)
    test_ci = CommercialInvoiceRequirement(for_lc=LC.objects.get(id=1), invoice_issuer=ci_params["invoice_issuer"], consignee=ci_params["consignee"], currency=ci_params["currency"], goods_description=ci_params["goods_description"])
    test_ci.generate_pdf()
    return JsonResponse({
        'doc':test_ci.link_to_submitted_doc
    })


# TODO should probably log received checkbox or radio values that are not one
# of the options they're supposed to be - thats an error, but easily fixable if we know thats what happened
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
        if Business.objects.filter(name=account_party_name).exists():
            lc.account_party = Business.objects.get(name=account_party_name)
        else:
            send_mail(
                lc.client.name + " has created their LC to work with you on Bountium",
                lc.client.name + ": Forward these instructions to a contact at your account party, so that they can view the LC on Bountium. \nInstructions for account party: 1. Set your business up at https://app.bountium.org/business/register, 2. Claim your acccount party status at https://app.bountium.org/business/claimAccountParty/" + str(lc.id) + "/",
                "steve@bountium.org",
                [list(lc.tasked_client_employees.all())[0]],
                fail_silently=False,
            )
            pass
    del json_data['account_party']
    del json_data['applicant_and_ap_j_and_s_obligated']
    del json_data['account_party_name']
    del json_data['account_party_address']

    # Question 13
    if 'advising_bank' in json_data:
        bank_name = json_data['advising_bank']
        if Bank.objects.filter(name=bank_name).exists():
            lc.advising_bank = Bank.objects.get(name=bank_name)
        else:
            # TODO this breaks for lcs where issuer empl has not yet been assigned
            """send_mail(
                lc.issuer.name + " has created an LC to work with you on Bountium",
                lc.issuer.name + ": Forward these instructions to a contact at the advising bank, so that they can view the LC on Bountium. \nInstructions for advising bank: 1. Set your bank up at https://app.bountium.org/bank/register, 2. Claim your advising bank status at https://app.bountium.org/bank/claimAdvising/" + str(lc.id) + "/",
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
    lc.units_of_measure = json_data['unit_of_measure']
    lc.units_purchased = json_data['units_purchased']
    lc.unit_error_tolerance = json_data['unit_error_tolerance']
    lc.confirmation_means = json_data['confirmation_means']
    del json_data['exchange_rate_tolerance']
    del json_data['purchased_item']
    del json_data['unit_of_measure']
    del json_data['units_purchased']
    del json_data['unit_error_tolerance']
    del json_data['confirmation_means']

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

    # TODO typed: when creating doc reqs, actually use all the fields in json_data, updating specifically typed doc reqs if some of them are missing. don't have to use in is_satisfied if you're scared of conflicting with ucp600

    # Question 37
    if json_data['commercial_invoice_required'] != "No":
        required_values = (
            "Version required: " + json_data['commercial_invoice_required'][5:]
            + "\nIncoterms to show: " + lc.incoterms_to_show
            + "\nNamed place of destination: " + lc.named_place_of_destination
        )
        required_values += "\nCopies: " + str(json_data['commercial_invoice_copies'])
        del json_data['commercial_invoice_copies']
        # TODO typed: test
        ci = CommercialInvoiceRequirement(
            for_lc = lc,
            doc_name="Commercial Invoice",
            required_values=required_values,
            due_date=lc.draft_presentation_date,
            type="Commercial Invoice"
        )
        ci.save()
    del json_data['commercial_invoice_required']

    # Question 38
    if 'required_transport_docs' in json_data:
        required_values = ""
        # Question 39
        for transport_doc_marking in json_data['transport_doc_marking']:
            required_values += "Marked " + transport_doc_marking + "\n"
        required_values = required_values[:-1]
        del json_data['transport_doc_marking']
        # TODO typed:  convert this to if xxx in json_data for the 3 transport doc types
        # we support
        for required_transport_doc in json_data['required_transport_docs']:
            lc.documentaryrequirement_set.create(
                doc_name=required_transport_doc,
                due_date=lc.draft_presentation_date,
                required_values=required_values
            )
        del json_data['required_transport_docs']

    # TODO typed: implement the below classes

    # Question 40
    if 'copies_of_packing_list' in json_data:
        if json_data['copies_of_packing_list'] != 0:
            lc.documentaryrequirement_set.create(
                doc_name="Packing List",
                due_date=lc.draft_presentation_date
            )
        del json_data['copies_of_packing_list']

    # Question 41
    if 'copies_of_certificate_of_origin' in json_data:
        if json_data['copies_of_certificate_of_origin'] != 0:
            lc.documentaryrequirement_set.create(
                doc_name="Certificate of Origin",
                due_date=lc.draft_presentation_date
            )
        del json_data['copies_of_certificate_of_origin']

    # Question 42
    # TODO typed: use inspeciton certificate model
    if 'copies_of_inspection_certificate' in json_data:
        if json_data['copies_of_inspection_certificate'] != 0:
            lc.documentaryrequirement_set.create(
                doc_name="Inspection Certificate",
                due_date=lc.draft_presentation_date
            )
        del json_data['copies_of_inspection_certificate']

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
            lc.documentaryrequirement_set.create(**doc_req)
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

    # 2. for any other fields left in json_data, save them as a tuple
    #    in other_data
    lc.other_data = json_data

    # 3. save and return back!
    lc.save()
