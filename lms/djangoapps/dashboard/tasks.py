"""Celery tasks for Sysadmin (`dashboard` app)."""

import logging
import time

from celery.task import task

from dashboard.background_download.tasks_utils import export_all_polls_submissions

log = logging.getLogger('edx.celery.task')


@task()
def export_poll_survey_csv_data(**kwargs):
    """
    Asynchronously export given data as a CSV file.

    Exports student answers to all supported questions to a CSV file.

    Ref.:
        https://github.com/open-craft/xblock-poll/blob/c7ebcc471153c860e1f8f4035f4f162c72b3f778/poll/tasks.py#L11
    """

    start_timestamp = time.time()
    user_id = kwargs.get("user_id", "")
    courses_ids = kwargs.get("courses_ids", [])
    filename = "poll_survey_submissions_{!s}_{!s}.csv".format(int(time.time()), user_id)

    log.info("Starting to process polls/surveys submissions...")
    export_all_polls_submissions(filename=filename, courses_ids=courses_ids, chunk_size=500, user_id=user_id)
    generation_time_s = time.time() - start_timestamp

    return {
        "error": None,
        "report_filename": filename,
        "start_timestamp": start_timestamp,
        "generation_time_s": generation_time_s,
    }
