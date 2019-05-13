"""
AMAT customizations.
"""
import json
import logging
import os
import re
import string
import tempfile
import time

import boto
from boto.exception import NoAuthHandlerFound
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails

from collections import defaultdict
from courseware.models import StudentModule
from edxmako.shortcuts import render_to_response
from path import Path as path
from rest_framework import status


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
    # TODO DRY (in this module)
    SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
    CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', "/edx/app/edxapp/"))
    CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""
    with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
        ENV_TOKENS = json.load(env_file)
    aws_access_key_id = ENV_TOKENS.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = ENV_TOKENS.get("AWS_SECRET_ACCESS_KEY")
    aws_video_bucket_name = ENV_TOKENS.get("AWS_BUCKET_NAME")
    s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    try:
        bucket = s3.get_bucket(aws_video_bucket_name)
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


def upload_to_s3(source, bucketname, target):
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
        ENV_TOKENS = get_all_env_tokens()
        #  if bitrate_in_kbps > 2048:
        #      return HttpResponse('{"status":"error",
        #      "message":"Video can not be uploaded due to unacceptable bitrate.
        #      If you are not sure how to fix it, please contact operations at appliedx_ops@amat.com"}')
        aws_access_key_id = ENV_TOKENS.get("AWS_ACCESS_KEY_ID")
        aws_secret_access_key = ENV_TOKENS.get("AWS_SECRET_ACCESS_KEY")
        s3 = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
        cf = boto.connect_cloudfront(aws_access_key_id, aws_secret_access_key)
        bucket_name = ENV_TOKENS.get("AWS_BUCKET_NAME")
        bucket = s3.get_bucket(bucket_name)
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
