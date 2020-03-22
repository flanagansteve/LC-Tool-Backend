from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
import json, datetime

# POST email & password, receive back one of
# - return the User, the user's employee object, & the user's employer object
# - a rejection for invalid creds
# TODO upgrade to django-oauth-toolkit
@csrf_exempt
def user_login(request):
    if request.method == "POST":
        login_attempt = json.loads(request.body)
        try:
            user = authenticate(request, username=login_attempt['email'], password=login_attempt['password'])
        except KeyError:
            response = HttpResponseBadRequest('You must send a JSON object with an email and password')
            return response
        if user is not None:
            login(request, user)
            user_employee = None
            users_employer = None
            if BankEmployee.objects.filter(email=user.username).exists():
                user_employee = BankEmployee.objects.get(email=user.username)
                users_employer = user_employee.bank
            else:
                user_employee = BusinesssEmployee.objects.get(email=user.username)
                users_employer = user_employee.employer
            return JsonResponse({
                "session_expiry" : request.session.get_expiry_date(),
                "user_employee" : model_to_dict(user_employee),
                "users_employer" : model_to_dict(users_employer)
            })
        else:
            return HttpResponseForbidden('Invalid credentials')
    else:
        return HttpResponseBadRequest('This endpoint only supports POST requests')

@csrf_exempt
def user_logout(request):
    if request.method == "POST":
        logout(request, user)
        return JsonResponse({"success":True})
    else:
        return HttpResponseBadRequest('This endpoint only supports POST requests')

@csrf_exempt
def change_password(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            this_user = User.objects.get(username=request.user.username)
            this_user.set_password(json_data['new_password'])
            return JsonResponse({"success":True})
        else:
            return HttpResponseForbidden('You must be logged in to change your password.')
    else:
        return HttpResponseBadRequest('This endpoint only supports POST requests')
