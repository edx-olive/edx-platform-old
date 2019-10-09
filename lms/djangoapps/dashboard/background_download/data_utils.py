"""Data preparation for file storage."""

import logging

from opaque_keys.edx.keys import CourseKey

from poll_survey.configs import (
    ALLOWED_POLLS_NAMES,
    POLLS_SUBMISSIONS_MAPPING,
)


log = logging.getLogger('edx.celery.task')


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
        return [
            poll_type,
            submission.course,
            submission.student.id,
            submission.question.id,
            submission.question.text,
            answer_id,
            answer_text
        ]
    except AttributeError:
        return [poll_type, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"]


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
