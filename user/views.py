from django.shortcuts import render

from django.http import HttpResponse
from django.http import HttpResponseBadRequest, Http404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json, datetime

# POST email & password, receive back one of
# - a user object w/ session cookie
# - a rejection for invalid creds
# TODO upgrade to django-oauth-toolkit
# TODO return the User, the user's employee object, & the user's employer object
@csrf_exempt
def user_login(request):
    if request.method == "POST":
        login_attempt = json.loads(request.body)
        try:
            user = authenticate(request, username=login_attempt['email'], password=login_attempt['password'])
        except KeyError:
            return HttpResponseBadRequest('400: you must send a JSON object with an email and password')
        if user is not None:
            login(request, user)
            now = str(datetime.datetime.now())
            return HttpResponse('{\"bountium_access_token\":\"' + user.username + now + "\"}", content_type="application/json")
        else:
            return HttpResponseBadRequest('403: invalid credentials')
    else:
        return HttpResponseBadRequest('400: this endpoint only supports POST requests')

# TODO return something
@csrf_exempt
def user_logout(request):
    if request.method == "POST":
        if request.user.is_authenticated():
            logout(request, user)
            return HttpResponse("{\"success\":true}")
        else:
            return HttpResponseBadRequest('403: you must be logged in to log out')
    else:
        return HttpResponseBadRequest('400: this endpoint only supports POST requests')
