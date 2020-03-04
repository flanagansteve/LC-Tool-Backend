from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from .models import Bank, BankEmployee
import json, datetime

# TODO on a bad request, set status_code to give a specific error code
# 1. GET all the banks
# 2. POST [the fields of a bank and employee]
#    and receive back [a session, and the objects_created [the bank obj u created and the new user]]
@csrf_exempt
def index(request):
    # TODO is there ever a situation where we GET all the banks?
    if request.method == "GET":
        all_banks = Bank.objects.all()
        return JsonResponse(list(all_banks.values()), safe=False)
    elif request.method == "POST":
        json_data = json.loads(request.body)
        # 1. create the bank
        try:
            bank = Bank(name = json_data['new_bank_name'])
            bank.save()
        except:
            pass
        # 2. create the first employee (must be sent as well)
        try:
            bank.bankemployee_set.create(name = json_data['name'], title = json_data['title'], email = json_data['email'])
        except KeyError:
            # TODO freak tf out
            pass
        # 3. create a User for this first employee, and log them in
        first_user = User.objects.create_user(username=json_data['email'],
                                 email=json_data['email'],
                                 password=json_data['password'])
        first_user = authenticate(username=json_data['email'], password=json_data['password'])
        login(request, first_user)
        # 4. return the objects_created (user object, bank) as well as a session obj
        now = str(datetime.datetime.now())
        response = {
            "bountium_access_token" : first_user.username + now,
            "objects_created" : [
                model_to_dict(bank), model_to_dict(first_user)
            ]
        }
        return JsonResponse(response)
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, POST")

# TODO authenticate this - whos allowed to R, and to UD?
def rud_bank(request, bank_id):
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            raise Http404("No bank with id " + bank_id)
        return JsonResponse(model_to_dict(bank))
    elif request.method == "DELETE":
        try:
            Bank.objects.delete(bank_id)
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to delete a bank employee. Need an ID to delete")
        except BankEmployee.DoesNotExist:
            return Http404(str(bank) + " does not have an employee with id " + json_data['id'] + " to delete.")
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        # TODO might want to make this more flexible if the bank object gets more complex
        try:
            Bank.objects.update(bank_id, name = json_data['name'])
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to update a bank employee. Required fields are XXX")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")

# TODO authenticate this - whos allowed to invite teammates?
@csrf_exempt
def invite_teammate(request, bank_id):
    if request.method == "POST":
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            raise Http404("No bank with id " + bank_id + " for you to invite a teammate to")
        # TODO handle empty body, bad json, or non-post-request
        json_data = json.loads(request.body)
        response = {"status" : "registered"}
        # 1a. Has this teammate already been invited?
        try:
            invitee_email = json_data['invitee_email']
        except KeyError:
            return HttpResponseBadRequest("You must send a request with a JSON object body, with an \"invitee_email\" field")
        try:
            invitee = bank.bankemployee_set.get(email = invitee_email)
            # 2. if so - have they registered?
            if invitee.name is not None:
                # 2a. if they have - return status:registered and the user object
                response["employee"] = model_to_dict(invitee)
            else:
                # 2c. if they have not - re-invite, then return status:reinvited [now]
                # TODO write the email to send as args: subject, message, from_email=None
                User.objects.get(email = invitee_email).email_user()
                now = str(datetime.datetime.now())
                response["status"] = "re-invited on " + now
        # 1b. If they have not been invited
        except BankEmployee.DoesNotExist:
            # 2. mail an invite
            # TODO write the email to send as args: subject, message, from_email=None
            User.objects.get(email = invitee_email).email_user()
            # 3. save them and return status:invited [now]
            bank.bankemployee_set.create(email = invitee_email)
            now = str(datetime.datetime.now())
            response["status"] = "invited on " + now
        return JsonResponse(response)
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# POST
# - email, both to validate the invite & create credentials
# - password
# - name and title (NOTE we might make this optional)
# and receive back
# - TODO what does ryan want back?
@csrf_exempt
def register_upon_invitation(request, bank_id):
    if request.method == "POST":
        new_user_data = json.loads(request.body)
        # 1. First, verify that this user has indeed been invited to the bank
        # they're trying to register into
        # a. get the bank by bank_id. Check for error
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Http404("There is no bank with id " + bank_id)
        # b. check if there is a bankemployee with email=new_user_data['email'],
        #    and blanks for all other fields. Check for error on either.
        new_employee = bank.bankemployee_set.get(email=new_user_data['email'])
        if new_employee is None:
            return Http404("There is no invitation for email " + new_user_data['email'])
        if new_employee.username:
            return HttpResponse("Someone has already used this invitation. Ask whoever administers Bountium at your employer about this.", status=401)
        # 2. Register the user account
        new_user = User.objects.create_user(username=new_user_data['email'],
                                 email=new_user_data['email'],
                                 password=new_user_data['password'])
        new_user = authenticate(username=new_user_data['email'], password=new_user_data['password'])
        login(request, new_user)
        # 3. Update the bankemployee with full fields
        bank.bankemployee_set.update(new_employee.id,
            name = new_user_data['name'],
            title = new_user_data['title'])
        # 4. return user object w/token
        # using this for testing:
        now = str(datetime.datetime.now())
        return HttpResponse('{\"bountium_access_token\":\"' + new_user.username + now + "\"}", content_type="application/json")
    else:
        return HttpResponseBadRequest("This endpoint only accepts POST requests")

# TODO authenticate this - whos allowed to R (and in what detail), and to UD?
def rud_bank_employee(request, bank_id, employee_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with id " + bank_id)
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            return JsonResponse(model_to_dict(bank.bankemployee_set.get(id=employee_id)))
        except BankEmployee.DoesNotExist:
            raise Http404(str(bank) + " does not have an employee with id " + employee_id)
    elif request.method == "DELETE":
        try:
            bank.bankemployee_set.delete(id = employee_id)
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to delete a bank employee. Need an ID to delete")
        except BankEmployee.DoesNotExist:
            return Http404(str(bank) + " does not have an employee with id " + employee_id + " to delete.")
    # TODO this should be more flexible, to eventually handle obj mutation like:
        # getting assigned to LCs
        # notifications about actions to take on an LC
        # licenses / competencies of an employee
    # There's probably something built-in that lets you go directly from
    # json obj to Django model, anyways
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        try:
            bank.bankemployee_set.update(employee_id, name = json_data['name'], title = json_data['title'], email = json_data['email'])
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to update a bank employee. Required fields are name, title, and email. You can supply old values for the other fields if you plan on only updating a few.")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")
