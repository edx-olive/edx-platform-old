"""
AMAT customizations.
"""
import datetime
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
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


def GetEmployeeIDUsingDjangoID(request):
    """
      Get the employee id of user using the django id
    """
    user_id = request.GET["user_id"]
    user = User.objects.get(id=user_id)  # Get The User Object
    social = user.social_auth.get(provider='tpa-saml')
    return JsonResponse({"Employee_ID": social.uid.split(':')[1], "email": user.email})
