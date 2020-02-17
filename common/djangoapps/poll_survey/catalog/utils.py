"""
AMAT Catalog data-driven utils.
"""
import logging

from django.db.models import F, Q
from xmodule.modulestore.django import modulestore

from poll_survey.configs import POLLS_SUBMISSIONS_MAPPING, RATING_POLL_NAME
from poll_survey.catalog.constants import ALLOWED_POLL_RATINGS
from poll_survey.catalog.exceptions import (
    AmatCatalogInvalidCourseIdException,
    AmatCatalogInvalidRatingException,
    AmatCatalogNonExistingCourseException,
    AmatCatalogRatingNonExistingUserIdException,
    AmatCatalogRatingUnacceptableUserIdException,
)


celery_log = logging.getLogger('edx.celery.task')


def prepare_employee_user_id(user_id):
    """
    Prepare/validate user employee id.

    Required by Catalog Transfer-Rating API endpoint.

    Employee id is based on AGU/PingSSO (social auth) flow.
    """

    # Won't be checking user auth entry for employee id, it's expensive
    if not user_id:
        raise AmatCatalogRatingNonExistingUserIdException
    try:
        int(user_id)  # e.g. "X" in user_id
    except ValueError:
        raise AmatCatalogRatingUnacceptableUserIdException
    return user_id


def prepare_course_agu_id(course_id):
    """
    Transform course_id into the AGU format.

    Required by Catalog Transfer-Rating API endpoint.

    For courses WITH defined "Course Number Display String" advanced setting
    (display_number_with_default), the value of such setting will be
    pushed to the catalog.

    For courses WITHOUT defined "Course Number Display String" advanced setting,
    the next pattern holds:  <course_code>, e.g. "course-v1: RG+CS101+2019_T1"
    should become "CS101".

    Arguments:
        course_id (`opaque_keys.edx.keys.CourseKey`): course id.
    """

    course_module = get_modulestore_course(course_id)
    if course_module:
        course_number = course_module.display_coursenumber
        if course_number:
            return course_number
        elif course_id.course:
            return course_id.course
        else:
            # Quite improbable case, or so they say
            raise AmatCatalogInvalidCourseIdException
    else:
        raise AmatCatalogNonExistingCourseException


def get_modulestore_course(course_id):
    """
    Get a course module from modulestore by course id.

    Arguments:
        course_id (`opaque_keys.edx.keys.CourseKey`): course id.
    """

    return modulestore().get_course(course_id, depth=0)


def prepare_poll_rating(rating):
    """
    Prepare/validate a poll rating.
    """

    if str(rating) not in ALLOWED_POLL_RATINGS:
        raise AmatCatalogInvalidRatingException
    return rating


def validate_payload_nomenclature(data, expected_params):
    """
    Validate API payload nomenclature.

    Arguments:
        data (dict): actual data in a payload.
        expected_params (list): expected params nomenclature.
    """

    provided_params = data.keys()
    for param in provided_params:
        if param not in expected_params:
            raise ValueError("Provide only allowed payload parameters to make a call to the AMAT Catalog API.")
    for param in expected_params:
        if param not in provided_params:
            raise ValueError("Provide all required payload parameters to make a call to the AMAT Catalog API.")


def catalog_push_rating_poll_submission(submission_entry, catalog_api_client, stdout=False):
    """
    Push poll rating submission to the AMAT Catalog.

    Arguments:
        submission_entry (`poll_survey.models.RatingPollSubmission`): rating poll
            submission object.
        catalog_api_client (`poll_survey.catalog.client.AmatCatalogApiClient`):
            the Catalog API client instance.
        stdout (bool): instruction to print out execution results.
    """

    user_id = submission_entry.employee_id
    try:
        _ = prepare_employee_user_id(user_id)
        # We do not pre-fetch the rating at earlier stages, as it might not be needed
        # (e.g. if a user is a contractor having "X011111"-like employee id
        # which is not accepted by the Catalog).
        rating = submission_entry.answer.text
        _ = prepare_poll_rating(rating)
        data = {
            "user_id": user_id,
            "course_id": submission_entry.course,
            "course_agu_id": submission_entry.course_agu_id,
            "rating": rating,
        }
        # Exceptions related to the Catalog/Pathway API interactions are handled by the client.
        # A common exception from api call (post) is also returned by the client logic as a marker.
        marker = catalog_api_client.transfer_rating(
            data=data,
            validate=False,
        )
        message = "Submission was pushed to the Catalog; marker: {!s}".format(marker)
    # edX business logic related errors (data preps/validation) are handled here, by higher-level logic
    except (
        AmatCatalogRatingNonExistingUserIdException,
        AmatCatalogRatingUnacceptableUserIdException,
        AmatCatalogInvalidRatingException,
        AmatCatalogInvalidCourseIdException,
        AmatCatalogNonExistingCourseException,
    ) as e:
        marker = e.marker.code
        message = "Submission with id '{!s}' wasn't pushed to the Catalog; " \
                  " marker: {!s}".format(submission_entry.id, marker)

    if stdout:
        print(message)
    else:
        # For now, we fall in this case from a Celery task only.
        celery_log.debug(message)

    return marker


def prepare_polls_submissions_queryset(
        submissions_model,
        submission_date_to=None,
        from_pk=1,
        courses_ids=None,
        markers=None,
        handle_resubmissions=False):
    """
    Prepare poll submissions queryset.

    Arguments:
        submissions_model (`poll_survey.models.SubmissionBase` subclass):
            submissions model.
        submission_date_to (datetime.datetime): submission date for filtering
            (will fetch entries created before this date). Optional to handle
            resubmissions and required for newly-arrived submissions.
        from_pk (long): pk for filtering.
        courses_ids (list): list of course ids (`opaque_keys.edx.keys.CourseKey`).
        markers (list): list of marked submissions to fetch by a `catalog_marker`,
            with each marker being of either of `poll_survey.catalog.constants` enums type.
        handle_resubmissions (bool): if True, only resubmissions will be considered.
    """

    if markers:
        validate_catalog_markers(markers, submissions_model)

    # Ensure that a `submissions_model` contains 'catalog_marker' field
    # (if using models other than `RatingPollSubmission`)

    if handle_resubmissions:
        # Re-submission:
        # - marked;
        # - created <= last processed;
        # - submission date > created;
        # - submission date >= latest_catalog_processing_date.
        latest_catalog_processing_date = submissions_model.objects.filter().latest(
            field_name="catalog_processed_date"
        ).catalog_processed_date
        if courses_ids:
            queryset = submissions_model.objects.filter(
                Q(
                    pk__gte=from_pk,
                    course__in=courses_ids,
                    submission_date__gte=latest_catalog_processing_date,
                    created__lte=latest_catalog_processing_date,
                    catalog_marker__isnull=False,
                ) &
                Q(
                    submission_date__gt=F("created"),
                )
            )
        else:
            queryset = submissions_model.objects.filter(
                Q(
                    pk__gte=from_pk,
                    submission_date__gte=latest_catalog_processing_date,
                    created__lte=latest_catalog_processing_date,
                    catalog_marker__isnull=False,
                ) &
                Q(
                    submission_date__gt=F("created"),
                )
            )
        return queryset

    if not submission_date_to:
        raise ValueError("Provide 'submission_date_to' to handle new submissions entries.")

    if courses_ids and markers:
        queryset = submissions_model.objects.filter(
            pk__gte=from_pk,
            submission_date__lte=submission_date_to,
            course__in=courses_ids,
            catalog_marker__in=markers,
        )
    elif courses_ids and not markers:
        queryset = submissions_model.objects.filter(
            pk__gte=from_pk,
            submission_date__lte=submission_date_to,
            course__in=courses_ids,
            catalog_marker=None  # Show unmarked submissions only
        )
    elif not courses_ids and markers:
        queryset = submissions_model.objects.filter(
            pk__gte=from_pk,
            submission_date__lte=submission_date_to,
            catalog_marker__in=markers,
        )
    else:
        queryset = submissions_model.objects.filter(
            pk__gte=from_pk,
            submission_date__lte=submission_date_to,
            catalog_marker=None,  # Show unmarked submissions only
        )
    return queryset


def fetch_polls_submissions_entries(
        submission_date_to=None,
        poll_type=RATING_POLL_NAME,
        from_pk=1,
        courses_ids=None,
        markers=None,
        offset=0,
        chunk_size=2000,
        handle_resubmissions=False):
    """
    Fetch submissions entries of a poll/survey of particular type.
    """

    print("Fetching '{!s}' poll_survey submissions starting from pk {!s}..."
          .format(poll_type, from_pk))

    submissions_model = define_polls_submissions_model(poll_type)

    return prepare_polls_submissions_queryset(
        submissions_model=submissions_model,
        submission_date_to=submission_date_to,
        courses_ids=courses_ids,
        markers=markers,
        handle_resubmissions=handle_resubmissions,
    )[offset:chunk_size+offset]


def define_polls_submissions_model(poll_type):
    """
    Define `poll_survey` submissions model.
    """

    submissions_model = POLLS_SUBMISSIONS_MAPPING.get(poll_type)
    if not submissions_model:
        raise ValueError("Please provide a valid poll type.")
    return submissions_model


def validate_catalog_markers(markers, submissions_model):
    """
    Validate catalog markers.

    NOTE: consider placing this logic in the `submissions_model`.

    Returns:
        markers (list): list of `poll_survey.catalog.constants` enums markers.
    """

    try:
        for m in markers:
            if m not in submissions_model.CATALOG_MARKER_CHOICES:
                raise ValueError(
                    "Provide a valid marker. "
                    "Refer to 'poll_survey.catalog.constants' enums values (value[0]). "
                )
    except AttributeError:
        raise ValueError(
            "Provide a valid 'submissions_model' or update your model "
            "for it to contain a 'catalog_marker' field. "
        )
