"""
AMAT customizations.
"""
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from edxmako.shortcuts import render_to_response

from student.models import UserProfile


def is_honor_code_accepted(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.meta:
        meta = json.loads(user_profile.meta)
        if meta.get("honor_code_accepted_on"):
            return True
    return False


def honorcode(request):
    return render_to_response("honor_code.html", {})


@login_required
def accept_honorcode(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.meta:
        meta = json.loads(user_profile.meta)
    else:
        meta = {}
    accepted_on = datetime.datetime.now()
    meta["honor_code_accepted_on"] = str(accepted_on)
    user_profile.meta = json.dumps(meta)
    user_profile.save()
    return HttpResponse(accepted_on)
