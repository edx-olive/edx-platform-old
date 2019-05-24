"""
AMAT customizations.
"""
import datetime
import json
import logging
import urllib
import urllib2

import pytz
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from courseware.models import StudentModule
from lms.djangoapps.grades.constants import ScoreDatabaseTableEnum
from lms.djangoapps.grades.signals.handlers import disconnect_submissions_signal_receiver
from lms.djangoapps.grades.signals.signals import PROBLEM_RAW_SCORE_CHANGED
from lms.djangoapps.instructor.enrollment import _reset_module_attempts
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from submissions.models import score_set
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from edxmako.shortcuts import render_to_response
from student.models import UserProfile, anonymous_id_for_user, CourseEnrollment
from eventtracking import tracker
from track.event_transaction_utils import create_new_event_transaction_id, set_event_transaction_type, \
    get_event_transaction_id
from submissions import api as sub_api
from util.custom_views import get_all_env_tokens, _get_course_team

log = logging.getLogger(__name__)


def is_honor_code_accepted(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    if user_profile.meta:
        meta = json.loads(user_profile.meta)
        if meta.get("honor_code_accepted_on"):
            return True
    return False


@login_required
def honorcode(request):
    """
    View to prompt a user to accept honor code.
    """
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


def _fire_score_changed_for_block(
        course_id,
        student,
        block,
        module_state_key,
):
    """
    Fires a PROBLEM_RAW_SCORE_CHANGED event for the given module.
    The earned points are always zero. We must retrieve the possible points
    from the XModule, as noted below. The effective time is now().
    """
    if block and block.has_score:
        max_score = block.max_score()
        if max_score is not None:
            PROBLEM_RAW_SCORE_CHANGED.send(
                sender=None,
                raw_earned=0,
                raw_possible=max_score,
                weight=getattr(block, 'weight', None),
                user_id=student.id,
                course_id=unicode(course_id),
                usage_id=unicode(module_state_key),
                score_deleted=True,
                only_if_higher=False,
                modified=datetime.datetime.now().replace(tzinfo=pytz.UTC),
                score_db_table=ScoreDatabaseTableEnum.courseware_student_module,
            )


def reset_student_attempts(course_id, student, module_state_key, requesting_user, delete_module=False):
    user_id = anonymous_id_for_user(student, course_id)
    requesting_user = User.objects.get(username="staff")
    requesting_user_id = anonymous_id_for_user(requesting_user, course_id)
    submission_cleared = False
    try:
        # A block may have children. Clear state on children first.
        block = modulestore().get_item(module_state_key)
        if block.has_children:
            for child in block.children:
                try:
                    reset_student_attempts(course_id, student, child, requesting_user, delete_module=delete_module)
                except StudentModule.DoesNotExist:
                    # If a particular child doesn't have any state, no big deal, as long as the parent does.
                    pass
        if delete_module:
            # Some blocks (openassessment) use StudentModule data as a key for internal submission data.
            # Inform these blocks of the reset and allow them to handle their data.
            clear_student_state = getattr(block, "clear_student_state", None)
            if callable(clear_student_state):
                with disconnect_submissions_signal_receiver(score_set):
                    clear_student_state(
                        user_id=user_id,
                        course_id=unicode(course_id),
                        item_id=unicode(module_state_key),
                        requesting_user_id=requesting_user_id
                    )
                submission_cleared = True
    except ItemNotFoundError:
        block = None
        log.warning("Could not find %s in modulestore when attempting to reset attempts.", module_state_key)
    if delete_module and not submission_cleared:
        sub_api.reset_score(
            user_id,
            course_id.to_deprecated_string(),
            module_state_key.to_deprecated_string(),
        )

    module_to_reset = StudentModule.objects.get(
        student_id=student.id,
        course_id=course_id,
        module_state_key=module_state_key
    )
    if delete_module:
        module_to_reset.delete()
        create_new_event_transaction_id()
        grade_update_root_type = 'edx.grades.problem.state_deleted'
        set_event_transaction_type(grade_update_root_type)
        tracker.emit(
            unicode(grade_update_root_type),
            {
                'user_id': unicode(student.id),
                'course_id': unicode(course_id),
                'problem_id': unicode(module_state_key),
                'instructor_id': unicode(requesting_user.id),
                'event_transaction_id': unicode(get_event_transaction_id()),
                'event_transaction_type': unicode(grade_update_root_type),
            }
        )
        if not submission_cleared:
            _fire_score_changed_for_block(
                course_id,
                student,
                block,
                module_state_key,
            )
    else:
        _reset_module_attempts(module_to_reset)


def service_reset_course(request):
    user_id = request.GET.get('user_id')
    user = User.objects.get(id=user_id)
    course_id = request.GET.get('course_id').replace(" ", "+")
    course_key = CourseKey.from_string(course_id)
    if not CourseEnrollment.is_enrolled(user, course_key):
        return HttpResponseBadRequest(_("You are not enrolled in this course"))
    for exam in StudentModule.objects.filter(student=user, course_id=course_id):
        log.error(exam.module_state_key)
        try:
            reset_student_attempts(course_id, user, exam.module_state_key, None, True)
        except:
            pass

    for exam in StudentModule.objects.filter(student=user, course_id=course_key):
        print(exam.state)
        try:
            state = json.loads(exam.state)
            resetcount = 0
            if state.get("resetcount"):
                resetcount = state["resetcount"]
            state["attempts"] = 0
            exam.state = '{"resetcount":' + str(resetcount + 1) + '}'  # json.dumps(state)
            exam.delete()
        #                exam.save()
        except:
            pass
    return JsonResponse({"Email": user.email, "User ID": user.id, "course_id": course_id})
