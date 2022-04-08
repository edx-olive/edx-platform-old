"""
Middleware for user api.
Adds user's tags to tracking event context.
"""

from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from eventtracking import tracker
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.track.contexts import COURSE_REGEX
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .models import UserCourseTag


def redirect_to_maintenance(absolute_url, path, user):
    """Redirect users who not enrolled in a course to a maintenance page."""
    from urllib.parse import quote
    from django.shortcuts import redirect

    if path == '/maintenancepage' or path == '/login' or path.startswith(('/user_api/', '/api/', '/notifier_api/', '/oauth2/access_token')):
        return None

    if not user.is_authenticated:
        return redirect("/login" + "?next={url}".format(url=quote(absolute_url, safe='')))
    else:
        if user.is_superuser:
            return None
    return redirect('/maintenancepage')


class UserTagsEventContextMiddleware(MiddlewareMixin):
    """Middleware that adds a user's tags to tracking event context."""
    CONTEXT_NAME = 'user_tags_context'

    def process_request(self, request):
        """
        Add a user's tags to the tracking event context.
        """
        match = COURSE_REGEX.match(request.build_absolute_uri())
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

            if request.user.is_authenticated:
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

        if configuration_helpers.get_value(
            'CAMPUS_RESTRICT_COURSE_ACCESS',
            settings.FEATURES.get("CAMPUS_RESTRICT_COURSE_ACCESS")
        ):
            return redirect_to_maintenance(request.build_absolute_uri(), request.path, request.user)

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """Exit the context if it exists."""
        try:
            tracker.get_tracker().exit_context(self.CONTEXT_NAME)
        except:  # pylint: disable=bare-except
            pass

        return response
