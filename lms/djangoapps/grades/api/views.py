""" API v0 views. """
import json
import logging

from django.contrib.auth import get_user_model
from django.http import Http404, JsonResponse
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.response import Response

from courseware.access import has_access
from courseware.models import StudentModule

from lms.djangoapps.ccx.utils import prep_course_for_grading
from lms.djangoapps.courseware import courses
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.grades.api.serializers import GradingPolicySerializer
from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
from openedx.core.lib.api.view_utils import DeveloperErrorViewMixin, view_auth_classes
from student.roles import CourseStaffRole

log = logging.getLogger(__name__)
USER_MODEL = get_user_model()


@view_auth_classes()
class GradeViewMixin(DeveloperErrorViewMixin):
    """
    Mixin class for Grades related views.
    """
    def _get_course(self, course_key_string, user, access_action):
        """
        Returns the course for the given course_key_string after
        verifying the requested access to the course by the given user.
        """
        try:
            course_key = CourseKey.from_string(course_key_string)
        except InvalidKeyError:
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The provided course key cannot be parsed.',
                error_code='invalid_course_key'
            )

        try:
            return courses.get_course_with_access(
                user,
                access_action,
                course_key,
                check_if_enrolled=True,
            )
        except Http404:
            log.info('Course with ID "%s" not found', course_key_string)
        except CourseAccessRedirect:
            log.info('User %s does not have access to course with ID "%s"', user.username, course_key_string)
        return self.make_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            developer_message='The user, the course or both do not exist.',
            error_code='user_or_course_does_not_exist',
        )

    def _get_effective_user(self, request, course):
        """
        Returns the user object corresponding to the request's 'username' parameter,
        or the current request.user if no 'username' was provided.

        Verifies that the request.user has access to the requested users's grades.
        Returns a 403 error response if access is denied, or a 404 error response if the user does not exist.
        """

        # Use the request user's if none provided.
        if 'username' in request.GET:
            username = request.GET.get('username')
        else:
            username = request.user.username

        if request.user.username == username:
            # Any user may request her own grades
            return request.user

        # Only a user with staff access may request grades for a user other than herself.
        if not has_access(request.user, CourseStaffRole.ROLE, course):
            log.info(
                'User %s tried to access the grade for user %s.',
                request.user.username,
                username
            )
            return self.make_error_response(
                status_code=status.HTTP_403_FORBIDDEN,
                developer_message='The user requested does not match the logged in user.',
                error_code='user_mismatch'
            )

        try:
            return USER_MODEL.objects.get(username=username)

        except USER_MODEL.DoesNotExist:
            return self.make_error_response(
                status_code=status.HTTP_404_NOT_FOUND,
                developer_message='The user matching the requested username does not exist.',
                error_code='user_does_not_exist'
            )

    def perform_authentication(self, request):
        """
        Ensures that the user is authenticated (e.g. not an AnonymousUser), unless DEBUG mode is enabled.
        """
        super(GradeViewMixin, self).perform_authentication(request)
        if request.user.is_anonymous():
            raise AuthenticationFailed


class UserGradeView(GradeViewMixin, GenericAPIView):
    """
    **Use Case**

        * Get the current course grades for a user in a course.

        The currently logged-in user may request her own grades, or a user with staff access to the course may request
        any enrolled user's grades.

    **Example Request**

        GET /api/grades/v0/course_grade/{course_id}/users/?username={username}

    **GET Parameters**

        A GET request may include the following parameters.

        * course_id: (required) A string representation of a Course ID.
        * username: (optional) A string representation of a user's username.
          Defaults to the currently logged-in user's username.

    **GET Response Values**

        If the request for information about the course grade
        is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response has the following values.

        * username: A string representation of a user's username passed in the request.

        * course_id: A string representation of a Course ID.

        * passed: Boolean representing whether the course has been
                  passed according the course's grading policy.

        * percent: A float representing the overall grade for the course

        * letter_grade: A letter grade as defined in grading_policy (e.g. 'A' 'B' 'C' for 6.002x) or None


    **Example GET Response**

        [{
            "username": "bob",
            "course_key": "edX/DemoX/Demo_Course",
            "passed": false,
            "percent": 0.03,
            "letter_grade": None,
        }]

    """
    def get(self, request, course_id):
        """
        Gets a course progress status.

        Args:
            request (Request): Django request object.
            course_id (string): URI element specifying the course location.

        Return:
            A JSON serialized representation of the requesting user's current grade status.
        """

        course = self._get_course(course_id, request.user, 'load')
        if isinstance(course, Response):
            # Returns a 404 if course_id is invalid, or request.user is not enrolled in the course
            return course

        grade_user = self._get_effective_user(request, course)
        if isinstance(grade_user, Response):
            # Returns a 403 if the request.user can't access grades for the requested user,
            # or a 404 if the requested user does not exist.
            return grade_user

        prep_course_for_grading(course, request)
        course_grade = CourseGradeFactory().create(grade_user, course)
        return Response([{
            'username': grade_user.username,
            'course_key': course_id,
            'passed': course_grade.passed,
            'percent': course_grade.percent,
            'letter_grade': course_grade.letter_grade,
        }])


class CourseGradingPolicy(GradeViewMixin, ListAPIView):
    """
    **Use Case**

        Get the course grading policy.

    **Example requests**:

        GET /api/grades/v0/policy/{course_id}/

    **Response Values**

        * assignment_type: The type of the assignment, as configured by course
          staff. For example, course staff might make the assignment types Homework,
          Quiz, and Exam.

        * count: The number of assignments of the type.

        * dropped: Number of assignments of the type that are dropped.

        * weight: The weight, or effect, of the assignment type on the learner's
          final grade.
    """

    allow_empty = False

    def get(self, request, course_id, **kwargs):
        course = self._get_course(course_id, request.user, 'staff')
        if isinstance(course, Response):
            return course
        return Response(GradingPolicySerializer(course.raw_grader, many=True).data)


def answered_count(user, course):
    problems = StudentModule.objects.filter(
        student=user,
        course_id=course.id,
        module_type="problem"
    ) | StudentModule.objects.filter(student=user, course_id=course.id, module_type="drag-and-drop-v2")
    if problems:
        answered = 0
        for s in problems:
            log.error(json.loads(s.state))
            if json.loads(s.state).get('correct_map'):
                answered += 1
            elif json.loads(s.state).get('item_state'):
                answered += 1
            elif json.loads(s.state).get('attempts'):
                answered += 1
        is_reset = json.loads(problems[0].state).get('resetcount')
        return answered, is_reset


def get_grades_api(request):
    course_id_raw = request.GET["course_id"]
    student = USER_MODEL.objects.get(id=int(request.GET["student_id"]))
    course_id_raw = course_id_raw.replace(' ', '+')
    course_id = CourseKey.from_string(course_id_raw)
    course = courses.get_course_by_id(course_id)
    course_grade = CourseGradeFactory().create(student, course)
    courseware_summary = course_grade.chapter_grades.values()
    answered = 0
    if StudentModule.objects.filter(student=student.id, course_id=course.id, module_type="problem"):
        answered, reset = answered_count(student.id, course)
    count = 0
    for sections in courseware_summary:
        for section in sections['sections']:
            for i in section.problem_scores:
                count = count + 1

    log.info(answered)
    log.info(count)
    return JsonResponse({
        'username': student.username,
        'passed': course_grade.passed,
        'percent': course_grade.percent,
        'letter_grade': course_grade.letter_grade,
        'courseware_summary': str(courseware_summary),
        'reset': answered == count
    })
