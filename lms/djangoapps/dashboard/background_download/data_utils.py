"""Data preparation for file storage."""

from collections import defaultdict
import logging

from django.conf import settings

from courseware.models import StudentModule
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from poll_survey.configs import (
    ALLOWED_POLLS_NAMES,
    POLLS_SUBMISSIONS_MAPPING,
)


log = logging.getLogger('edx.celery.task')


def _get_closest_to_dt(qs, dt):
    """
    Filter given queryset by the givet DateTime.

    Returns value closest to given datetime.

    Args:
        qs (Queryset): Queryset to filter
        dt (DateTime): DateTime for what to find closest record in the qs (should be offset-aware)

    Returns:
        [type]: [description]
    """
    greater = qs.filter(created__gte=dt).order_by("created").first()
    less = qs.filter(created__lte=dt).order_by("-created").first()
    if greater and less:
        return greater if abs(greater.created - dt) < abs(less.created - dt) else less
    else:
        return greater or less


def get_block_info(submission):
    """
    Get poll/survey parents and studio unit link.

    Args:
        submission (`poll_survey.models.PollSubmission` |
            `poll_survey.models.SurveySubmission` |
            `poll_survey.models.OpenEndedSubmission` obj): poll/submission obj

    Returns:
        dict: dict with parent names and studio link to unit containing poll/survey
    """
    qs = StudentModule.objects.filter(
      course_id=submission.course,
      student=submission.student,
    )
    # In most cases closest will be the `greter` one with differense between records ~ 1 sec.
    closest = _get_closest_to_dt(qs, submission.submission_date)
    if not closest:
        return defaultdict(lambda: 'n/a')
    usage_loc = closest.module_state_key
    item = modulestore().get_item(usage_loc)
    unit = item.get_parent()
    unit_url = '{studio_base}/container/{block_key}'.format(
        studio_base=settings.CMS_BASE,
        block_key=str(unit.location)
    )
    subsection = unit.get_parent()
    section = subsection.get_parent()
    return {
        'section_name': section.display_name,
        'subsection_name': subsection.display_name,
        'unit_name': unit.display_name,
        'page_link': unit_url
    }


def prepare_submission_datum(submission, **kwargs):
    """
    Wrap up submission datum for reports.

    Arguments:
        poll_type (str): poll type.
        submission (`poll_survey.models.PollSubmission` |
            `poll_survey.models.SurveySubmission` |
            `poll_survey.models.OpenEndedSubmission` obj)
    Returns:
        data (list | None): data expected for reports.

    """
    poll_type = kwargs.get("poll_type")
    validate_poll_type(poll_type)
    try:
        answer_id = submission.answer.id if getattr(submission, "answer", None) else "-"
        # For "open_ended_survey", there'll be `submission.answer_text`
        # instead of submission's answer.id and answer.text
        answer_text = submission.answer.text if getattr(submission, "answer", None) else submission.answer_text
        try:
            submission_date = submission.submission_date.strftime("%m/%d/%Y")  # MM/DD/YYYY e.g. "11/07/2019"
        except:  # Cannot think of any particular error
            submission_date = "-"

        block_info = get_block_info(submission)

        return [
            poll_type,
            submission.course,
            block_info['section_name'],
            block_info['subsection_name'],
            block_info['unit_name'],
            block_info['page_link'],
            submission.student.email,
            submission.student.id,
            submission.employee_id or "-",
            submission.question.id,
            submission.question.text.encode("utf8"),
            answer_id,
            answer_text.encode("utf8"),
            submission_date,
        ]
    except AttributeError:
        return [poll_type, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]


def validate_poll_type(poll_type):
    if poll_type not in ALLOWED_POLLS_NAMES:
        raise ValueError("Provide a correct 'poll_type'.")


def prepare_course_ids(courses_ids):
    validated_courses_ids = []
    for cid in courses_ids:
        valid_cid = cid if isinstance(cid, CourseKey) else CourseKey.from_string(cid.strip())
        validated_courses_ids.append(valid_cid)
    return tuple(validated_courses_ids)


def define_subs_class(poll_type):
    if poll_type not in ALLOWED_POLLS_NAMES:
        raise ValueError("Please provide a valid poll_type.")
    subs_class = POLLS_SUBMISSIONS_MAPPING.get(poll_type)
    if not subs_class:
        raise ValueError("Update `POLLS_SUBMISSIONS_MAPPING` and/or 'ALLOWED_POLLS_NAMES'.")
    return subs_class


def define_subs_size(courses_ids, subs_model_class):
    if courses_ids:
        subs_size = subs_model_class.objects.filter(course__in=courses_ids).count()
    else:
        subs_size = subs_model_class.objects.all().count()
    return subs_size


def fetch_submissions(courses_ids, subs_model_class, offset, chunk_size):
    if courses_ids:
        submissions = subs_model_class.objects.filter(course__in=courses_ids)[offset:chunk_size + offset]
    else:
        submissions = subs_model_class.objects.filter()[offset:chunk_size + offset]
    return submissions
