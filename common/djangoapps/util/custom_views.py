"""
AMAT customizations.
"""
from collections import defaultdict
import datetime
import json
import logging
import os
import re
import socket
import string
import tempfile
import time

import boto
from boto.exception import NoAuthHandlerFound
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails
from path import Path as path
import pytz
from rest_framework import status
from search.api import course_discovery_search
from xmodule.modulestore.django import modulestore

import branding
from courseware.models import StudentModule
from cms.djangoapps.models.settings.course_metadata import CourseMetadata
from student.roles import CourseInstructorRole, CourseStaffRole


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def sign_cloudfront_url(request):
    """
    Sign Cloudfront URL.

    Used to upload videos (`vr_xblock`, default video).
    """
    url = request.GET['url']
    url = url.replace(" ", "+")
    SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
    CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', "/edx/app/edxapp/"))
    CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""
    with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
        ENV_TOKENS = json.load(env_file)
    aws_access_key_id = ENV_TOKENS.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = ENV_TOKENS.get("AWS_SECRET_ACCESS_KEY")
    s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    try:
        # TODO: DRY (in this module)
        cf = boto.connect_cloudfront(aws_access_key_id, aws_secret_access_key)
        key_pair_id = ENV_TOKENS.get("SIGNING_KEY_ID")
        priv_key_file = ENV_TOKENS.get("SIGNING_KEY_FILE")
        expires = int(time.time()) + 600
        http_resource = url
        dist = cf.get_all_distributions()[0].get_distribution()
        http_signed_url = dist.create_signed_url(http_resource, key_pair_id, expires, private_key_file=priv_key_file)
        return HttpResponse(http_signed_url)
    except NoAuthHandlerFound:
        return HttpResponse(
            json.dumps({
                "status": "error",
                "message": "Failed to sign CloudFront url."}),
            status=status.HTTP_401_UNAUTHORIZED
        )


def s3_video_list(request):
    """
    Return a list of videos for a course.
    """
    # TODO try except
    foldername = request.GET['course_folder']
    s3 = boto.connect_s3(settings.AWS_VIDEO_ACCESS_KEY, settings.AWS_VIDEO_SECRET_ACCESS_KEY)
    try:
        bucket = s3.get_bucket(settings.AWS_VIDEO_BUCKET)
    except TypeError:
        return HttpResponse(
            json.dumps({
                "status": "error",
                "message": "AWS bucket not found."}),
            status=status.HTTP_404_NOT_FOUND
        )
    files = bucket.list(foldername)
    filenames = []
    for key in files:
        filenames.append(key.name)
    video_list = json.dumps(filenames)
    return HttpResponse(video_list)


def upload_to_s3(source, bucketname, target): # TODO remove it, seems like it is never used
    """
    Upload a video to AWS S3.
    """
    try:
        ENV_TOKENS = get_all_env_tokens()
        aws_access_key_id = ENV_TOKENS.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = ENV_TOKENS.get("AWS_SECRET_ACCESS_KEY")
        s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
        cf = boto.connect_cloudfront(aws_access_key_id, aws_secret_access_key)
        bucket = s3.get_bucket(bucketname)
        key = bucket.new_key(target)
        key.set_contents_from_filename(source)
    except Exception, e:
        return False
    return True


def video_upload(request):
    """
    Upload a video to AWS S3.
    """
    cloudFrontURL = settings.FEATURES.get('CLOUDFRONT_URL')
    try:
        filename = request.FILES['file'].name
        with open('/tmp/' + filename, 'wb+') as destination:
            for chunk in request.FILES['file'].chunks():
                destination.write(chunk)
            course_directory = request.POST['course_directory']
            metadata = get_video_metadata('/tmp/' + filename)
        # bitrate_in_kbps = to_kilo_bits_per_second(metadata['bitrate'])
        #  if bitrate_in_kbps > 2048:
        #      return HttpResponse('{"status":"error",
        #      "message":"Video can not be uploaded due to unacceptable bitrate.
        #      If you are not sure how to fix it, please contact operations at appliedx_ops@amat.com"}')
        s3 = boto.connect_s3(settings.AWS_VIDEO_ACCESS_KEY, settings.AWS_VIDEO_SECRET_ACCESS_KEY)
        bucket = s3.get_bucket(settings.AWS_VIDEO_BUCKET)
        object_name = course_directory + "/" + string.replace(filename, " ", "_")
        key = bucket.new_key(object_name)
        key.set_contents_from_filename('/tmp/' + filename)
        cloudFrontURL += object_name
    except Exception, e:
        return HttpResponse(e)
    message = "Video has been uploaded succesfully."
    #  if bitrate_in_kbps > 1536:
    #      message += "Please note that bitrate is slightly higher than recommended."
    # TODO use json dumps here
    response = '{"status": "success", "message":"' + \
               message + '", "cloudfront_url":"' + \
               cloudFrontURL + '", "metadata":' + \
               json.dumps(metadata) + '}'
    return HttpResponse(response)


def get_video_metadata(filepath):
    """
    Convert a video and prepare its metadata.

    Arguments:
        filepath (str): video filename.

    Returns:
          metadata (dict): video characteristics.
    """
    tmpf = tempfile.NamedTemporaryFile()
    os.system("avconv -i \"%s\" 2> %s" % (filepath, tmpf.name))
    lines = tmpf.readlines()
    tmpf.close()
    metadata = {}
    if lines:
        for l in lines:
            l = l.strip()
            if l.startswith('Duration'):
                metadata['duration'] = re.search('Duration: (.*?),', l).group(0).split(':', 1)[1].strip(' ,')
                metadata['bitrate'] = re.search('bitrate: (\d+ kb/s)', l).group(0).split(':')[1].strip()
            if l.startswith('Stream #0') and re.search('Video: (.*? \(.*?\)),? ', l) is not None:
                metadata['video'] = {}
                metadata['video']['codec'], metadata['video']['profile'] = \
                    [e.strip(' ,()') for e in re.search('Video: (.*? \(.*?\)),? ', l).group(0).split(':')[1].split('(')]
                metadata['video']['resolution'] = re.search('([1-9]\d+x\d+)', l).group(1)
                metadata['video']['bitrate'] = re.search('(\d+ kb/s)', l).group(1)
                metadata['video']['fps'] = re.search('(\d+ fps)', l).group(1)
            if l.startswith('Stream #0') and re.search('Video: (.*? \(.*?\)),? ',l) is None:
                metadata['audio'] = {}
                metadata['audio']['codec'] = re.search('Audio: (.*?) ', l).group(1)
                metadata['audio']['frequency'] = re.search(', (.*? Hz),', l).group(1)
                metadata['audio']['bitrate'] = re.search(', (\d+ kb/s)', l).group(1)
    return metadata


def get_all_env_tokens():
    try:
        SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
        CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', "/edx/app/edxapp/"))
        CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""
        with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
            ENV_TOKENS = json.load(env_file)
    except Exception, e:
        return HttpResponse(e)
    return ENV_TOKENS


def to_kilo_bits_per_second(raw):
    split = raw.split(" ")
    value = int(split[0])
    denomination = split[1].split("/s")[0]
    if denomination[0] == "k":
        value *= 1
    if denomination[0] == "m":
        value *= 1000
    if denomination[0] == "g":
        value *= 1000000
    if denomination[0] == "t":
        value *= 1000000000
    if denomination[1] == "B":
        value *= 8
    return value


def yammer_group_id(request):
    course_id = request.GET.get('course_id').replace(" ", "+")
    ygid = CourseDetails.fetch_about_attribute(CourseKey.from_string(course_id), 'yammer')
    if ygid is None:
        ygid = "0"
    return HttpResponse('{"ygid": "' + ygid + '"}')


def feedback_for_all_courses(request, course_id):
    """
    Get feedback for a course.

    :args course_id
    :returns feedback survey for course
    eg. https://appliedxvpcdev.amat.com/feedback_for_all_courses/course-v1:T1+TF101+2018_T1/
    """
    try:
        course_key = CourseKey.from_string(course_id)
        CourseStudentAllModules = StudentModule.objects.filter(course_id=course_key)
        feedback_dict = defaultdict(list)
        if CourseStudentAllModules.count() != 0:
            data = CourseStudentAllModules.filter(module_type='feedback')
            if data.count() != 0:
                for feedback in data:
                    state = json.loads(str(feedback.state))
                    if 'answer' in state.keys():
                        module_state_key = feedback.module_state_key.block_id
                        student_id = User.objects.get(id=feedback.student_id).email
                        course_id = course_id
                        feedback_dict[course_id].append(
                            {
                                'student_email': student_id,
                                'answer': state.get('answer'),
                                'module_state_key': module_state_key
                            }
                        )
        return JsonResponse({'resp': feedback_dict})
    except Exception as e:
        logger.error('Unable to get feedback for all courses ' + str(e))
        return JsonResponse({'resp': ''})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def allow_only_native_calls(_function):
    def block_external_request_source(request, *args, **kwargs):
        if get_client_ip(request) != socket.gethostbyname(socket.gethostname()):
            return HttpResponse('{"status":"error", "message":"forbidden"}')
        else:
             return _function(request, *args, **kwargs)
    return block_external_request_source


@allow_only_native_calls
def update_course_metadata(request):
    course_id = request.GET.get("course_id").replace(" ","+")
    attribute_name = request.GET.get("attr_name")
    attribute_value = request.GET.get("attr_val")
    lms_username = request.GET.get("user")
    course_module = modulestore().get_course(CourseKey.from_string(course_id), depth=1)
    metadata = CourseMetadata.fetch(course_module)
    attribute_to_update = metadata[attribute_name]
    attribute_to_update["value"] = attribute_value
    metadata = CourseMetadata.update_from_json(course_module,
                                               {attribute_name: attribute_to_update},
                                               User.objects.get(username=lms_username))
    return HttpResponse('{"' + attribute_name + '" : "' + str(metadata[attribute_name]) + '"}')


@allow_only_native_calls
def update_about_attribute(request):
    course_id = request.GET.get("course_id").replace(" ", "+")
    attribute_name = request.GET.get("attr_name")
    attribute_value = request.GET.get("attr_val")
    lms_username = request.GET.get("user")
    course_key = CourseKey.from_string(course_id)
    if attribute_name == "release_date":
        json_dict = {}  # TODO test
        if attribute_value == "now":
            now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
            json_dict = {
                "start_date": now,
                "enrollment_start": now,
                "intro_video": CourseDetails.fetch_about_attribute(CourseKey.from_string(course_id), 'video')
            }
    else:
        json_dict = {
            attribute_name: attribute_value,
            "intro_video": CourseDetails.fetch_about_attribute(CourseKey.from_string(course_id), 'video')
        }
    CourseDetails.update_from_json(course_key, json_dict, User.objects.get(username=lms_username))
    attribute_value = getattr(CourseDetails.fetch(CourseKey.from_string(course_id)), attribute_name, "error")
    return HttpResponse('{"' + attribute_name + '" : "' + str(attribute_value) + '"}')


def _search(search_key, page_size, page_index, mobile, field_dict):
    if page_size == "" or page_size is None:
        page_size = 20
    if page_index == "" or page_index is None:
        page_index = 1
    start = (int(page_index) - 1) * int(page_size)
    if mobile is not None and mobile != "false":
        data = course_discovery_search(search_term=search_key, size=page_size, from_=start, field_dictionary=field_dict)
        results = data['results']
        print(len(results))
        store = modulestore()
        newResult = list()
        for result in results:
            course_key = CourseKey.from_string(result['_id'])
            print(course_key)
            course = store.get_course(course_key)
            try:
                field = course.fields['mobile_available']
                value = field.read_json(course)
                print(value)
                if value:
                    newResult.append(result)
            except:
                pass
        data['results'] = newResult
        data['total'] = len(newResult)
        return data
    return course_discovery_search(search_term=search_key, size=page_size, from_=start, field_dictionary=field_dict)


def _get_course_team(course_key_string):
    if course_key_string is None:
        return {"staff": [], "admins": []}
    course_key = CourseKey.from_string(course_key_string)
    course_module = modulestore().get_course(course_key)
    instructors = set(CourseInstructorRole(course_key).users_with_role())
    staff = set(set(CourseStaffRole(course_key).users_with_role()) - instructors)
    emails = {"staff": [], "admins": []}
    for member in staff:
        emails["staff"].append(member.email)
    for member in instructors:
        emails["admins"].append(member.email)
    return emails


def _get_course_ids():
    courses = branding.get_visible_courses()
    course_ids = []
    for course in courses:
        course_ids.append(str(course.id))
    return course_ids


def _get_audience_list(all_superusers = False,
                       all_staff = False,
                       all_course_admins = False,
                       all_course_staff = False,
                       group_list = [],
                       course_id = "",
                       all_courses = False):
    audience = dict({"groups":dict(), "courses":dict()})
    group_audience = audience.get("groups")
    for group_name in group_list:
        group = Group.objects.get(name=group_name)
        group_mails = []
        for user in group.user_set.all():
            group_mails.append(user.email)
    group_audience[group_name] = group_mails
    if all_superusers:
        superusers = User.objects.filter(is_superuser = True).values_list('email', flat=True)
        audience["superusers"] = list(superusers)
    if all_staff:
        staff = User.objects.filter(is_staff= True).values_list('email', flat=True)
        audience["staff"] = list(staff)
    course_id_list = list()
    if course_id != "":
        course_id_list.append(course_id)
    if all_courses:
        course_id_list = _get_course_ids()
    if course_id_list == 0:
        return audience
    course_staff = {}
    course_audience = audience.get("courses")
    for course_id in course_id_list:
        if all_course_staff or all_course_admins:
            this_course_staff = _get_course_team(course_id)
            course_audience[course_id] = dict()
        if all_course_staff:
            course_audience[course_id]["staff"] = this_course_staff.get("staff")
        if all_course_admins:
            course_audience[course_id]["admins"] = this_course_staff.get("admins")
    return audience


def _get_user_role_in_course(course_id, email):
    team = _get_course_team(course_id)
    if email in team["staff"]:
        return {"role": "staff"}
    if email in team["admins"]:
        return {"role": "admins"}
    return {"role": "none"}


def search(request):
    """Custom courses search endpoint."""
    search_key = request.GET.get('search_string')
    page_size = request.GET.get('page_size')
    page_index = request.GET.get('page_index')
    mobile = request.GET.get('mobile')
    field_dict = dict()
    for parameter in request.GET:
        if parameter not in ('search_string', 'page_size', 'page_index', 'mobile' ):
            field_dict.update(dict({parameter: request.GET[parameter]}))

    return HttpResponse(json.dumps(_search(search_key, page_size, page_index, mobile, field_dict)))