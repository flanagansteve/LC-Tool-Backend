from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.core import serializers
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from .models import Bank, BankEmployee, LCAppQuestion
from .values import default_questions
from util import update_django_instance_with_subset_json
import json, datetime

# 1. GET all the banks
# 2. POST [the fields of a bank and employee]
#    and receive back [a session, and the objects_created [the bank obj u created and the new user]]
# TODO this should do all error checking THEN save instances.
# currently, it will save instances but return an error
# later in the function, leading to bad data
@csrf_exempt
def index(request):
    if request.method == "GET":
        all_banks = Bank.objects.all()
        return JsonResponse(list(all_banks.values()), safe=False)
    elif request.method == "POST":
        json_data = json.loads(request.body)
        # 1. create the bank
        try:
            bank = Bank(name = json_data['new_bank_name'])
            bank.save()
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to create a bank. Need a \"new_bank_name\" field")
        # 2. create the first employee (must be sent as well)
        try:
            bank.bankemployee_set.create(name = json_data['name'], title = json_data['title'], email = json_data['email'])
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to create a bank. Need the parameters of the bank's first employee - \"email\", \"name\", and \"title\" fields")
        # 3. create a User for this first employee, and log them in
        first_user = User.objects.create_user(username=json_data['email'],
                                 email=json_data['email'],
                                 password=json_data['password'])
        first_user = authenticate(username=json_data['email'], password=json_data['password'])
        login(request, first_user)
        # 4. Start the bank off with the default set of lc application question
        populate_application(bank)
        # 5. return the objects created (user object, bank) as well as a session obj
        return JsonResponse({
            "session_expiry" : request.session.get_expiry_date(),
            "user_employee" : model_to_dict(bank.bankemployee_set.get(email=json_data['email'])),
            "users_employer" : bank.to_dict()
        })
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

def populate_application(bank):
    # 1. try to get the default questions and save them onto the bank
    for default_question in default_questions:
        if not LCAppQuestion.objects.filter(key=default_question['key']).exists():
            LCAppQuestion.objects.create(**default_question)
        bank.digital_application.add(LCAppQuestion.objects.get(key=default_question['key']))

# TODO more specifically authenticate this - who within a bank is allowed to R, and to UD?
@csrf_exempt
def rud_bank(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with id " + bank_id)
    if request.method == "GET":
        return JsonResponse(bank.to_dict())
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if bank.bankemployee_set.filter(email = request.user.username).exists():
                bank.delete()
                return JsonResponse({
                    "success" : True
                })
            else:
                return HttpResponseForbidden("You may only delete the organisation you are employed by.")
        else:
            return HttpResponseForbidden("You must be logged in to delete your employer's profile.")
    elif request.method == "PUT":
        if request.user.is_authenticated:
            if bank.bankemployee_set.filter(email = request.user.username).exists():
                update_django_instance_with_subset_json(json_data, bank)
                bank.save()
                return JsonResponse({
                    "user_employee" : model_to_dict(bank.bankemployee_set.get(email = request.user.username)),
                    "users_employer" : bank.to_dict()
                })
            else:
                return HttpResponseForbidden("You may only update the organisation you are employed by.")
        else:
            return HttpResponseForbidden("You must be logged in to update your employer's profile.")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")

@csrf_exempt
def invite_teammate(request, bank_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            try:
                bank = Bank.objects.get(id=bank_id)
            except Bank.DoesNotExist:
                return Http404("No bank with id " + bank_id + " for you to invite a teammate to")
            if not bank.bankemployee_set.filter(email=request.user.username).exists():
                return HttpResponseForbidden("You may only invite teammates to your own bank")
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
                    send_mail(
                        bank.bankemployee_set.get(email=request.user.username).name + " has re-invited you to join their team on Bountium",
                        "Register at https://app.bountium.org/bank/register/" + str(bank.id),
                        'steve@bountium.org',
                        [invitee_email],
                        fail_silently=False,
                    )
                    now = str(datetime.datetime.now())
                    response["status"] = "re-invited on " + now
            # 1b. If they have not been invited
            except BankEmployee.DoesNotExist:
                # 2. create the user and mail an invite
                send_mail(
                    bank.bankemployee_set.get(email=request.user.username).name + " has invited you to join their team on Bountium!",
                    "Register at https://app.bountium.org/bank/register/" + str(bank.id),
                    'steve@bountium.org',
                    [invitee_email],
                    fail_silently=False,
                )
                # 3. save them and return status:invited [now]
                bank.bankemployee_set.create(email = invitee_email)
                now = str(datetime.datetime.now())
                response["status"] = "invited on " + now
            return JsonResponse(response)
        else:
            return HttpResponseForbidden("You must be logged in to invite teammates")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# POST
# - email, both to validate the invite & create credentials.py
# - password
# - name and title (NOTE we might make this optional)
# and receive back
# - access token
# - the employee obj
# - the bank obj
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
        if new_employee.name:
            return HttpResponse("Someone has already used this invitation. Ask whoever administers Bountium at your employer about this.", status=401)
        # 2. Register the user account
        new_user = User.objects.create_user(username=new_user_data['email'],
                                 email=new_user_data['email'],
                                 password=new_user_data['password'])
        new_user = authenticate(username=new_user_data['email'], password=new_user_data['password'])
        login(request, new_user)
        # 3. Update the bankemployee with full fields
        bank.bankemployee_set.filter(id=new_employee.id).update(
            name = new_user_data['name'],
            title = new_user_data['title'])
        # 4. return user object w/token
        now = str(datetime.datetime.now())
        return JsonResponse({
            "session_expiry" : request.session.get_expiry_date(),
            "user_employee" : model_to_dict(bank.bankemployee_set.get(email=new_user_data['email'])),
            "users_employer" : bank.to_dict()
        })
    else:
        return HttpResponseBadRequest("This endpoint only accepts POST requests")

@csrf_exempt
# TODO don't let people update their email
def rud_bank_employee(request, bank_id, employee_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with id " + bank_id)
    if request.method == "GET":
        try:
            return JsonResponse(model_to_dict(bank.bankemployee_set.get(id=employee_id)))
        except BankEmployee.DoesNotExist:
            return Http404(str(bank) + " does not have an employee with id " + employee_id)
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if bank.bankemployee_set.filter(id = employee_id).exists():
                bank_employee = bank.bankemployee_set.get(id = employee_id)
                if request.user.username != bank_employee.email:
                    return HttpResponseForbidden("You may only delete your own account. Ask the user with email " + bank_employee.email + " to delete their account if need be.")
                else:
                    bank_employee.delete()
                    return JsonResponse({
                        "success" : True,
                        "users_employer" : bank.to_dict()
                    })
            else:
                return Http404(str(bank) + " does not have an employee with id " + employee_id)
        else:
            return HttpResponseForbidden("You must be logged in to delete your employer's profile.")
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        if request.user.is_authenticated:
            print("Requesters email: " + request.user.username)
            try:
                bank_employee = bank.bankemployee_set.get(id = employee_id)
                print(employee_id + "'s email: " + bank_employee.email)
                if request.user.username != bank_employee.email:
                    return HttpResponseForbidden("You may only update your own account. Ask the user with email " + bank_employee.email + " to update their account if need be.")
                update_django_instance_with_subset_json(json_data, bank_employee)
                bank_employee.save()
            except BankEmployee.DoesNotExist:
                return Http404(str(bank) + " does not have an employee with id " + employee_id)
            return JsonResponse({
                "user_employee" : model_to_dict(bank.bankemployee_set.get(id = employee_id)),
                "users_employer" : bank.to_dict()
            })
        else:
            return HttpResponseForbidden("You must be logged in to update your account.")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")

# TODO pdf app

@csrf_exempt
def cr_digital_app(request, bank_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with id " + bank_id)
    if request.method == 'GET':
        return JsonResponse(bank.get_lc_app(), safe=False)
    elif request.method == 'POST':
        json_data = json.loads(request.body)
        LCAppQuestion.objects.create(**json_data)
        bank.digital_application.add(LCAppQuestion.objects.get(key=json_data['key']))
        return JsonResponse({
            'success':True,
            'new_app':bank.get_lc_app()
        })
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

@csrf_exempt
def ud_digital_app(request, bank_id, question_id):
    try:
        bank = Bank.objects.get(id=bank_id)
    except Bank.DoesNotExist:
        return Http404("No bank with id " + bank_id)
    if request.method == 'PUT':
        json_data = json.loads(request.body)
        question = bank.digital_application.get(id=question_id)
        update_django_instance_with_subset_json(question, json_data)
        question.save()
        return JsonResponse({
            'success':True,
            'new_app':bank.get_lc_app()
        })
    elif request.method == 'DELETE':
        bank.digital_application.get(id=question_id).delete()
        return JsonResponse({
            'success':True,
            'new_app':bank.get_lc_app()
        })
    else:
        return HttpResponseBadRequest("This endpoint only supports PUT, DELETE")
