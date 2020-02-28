from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Bank, BankEmployee
import json, datetime

# GET all the banks, or POST a new bank
def index(request):
    # TODO is there ever a situation where we GET all the banks?
    if request.method == "GET":
        all_banks = Bank.objects.all()
        all_banks_json = serializers.serialize('json', all_banks)
        return HttpResponse(all_banks_json, content_type="application/json")
    elif request.method == "POST":
        json_data = json.loads(request.body)
        try:
            # 1. create the bank
            bank = Bank(name = json_data['new_bank_name'])
            bank.save()
            # 2. create the first employee (must be sent as well)
            try:
                bank.bankemployee_set.create(name = json_data['name'], title = json_data['title'], email = json_data['email'])
            except KeyError:
                # TODO freak tf out
                pass
                # TODO 3. register the first employee
                # TODO what to return back to front end?
        except:
            pass
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
        return HttpResponse(serializers.serialize('json', [ bank, ]))
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
        raise HttpResponseBadRequest("This endpoint only supports GET, POST, DELETE, PUT")

# TODO authenticate this - whos allowed to invite teammates?
def invite_teammate(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with id " + bank_id + " for you to invite a teammate to")
    # TODO exception handling - what if it aint a post, bad json, etc
    json_data = json.loads(request.body)
    try:
        bank.bankemployee_set.create(email = json_data['invitee_email'], bank = bank.id)
    except KeyError:
        # TODO freak tf out
        pass
    # TODO return something

# POST
# - email, both to validate the invite & create credentials
# - password
# - name and title (NOTE we might make this optional)
# and receive back
# - a user object w/ session cookie
# TODO handle key errors
def register_upon_invitation(request, bank_id):
    new_user_data = json.loads(request.body)
    # 1. First, verify that this user has indeed been invited to the bank
    # they're trying to register into
    # a. get the bank by bank_id. Check for error
    try:
        bank = Banks.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("There is no bank with id " + bank_id)
    # b. check if there is a bankemployee with email=new_user_data['email'],
    #    and blanks for all other fields. Check for error on either.
    new_employee = Bank.bankemployee_set.get(email=new_user_data['emai'])
    if new_employee is None:
        return Http404("There is no invitation for email " + new_user_data['emai'])
    if new_employee.username:
        return HttpResponse("401: Someone has already used this invitation. Ask whoever administers Bountium at your employer about this.")
    # 2. Register the user account
    new_user = User.objects.create(username = new_user_data['email'],
        email = new_user_data['email'])
    new_user.set_password(new_user_data['password')
    # 3. Update the bankemployee with full fields
    bank.bankemployee_set.update(new_employee.id,
        name = new_user_data['name'],
        title = new_user_data['title'])
    # 4. return user object w/token
    # TODO what does ryan need to know after a login?
        # does he need a special cookie?
        # does he need params about the user, like which bank they're a part of?
            # or will he ask for those other things as he needs them?
    # using this for testing:
    now = str(datetime.datetime.now())
    return HttpResponse('{\"bountium_access_token\":\"' + new_user.username + now + "\"}", content_type="application/json")

# POST email & password, receive back one of
# - a user object w/ session cookie
# - a rejection for invalid creds
# TODO upgrade to django-oauth-toolkit
# TODO do we need to use bank_id? i feel like not
# TODO handle KeyError
def login(request, bank_id):
    login_attempt = json.loads(request.body)
    user = authenticate(username=login_attempt['email'], password=login_attempt['password'])
    if user is not None:
        if user.is_active:
            #login(request, user)
            # TODO what does ryan need to know after a login?
                # does he need a special cookie?
                # does he need params about the user, like which bank they're a part of?
                    # or will he ask for those other things as he needs them?
            now = str(datetime.datetime.now())
            return HttpResponse('{\"bountium_access_token\":\"' + user.username + now + "\"}", content_type="application/json")
    return HttpResponseBadRequest('401: invalid credentials')

# TODO authenticate this - whos allowed to R (and in what detail), and to UD?
def rud_bank_employee(request, bank_id, employee_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        raise Http404("No bank with id " + bank_id)
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            return HttpResponse(serializers.serialize('json', [ bank.bankemployee_set.get(id=employee_id), ]))
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
