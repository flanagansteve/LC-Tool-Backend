from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseBadRequest, Http404
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import LC
import json, datetime

# 1. GET all the lcs
# 2. POST TODO
@csrf_exempt
def index(request):
    return HttpResponse("nice")
