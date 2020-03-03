from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import LC, LCEmployee
import json, datetime

# 1. GET all the lcs
# 2. POST TODO
@csrf_exempt
def index(request):
    # TODO is there ever a situation where we GET all the lcs?
    if request.method == "GET":
        all_lcs = LC.objects.all()
        all_lcs_json = serializers.serialize('json', all_lcs)
        return HttpResponse(all_lcs_json, content_type="application/json")
    elif request.method == "POST":
        json_data = json.loads(request.body)
        # 1. create the lc
        try:
            #TODO
            #lc = LC(name = json_data['new_lc_name'])
            #lc.save()
        except:
            pass
        # 2. return TODO
        return HttpResponse("nice")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, POST")

# TODO authenticate this - whos allowed to R, and to UD?
def rud_lc(request, lc_id):
    # lol python has no switch(). could use a dict + lambdas, but its only 3 branches...
    if request.method == "GET":
        try:
            lc = LC.objects.get(id=lc_id)
        except LC.DoesNotExist:
            raise Http404("No lc with id " + lc_id)
        return HttpResponse(serializers.serialize('json', [ lc, ]), content_type="application/json")
    elif request.method == "DELETE":
        try:
            LC.objects.delete(lc_id)
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to delete a lc employee. Need an ID to delete")
        except LCEmployee.DoesNotExist:
            return Http404(str(lc) + " does not have an employee with id " + json_data['id'] + " to delete.")
    elif request.method == "PUT":
        json_data = json.loads(request.body)
        try:
            # TODO
            #LC.objects.update(lc_id, name = json_data['name'])
            # TODO return something
        except KeyError:
            return HttpResponseBadRequest("Badly formatted json to update a lc employee. Required fields are XXX")
    else:
        raise HttpResponseBadRequest("This endpoint only supports GET, DELETE, PUT")
