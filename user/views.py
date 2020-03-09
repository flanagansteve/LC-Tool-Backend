from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest, Http404, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.views.decorators.csrf import csrf_exempt
from bank.models import Bank, BankEmployee
from business.models import Business, BusinessEmployee
import json, datetime

# POST email & password, receive back one of
# - TODO return the User, the user's employee object, & the user's employer object
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
            userEmployee = None
            usersEmployer = None
            if BankEmployee.objects.filter(email=user.username).exists():
                userEmployee = BankEmployee.objects.get(email=user.username)
                usersEmployer = userEmployee.bank
            else:
                userEmployee = BusinesssEmployee.objects.get(email=user.username)
                usersEmployer = userEmployee.employer
            now = str(datetime.datetime.now())
            return JsonResponse({
                "bountium_access_token" : user.username + now,
                "userEmployee" : model_to_dict(userEmployee),
                "usersEmployer" : model_to_dict(usersEmployer)
            })
        else:
            return HttpResponseForbidden('Invalid credentials')
    else:
        return HttpResponseBadRequest('This endpoint only supports POST requests')

# TODO return the User, the user's employee object, & the user's employer object
@csrf_exempt
def user_logout(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            logout(request, user)
            return JsonResponse({"success":True})
        else:
            return HttpResponseForbidden('You must be logged in to log out')
    else:
        return HttpResponseBadRequest('This endpoint only supports POST requests')
