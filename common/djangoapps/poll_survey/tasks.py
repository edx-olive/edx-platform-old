"""
Periodic "poll_survey" tasks.
"""

from celery.task import task
from datetime import datetime
import logging

from poll_survey.catalog.client import AmatCatalogApiClient
from poll_survey.configs import RATING_POLL_NAME
from poll_survey.catalog.utils import (
    catalog_push_rating_poll_submission,
    fetch_polls_submissions_entries,
    prepare_polls_submissions_queryset,
)
from poll_survey.models import RatingPollSubmission


log = logging.getLogger('edx.celery.task')


@task(name="catalog_rating_polls")
def catalog_rating_polls():
    """
    Celery periodic task that gathers information about
    rating polls and pushes the data to the AMAT Pathway/Catalog.
    Runs every day at 11.30 a.m.
    """

    CHUNK_SIZE = 2000
    submission_date_to = datetime.now()
    catalog_api_client = AmatCatalogApiClient()

    # Check for newly-arrived submissions
    subs_count = prepare_polls_submissions_queryset(
        submissions_model=RatingPollSubmission,
        submission_date_to=submission_date_to,
    ).count()
    if subs_count:
        log.info("Found {!s} rating polls submissions.".format(subs_count))
        for offset in range(0, subs_count, CHUNK_SIZE):
            for submission_entry in fetch_polls_submissions_entries(
                poll_type=RATING_POLL_NAME,
                offset=offset,
                chunk_size=CHUNK_SIZE,
                submission_date_to=submission_date_to,
            ):
                marker = catalog_push_rating_poll_submission(submission_entry, catalog_api_client)
                submission_entry.store_catalog_marker(marker)

        log.info("Finished processing {!s} unmarked rating polls submissions.".format(subs_count))
    else:
        log.info("No rating polls submissions found.")

    # Now, check for re-submissions.
    resubmitted_subs_count = prepare_polls_submissions_queryset(
        submissions_model=RatingPollSubmission,
        handle_resubmissions=True,
    ).count()
    if resubmitted_subs_count:
        log.info("Found {!s} rating polls re-submissions.".format(resubmitted_subs_count))
        for offset in range(0, resubmitted_subs_count, CHUNK_SIZE):
            for submission_entry in fetch_polls_submissions_entries(
                poll_type=RATING_POLL_NAME,
                offset=offset,
                chunk_size=CHUNK_SIZE,
                handle_resubmissions=True,
            ):
                marker = catalog_push_rating_poll_submission(submission_entry, catalog_api_client)
                submission_entry.store_catalog_marker(marker)

        log.info("Finished processing {!s} rating polls re-submissions.".format(resubmitted_subs_count))
    else:
        log.info("No rating polls re-submissions found.")
