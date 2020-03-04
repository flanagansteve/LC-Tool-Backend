from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
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
        all_businesses_json = serializers.serialize('json', all_businesses)
        return HttpResponse(all_businesses_json, content_type="application/json")
    elif request.method == "POST":
        json_data = json.loads(request.body)
        # 1. create the business
        try:
            business = Business(name = json_data['new_business_name'])
            business.save()
        except:
            pass
        # 2. create the first employee (must be sent as well)
        try:
            business.businessemployee_set.create(name = json_data['name'], title = json_data['title'], email = json_data['email'])
        except KeyError:
            # TODO freak tf out
            pass
        # 3. create a User for this first employee
        first_user = User.objects.create(username = json_data['email'],
            email = json_data['email'])
        first_user.set_password(json_data['password'])
        # 4. return the objects_created (user object, business) as well as a session obj
        now = str(datetime.datetime.now())
        return HttpResponse("{\"bountium_access_token\":\"" + first_user.username + now + "\"," +
            "\"objects_created\":" + serializers.serialize('json', [ business, first_user, ]) + "}")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, POST")

# TODO authenticate this - whos allowed to R, and to UD?
def rud_business(request, business_id):
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            business = Business.objects.get(id=business_id)
        except Business.DoesNotExist:
            raise Http404("No business with id " + business_id)
        return HttpResponse(serializers.serialize('json', [ business, ]), content_type="application/json")
    elif request.method == "DELETE":
        try:
            Business.objects.delete(business_id)
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to delete a business employee. Need an ID to delete")
        except BusinessEmployee.DoesNotExist:
            return Http404(str(business) + " does not have an employee with id " + json_data['id'] + " to delete.")
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        # TODO might want to make this more flexible if the business object gets more complex
        try:
            Business.objects.update(business_id, name = json_data['name'])
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to update a business employee. Required fields are XXX")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")

# TODO authenticate this - whos allowed to invite teammates?
@csrf_exempt
def invite_teammate(request, business_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        raise Http404("No business with id " + business_id + " for you to invite a teammate to")
    # TODO handle empty body, bad json, or non-post-request
    json_data = json.loads(request.body)
    # 1a. Has this teammate hasn't already been invited?
    # TODO handle key error
    invitee_email = json_data['invitee_email']
    try:
        invitee = business.businessemployee_set.get(email = invitee_email)
        # 2. if so - have they registered?
        if invitee.name is not None:
            # 2a. if they have - return status:registered and the user object
            return HttpResponse("{\"status\":\"registered\", \"employee\":" + serializers.serialize(invitee) + "}", content_type="application/json")
        else:
            # 2c. if they have not - re-invite, then return status:reinvited [now]
            # TODO write the email to send as args: subject, message, from_email=None
            User.objects.get(email = invitee_email).email_user()
            now = str(datetime.datetime.now())
            return HttpResponse("{\"status\":\"re-invited on " + now + "\"}", content_type="application/json")
    # 1b. If they have not been invited
    except BusinessEmployee.DoesNotExist:
        # TODO 2. mail an invite
        # TODO write the email to send as args: subject, message, from_email=None
        User.objects.get(email = invitee_email).email_user()
        # 3. save them and return status:invited [now]
        # TODO exceptions to handle here?
        business.businessemployee_set.create(email = invitee_email)
        now = str(datetime.datetime.now())
        return HttpResponse("{\"status\":\"invited on \"" + now + "\"}", content_type="application/json")

# POST
# - email, both to validate the invite & create credentials
# - password
# - name and title (NOTE we might make this optional)
# and receive back
# - a user object w/ session cookie
# TODO handle key errors
@csrf_exempt
def register_upon_invitation(request, business_id):
    new_user_data = json.loads(request.body)
    # 1. First, verify that this user has indeed been invited to the business
    # they're trying to register into
    # a. get the business by business_id. Check for error
    try:
        business = Businesss.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Http404("There is no business with id " + business_id)
    # b. check if there is a businessemployee with email=new_user_data['email'],
    #    and blanks for all other fields. Check for error on either.
    new_employee = Business.businessemployee_set.get(email=new_user_data['emai'])
    if new_employee is None:
        return Http404("There is no invitation for email " + new_user_data['emai'])
    if new_employee.username:
        return HttpResponse("401: Someone has already used this invitation. Ask whoever administers Bountium at your employer about this.")
    # 2. Register the user account
    new_user = User.objects.create(username = new_user_data['email'],
        email = new_user_data['email'])
    new_user.set_password(new_user_data['password'])
    # 3. Update the businessemployee with full fields
    business.businessemployee_set.update(new_employee.id,
        name = new_user_data['name'],
        title = new_user_data['title'])
    # 4. return user object w/token
    request.session['logged_in'] = True
    # TODO what does ryan need to know after a login?
        # does he need a special cookie?
        # does he need params about the user, like which business they're a part of?
            # or will he ask for those other things as he needs them?
    # using this for testing:
    now = str(datetime.datetime.now())
    return HttpResponse('{\"bountium_access_token\":\"' + new_user.username + now + "\"}", content_type="application/json")

# POST email & password, receive back one of
# - a user object w/ session cookie
# - a rejection for invalid creds
# TODO upgrade to django-oauth-toolkit
# TODO do we need to use business_id? i feel like not
# TODO handle KeyError
@csrf_exempt
def login(request, business_id):
    login_attempt = json.loads(request.body)
    user = authenticate(username=login_attempt['email'], password=login_attempt['password'])
    if user is not None:
        if user.is_active:
            # TODO what does ryan need to know after a login?
                # does he need a special cookie?
                # does he need params about the user, like which business they're a part of?
                    # or will he ask for those other things as he needs them?
            request.session['logged_in'] = True
            now = str(datetime.datetime.now())
            return HttpResponse('{\"bountium_access_token\":\"' + user.username + now + "\"}", content_type="application/json")
    return HttpResponseBadRequest('401: invalid credentials')

@csrf_exempt
def logout(request, business_id):
    # TODO authenticate this somehow - does this work?
    if request.user.is_authenticated():
        request.session['logged_in'] = False
    return HttpResponse("{\"success\":true}")

# TODO authenticate this - whos allowed to R (and in what detail), and to UD?
def rud_business_employee(request, business_id, employee_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        raise Http404("No business with id " + business_id)
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            return HttpResponse(serializers.serialize('json', [ business.businessemployee_set.get(id=employee_id), ]), content_type="application/json")
        except BusinessEmployee.DoesNotExist:
            raise Http404(str(business) + " does not have an employee with id " + employee_id)
    elif request.method == "DELETE":
        try:
            business.businessemployee_set.delete(id = employee_id)
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to delete a business employee. Need an ID to delete")
        except BusinessEmployee.DoesNotExist:
            return Http404(str(business) + " does not have an employee with id " + employee_id + " to delete.")
    # TODO this should be more flexible, to eventually handle obj mutation like:
        # getting assigned to LCs
        # notifications about actions to take on an LC
        # licenses / competencies of an employee
    # There's probably something built-in that lets you go directly from
    # json obj to Django model, anyways
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        try:
            business.businessemployee_set.update(employee_id, name = json_data['name'], title = json_data['title'], email = json_data['email'])
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to update a business employee. Required fields are name, title, and email. You can supply old values for the other fields if you plan on only updating a few.")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")
