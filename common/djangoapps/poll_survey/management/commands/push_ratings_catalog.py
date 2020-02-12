"""
Push historical poll ratings to the AMAT Catalog (Pathway).
"""

from datetime import datetime
from optparse import make_option

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from poll_survey.catalog.client import AmatCatalogApiClient
from poll_survey.catalog.utils import catalog_push_rating_poll_submission
from poll_survey.configs import RATING_POLL_NAME
from poll_survey.management.commands.utils.commands_utils import get_comma_separated_args
from poll_survey.catalog.utils import (
    fetch_polls_submissions_entries,
    prepare_polls_submissions_queryset,
)
from poll_survey.models import RatingPollSubmission


class Command(BaseCommand):
    """
    Command to push historical ratings to the AMAT Catalog.

    Examples of command to execute on devstack:
    ```
    # First run
    ./manage.py lms --settings=devstack push_ratings_catalog  --submission_date_to="2019-11-19"
    # Other examples
    ./manage.py lms --settings=devstack push_ratings_catalog  --submission_date_to="2019-11-18"
    ./manage.py lms --settings=devstack push_ratings_catalog  --submission_date_to="2019-11-18" --markers="RATING_INVALID_COURSE_ID"
    ```
    """

    CHUNK_SIZE = 2000
    FROM_PK = 1L
    MEASURE = 0
    HANDLE_RESUBMISSIONS = 0
    # Not what this command was designed for, but need to take
    # advantage and update all historical data!
    STORE_COURSE_AGU_ID = 0

    args = ""
    help = "Push historical ratings data to the AMAT Catalog (Pathway)."
    option_list = BaseCommand.option_list + (
        make_option("--courses_ids",
                    dest="courses_ids",
                    type="string",
                    action="callback",
                    callback=get_comma_separated_args,
                    help="Run the command for particular courses only. Course id should be of the standard course key "
                         "format, e.g. 'course-v1:RF+CS101+2019_T1'"),
        make_option("--markers",
                    dest="markers",
                    type="string",
                    action="callback",
                    callback=get_comma_separated_args,
                    help="Rating polls submissions' markers to consider (if specified, all the rest will "
                         "be filtered out), see 'poll_survey.catalog.constants' enums for codes. "
                         "Example: 'RATING_INVALID_COURSE_ID, RATING_INCORRECT_USER_ID, CATALOG_RATING_BAD_REQUEST'."),
        make_option("--submission_date_to",
                    dest="submission_date_to",
                    type="string",
                    help="Rating submissions date (will fetch entries created before this date). "
                         "Format: YYYY-MM-DD, e.g. '2019-09-13'"),
        make_option("--handle_resubmissions",
                    dest="handle_resubmissions",
                    type="int",
                    default=HANDLE_RESUBMISSIONS,
                    help="Instruction to handle re-submissions only."),
        make_option("--store_course_agu_id",
                    dest="store_course_agu_id",
                    type="int",
                    default=STORE_COURSE_AGU_ID,
                    help="Instruction to store course agu id in rating polls' submissions."),
        make_option("--from_pk",
                    dest="from_pk",
                    type="long",
                    default=FROM_PK,
                    help="PK of a rating poll submission to start from "
                         "(from the 'poll_survey_ratingpollsubmission' table)."),
        make_option("--measure",
                    dest="measure",
                    type="int",
                    default=MEASURE,
                    help="Instruction to measure submissions processing."),
        make_option("--chunk_size",
                    dest="chunk_size",
                    type="int",
                    default=CHUNK_SIZE,
                    help="Number of rating polls submissions in a chunk."))

    def handle(self, *args, **options):
        """
        Push historical ratings to the Catalog.
        """
        print("Processing historical ratings...")
        markers = options.get("markers")
        chunk_size = options.get("chunk_size")
        from_pk = options.get("from_pk")
        submission_date_to = datetime.strptime(options.get("submission_date_to"), '%Y-%m-%d')
        courses_ids = [CourseKey.from_string(k.strip()) for k in options.get("courses_ids")] \
            if options.get("courses_ids") else None
        measure = options.get("measure")
        handle_resubmissions = options.get("handle_resubmissions")
        store_course_agu_id = options.get("store_course_agu_id")

        if courses_ids:
            print("Considering particular courses only: {!s}".format(courses_ids))

        subs_count = prepare_polls_submissions_queryset(
            submissions_model=RatingPollSubmission,
            submission_date_to=submission_date_to,
            courses_ids=courses_ids,
            markers=markers,
            handle_resubmissions=handle_resubmissions,
        ).count()
        if subs_count:
            print("Found {!s} rating poll submissions.".format(subs_count))
        else:
            print("No rating poll submissions found.")
            return

        processed_subs_counter = 0
        sub_processing_time = 0
        catalog_api_client = AmatCatalogApiClient()

        for offset in range(0, subs_count, chunk_size):
            print("===================================offset: {!s}====================================\n"
                  "===================================================================================\n"                  
                  "Starting to process rating poll submissions from {!s} to {!s}."
                  .format(offset, offset, chunk_size+offset))
            for submission_entry in fetch_polls_submissions_entries(
                poll_type=RATING_POLL_NAME,
                offset=offset,
                chunk_size=chunk_size,
                from_pk=from_pk,
                submission_date_to=submission_date_to,
                courses_ids=courses_ids,
                markers=markers,
                handle_resubmissions=handle_resubmissions,
            ):
                sub_t1 = datetime.now() if measure else 0
                print("=============submission entry {!s}=============".format(submission_entry.id))
                marker = catalog_push_rating_poll_submission(submission_entry, catalog_api_client, stdout=True)
                submission_entry.store_catalog_marker(marker)
                if store_course_agu_id:
                    print("Storing course agu id.")
                    submission_entry.store_course_agu_id()
                processed_subs_counter += 1
                print("Processed {!s} submissions (submissions entries) out of {!s}.".format(
                    processed_subs_counter,
                    subs_count
                ))
                print("Latest processed submission entry id - {!s}, submission date - {!s}"
                      .format(submission_entry.id, submission_entry.created))
                print("Current offset: {!s}".format(offset))

                if measure:
                    sub_t2 = datetime.now()
                    diff = (sub_t2 - sub_t1).microseconds
                    sub_processing_time += diff
                    print("Processing time for one submission_entry: {!s} microseconds"
                          .format(diff))
                    print("Average processing time for one submission_entry: {!s} microseconds."
                          .format(float(sub_processing_time / processed_subs_counter)))

        if measure and processed_subs_counter:
            print("\n\n\nAverage processing time for one submission_entry (out of {!s} entries): {!s} microseconds."
                  .format(processed_subs_counter, float(sub_processing_time / processed_subs_counter)))

        print("============= THE END. =============")
