from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.forms.models import model_to_dict
from .models import Business, BusinessEmployee
import json, datetime

# 1. GET all the businesses
# 2. POST [the fields of a business and employee]
#    and receive back [a session, and the objects_created [the business obj u created and the new user]]
@csrf_exempt
def index(request):
    # TODO is there ever a situation where we GET all the businesses?
    if request.method == "GET":
        all_businesses = Business.objects.all()
        return JsonResponse(list(all_businesses.values()), safe=False)
    elif request.method == "POST":
        json_data = json.loads(request.body)
        # 1. create the business
        try:
            business = Business(name = json_data['new_business_name'])
            business.save()
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to create a business. Need a \"new_business_name\" field")
        # 2. create the first employee (must be sent as well)
        try:
            business.businessemployee_set.create(name = json_data['name'], title = json_data['title'], email = json_data['email'])
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to create a business. Need the parameters of the business's first employee - \"email\", \"name\", and \"title\" fields")
        # 3. create a User for this first employee, and log them in
        first_user = User.objects.create_user(username=json_data['email'],
                                 email=json_data['email'],
                                 password=json_data['password'])
        first_user = authenticate(username=json_data['email'], password=json_data['password'])
        login(request, first_user)
        # 4. return the objects created (user object, business) as well as a session obj
        return JsonResponse({
            "session_expiry" : request.session.get_expiry_date(),
            "user_employee" : model_to_dict(business.businessemployee_set.get(email=json_data['email'])),
            "users_employer" : model_to_dict(business)
        })
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, POST")

# TODO more specifically authenticate this - who within a bank is allowed to R, and to UD?
@csrf_exempt
def rud_business(request, business_id):
    try:
        business = Bank.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Http404("No business with id " + business_id)
    if request.method == "GET":
        return JsonResponse(model_to_dict(business))
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if business.businessemployee_set.filter(email = request.user.username).exists():
                business.delete()
                return JsonResponse({
                    "success" : True
                })
            else:
                return HttpResponseForbidden("You may only delete the organisation you are employed by.")
        else:
            return HttpResponseForbidden("You must be logged in to delete your employer's profile.")
    elif request.method == "PUT":
        if request.user.is_authenticated:
            if business.businessemployee_set.filter(email = request.user.username).exists():
                for key in json_data:
                    if key in dir(business):
                        setattr(business, key, json_data[key])
                    else:
                        # TODO log a bad field but dont flip out
                        pass
                business.save()
                return JsonResponse({
                    "user_employee" : model_to_dict(business.businessemployee_set.get(email = request.user.username)),
                    "users_employer" : model_to_dict(business)
                })
            else:
                return HttpResponseForbidden("You may only update the organisation you are employed by.")
        else:
            return HttpResponseForbidden("You must be logged in to update your employer's profile.")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")

@csrf_exempt
def invite_teammate(request, business_id):
    if request.method == "POST":
        if request.user.is_authenticated:
            try:
                business = Business.objects.get(id=business_id)
            except Business.DoesNotExist:
                return Http404("No business with id " + business_id + " for you to invite a teammate to")
            if not business.businessemployee_set.filter(email=request.user.username).exists():
                return HttpResponseForbidden("You may only invite teammates to your own business")
            json_data = json.loads(request.body)
            response = {"status" : "registered"}
            # 1a. Has this teammate already been invited?
            try:
                invitee_email = json_data['invitee_email']
            except KeyError:
                return HttpResponseBadRequest("You must send a request with a JSON object body, with an \"invitee_email\" field")
            try:
                invitee = business.businessemployee_set.get(email = invitee_email)
                # 2. if so - have they registered?
                if invitee.name is not None:
                    # 2a. if they have - return status:registered and the user object
                    response["employee"] = model_to_dict(invitee)
                else:
                    # 2c. if they have not - re-invite, then return status:reinvited [now]
                    # TODO confirm with ryan that this is the registration link / that we don't need to embed url params:
                    link = "https://bountium.org/register"
                    send_mail(
                        business.businessemployee_set.get(email=request.user.username).name + " has re-invited you to join their team on Bountium",
                        "Register at " + link,
                        'steve@bountium.org',
                        [invitee_email],
                        fail_silently=False,
                    )
                    now = str(datetime.datetime.now())
                    response["status"] = "re-invited on " + now
            # 1b. If they have not been invited
            except BusinessEmployee.DoesNotExist:
                # 2. create the user and mail an invite
                # TODO confirm with ryan that this is the registration link / that we don't need to embed url params:
                link = "https://bountium.org/register"
                send_mail(
                    business.businessemployee_set.get(email=request.user.username).name + " has invited you to join their team on Bountium!",
                    "Register at " + link,
                    'steve@bountium.org',
                    [invitee_email],
                    fail_silently=False,
                )
                # 3. save them and return status:invited [now]
                business.businessemployee_set.create(email = invitee_email)
                now = str(datetime.datetime.now())
                response["status"] = "invited on " + now
            return JsonResponse(response)
        else:
            return HttpResponseForbidden("You must be logged in to invite teammates")
    else:
        return HttpResponseBadRequest("This endpoint only supports POST")

# POST
# - email, both to validate the invite & create credentials
# - password
# - name and title (NOTE we might make this optional)
# and receive back
# - access token
# - the employee obj
# - the bank obj
@csrf_exempt
def register_upon_invitation(request, business_id):
    if request.method == "POST":
        new_user_data = json.loads(request.body)
        # 1. First, verify that this user has indeed been invited to the business
        # they're trying to register into
        # a. get the business by business_id. Check for error
        try:
            business = Business.objects.get(id=business_id)
        except Bank.DoesNotExist:
            return Http404("There is no business with id " + business_id)
        # b. check if there is a businessemployee with email=new_user_data['email'],
        #    and blanks for all other fields. Check for error on either.
        new_employee = business.businessemployee_set.get(email=new_user_data['email'])
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
        # 3. Update the businessemployee_set with full fields
        business.businessemployee_set.filter(id=new_employee.id).update(
            name = new_user_data['name'],
            title = new_user_data['title'])
        # 4. return user object w/token
        return JsonResponse({
            "session_expiry" : request.session.get_expiry_date(),
            "user_employee" : model_to_dict(business.businessemployee_set.get(email=new_user_data['email'])),
            "users_employer" : model_to_dict(business)
        })
    else:
        return HttpResponseBadRequest("This endpoint only accepts POST requests")

@csrf_exempt
# TODO don't let people update their email
def rud_business_employee(request, business_id, employee_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Http404("No business with id " + business_id)
    if request.method == "GET":
        try:
            return JsonResponse(model_to_dict(business.businessemployee_set.get(id=employee_id)))
        except BankEmployee.DoesNotExist:
            return Http404(str(business) + " does not have an employee with id " + employee_id)
    elif request.method == "DELETE":
        if request.user.is_authenticated:
            if business.businessemployee_set.filter(id = employee_id).exists():
                business_employee = business.businessemployee_set.get(id = employee_id)
                if request.user.username != business_employee.email:
                    return HttpResponseForbidden("You may only delete your own account. Ask the user with email " + business_employee.email + " to delete their account if need be.")
                else:
                    business_employee.delete()
                    return JsonResponse({
                        "success" : True,
                        "users_employer" : model_to_dict(business)
                    })
            else:
                return Http404(str(business) + " does not have an employee with id " + employee_id)
        else:
            return HttpResponseForbidden("You must be logged in to delete your employer's profile.")
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        if request.user.is_authenticated:
            try:
                business_employee = business.businessemployee_set.get(id = employee_id)
                if request.user.username != business_employee.email:
                    return HttpResponseForbidden("You may only update your own account. Ask the user with email " + business_employee.email + " to update their account if need be.")
                for key in json_data:
                    if key in dir(business_employee):
                        setattr(business_employee, key, json_data[key])
                    else:
                        # TODO log a bad field but dont flip out
                        pass
                business_employee.save()
            except BusinessEmployee.DoesNotExist:
                return Http404(str(business) + " does not have an employee with id " + employee_id)
            return JsonResponse({
                "user_employee" : model_to_dict(business.businessemployee_set.get(id = employee_id)),
                "users_employer" : model_to_dict(business)
            })
        else:
            return HttpResponseForbidden("You must be logged in to update your account.")
    else:
        return HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")
