"""
Middleware for user api.
Adds user's tags to tracking event context.
"""

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from django.conf import settings
from eventtracking import tracker
from track.contexts import COURSE_REGEX

from .models import UserCourseTag


def redirect_to_maintenance(absolute_url, path, user, course_id, course_key):
    """Redirect users who not enrolled in a course to a maintenance page."""
    from urllib import quote
    from django.shortcuts import redirect
    from django.core.urlresolvers import reverse
    from student.models import (
        CourseEnrollment,
    )
    list_of_courses = ['course-v1:TAU+ACD_TAU_psychology101x+2019_1', 'course-v1:TAU+ACD_TAU_misraelx+1_2020',
                       'course-v1:MSE+GOV_PsychometryHe+2018_1', 'course-v1:TAU+ACD_TAU_beat_viruses+2019_2',
                       'course-v1:TAU+ACD_TAU_chemistry101x+2019_3']

    if path == reverse('maintenancepage') or path == '/login' or path == '/heartbeat' or path.startswith(('/user_api/', '/api/', '/notifier_api/', '/oauth2/access_token')):
        return None

    if not user.is_authenticated():
        if course_key and course_id in list_of_courses:
            return redirect("/login" + "?next={url}".format(url=quote(absolute_url, safe='')))
        return redirect(reverse('maintenancepage'))
    else:
        if user.is_superuser:
            return None

        if course_key and course_id in list_of_courses:
            try:
                enrollment = CourseEnrollment.objects.get(user=user.id, course_id=course_key)
                if enrollment.is_active:
                    return None
            except CourseEnrollment.DoesNotExist:
                return redirect(reverse('maintenancepage'))
        else:
            list_of_course_keys = [CourseKey.from_string(id) for id in list_of_courses]
            enrollments = CourseEnrollment.objects.filter(
                user=user.id, is_active=True, course_id__in=list_of_course_keys).values_list("course_id", flat=True)
            if enrollments.count() > 0:
                return None

    return redirect(reverse('maintenancepage'))


class UserTagsEventContextMiddleware(object):
    """Middleware that adds a user's tags to tracking event context."""
    CONTEXT_NAME = 'user_tags_context'

    def process_request(self, request):
        """
        Add a user's tags to the tracking event context.
        """
        from urllib import unquote
        match = COURSE_REGEX.match(unquote(request.build_absolute_uri()))
        course_id = None
        if match:
            course_id = match.group('course_id')
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                course_id = None
                course_key = None

        context = {}

        if course_id:
            context['course_id'] = course_id

            if request.user.is_authenticated():
                context['course_user_tags'] = dict(
                    UserCourseTag.objects.filter(
                        user=request.user.pk,
                        course_id=course_key,
                    ).values_list('key', 'value')
                )
            else:
                context['course_user_tags'] = {}

        tracker.get_tracker().enter_context(
            self.CONTEXT_NAME,
            context
        )
        if settings.FEATURES.get("CAMPUS_RESTRICT_COURSE_ACCESS"):
            if not course_id:
                course_key = None
            return redirect_to_maintenance(request.build_absolute_uri(), request.path, request.user, course_id, course_key)

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """Exit the context if it exists."""
        try:
            tracker.get_tracker().exit_context(self.CONTEXT_NAME)
        except:  # pylint: disable=bare-except
            pass

        return response
