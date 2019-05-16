"""
AMAT customizations.
"""
import datetime
import json
import urllib
import urllib2

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile
from util.custom_views import get_all_env_tokens, _get_course_team


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


def authorized_users(group_list={}, all_superusers=False, all_staff=False):

    def ensure_right_access(_function):
        def _ensure_right_access(request, *args, **kwargs):
            if all_superusers and request.user.is_superuser:
                return _function(request, *args, **kwargs)
            if all_staff and request.user.is_staff:
                return _function(request, *args, **kwargs)
            for group_name in group_list:
                group = Group.objects.filter(name=group_name).first()
                if group is not None and request.user in group.user_set.all():
                    return _function(request, *args, **kwargs)
            return HttpResponse('{"status":"error", "message":"forbidden"}')
        return _ensure_right_access
    return ensure_right_access


def send_release_request(course_id):

    studio_url = get_all_env_tokens()["CMS_BASE"]
    group = Group.objects.filter(name="RELEASE_ADMINS").first()
    if group is None or len(group.user_set.all()) == 0:
        return HttpResponse('{"status":"error", "message":"Release Admins group is not set or no users present"}')
    release_admins = group.user_set.all()
    admin_emails = []
    for admin in release_admins:
        admin_emails.append(admin.email)
    course_url = "https://" + studio_url + "/course/" + course_id
    release_url = "https://" + studio_url + "/start_course?course_id=" + course_id
    overview = CourseOverview.objects.get(id = CourseKey.from_string(course_id))
    course_name = overview.display_name
    course_team = _get_course_team(course_id)
    course_team_mails = list()
    course_admin_mails = course_team.get("admins")
    course_staff_mails = course_team.get("staff")
    if course_admin_mails is not None:
        course_team_mails += course_admin_mails
    if course_staff_mails is not None:
        course_team_mails += course_staff_mails

    #Mailer(18, ";".join(admin_emails), {"course_name":course_name}, {"course_name":course_name, "course_url":course_url, "release_url":release_url, "sender": "appliedx_ops@amat.com"}, mail_cc=",".join(course_team_mails)).mail_send()
    return HttpResponse('{"status":"success", "emails":"' + ",".join(admin_emails) + '"}')


@login_required
@authorized_users({"AGU_ADMINS"}, all_superusers=False, all_staff=False)
def set_agu_url(request):
    user = request.user
    agu_url = urllib.quote(request.POST.get('agu_url'))
    course_id = request.POST.get('course_id')
    studio_url = get_all_env_tokens()["CMS_BASE"]
    url = "https://" + studio_url + "/update_course_metadata?course_id=" + urllib.quote(course_id) + "&attr_name=cert_name_long&attr_val=" + agu_url + "&user=" + str(user.username)
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    resp_text = str(resp.read())
    overview = CourseOverview.objects.get(id = CourseKey.from_string(course_id))
    course_name = overview.display_name
    email = user.email
    course_team = _get_course_team(course_id)
    course_team_mails = list()
    course_admin_mails = course_team.get("admins")
    course_staff_mails = course_team.get("staff")
    if course_admin_mails is not None:
        course_team_mails += course_admin_mails
    if course_staff_mails is not None:
        course_team_mails += course_staff_mails
    #Mailer(5, email, {"course_name":course_name}, {"course_name":course_name, "sender": "applied_ops@amat.com"}, mail_cc=",".join(course_team_mails)).mail_send()
    send_release_request(course_id)
    return HttpResponse('{"status":"success"}')


def agu_url(request):
   authenticated = False
   if request.user.is_authenticated():
        authenticated = True
   context = {'logged_in': authenticated}
   return render_to_response("agu_url.html", context)


@login_required
@authorized_users({"RELEASE_ADMINS"}, all_superusers=True, all_staff=False)
def start_course(request):

    user = request.user
    course_id = request.GET.get('course_id').replace(" ","+")
    studio_url = get_all_env_tokens()["CMS_BASE"]
    url = "https://" + studio_url + "/update_about_attribute?course_id=" + urllib.quote(course_id) + "&attr_name=release_date&attr_val=now&user=" + str(user.username)
    req = urllib2.Request(url)
    resp = urllib2.urlopen(req)
    resp_text = str(resp.read())
    url_re = "https://" + studio_url + "/course/" + course_id + "/search_reindex"
    req_re = urllib2.Request(url_re)
    resp_re = urllib2.urlopen(req_re)
    resp_text_re = str(resp_re.read())
    overview = CourseOverview.objects.get(id = CourseKey.from_string(course_id))
    course_name = overview.display_name
    email = user.email
    course_team = _get_course_team(course_id)
    course_team_mails = list()
    course_admin_mails = course_team.get("admins")
    course_staff_mails = course_team.get("staff")
    if course_admin_mails is not None:
        course_team_mails += course_admin_mails
    if course_staff_mails is not None:
        course_team_mails += course_staff_mails
    #Mailer(5, email, {"course_name":course_name}, {"course_name":course_name, "sender": "applied_ops@amat.com"}, mail_cc=",".join(course_team_mails)).mail_send()
    return HttpResponse('{"status":"success"}')
