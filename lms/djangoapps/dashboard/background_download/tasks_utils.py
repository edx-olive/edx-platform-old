"""Task utility logic, incorporating other utils."""

import logging
import os

from django.conf import settings

from dashboard.background_download.io_utils import cleanup_directory_files, create_empty_file, store_rows
from dashboard.background_download.data_utils import (
    define_subs_class,
    define_subs_size,
    fetch_submissions,
    prepare_course_ids,
    prepare_submission_datum,
)
from poll_survey.configs import (
    COURSE_QUALITY_SURVEY_NAME,
    OPEN_ENDED_SURVEY_NAME,
    POST_COURSE_SURVEY_NAME,
    PRE_COURSE_SURVEY_NAME,
    REGULAR_POLL_NAME,
    REGULAR_SURVEY_NAME,
)

log = logging.getLogger('edx.celery.task')


def export_all_polls_submissions(filename, chunk_size, courses_ids, user_id):

    if not settings.POLL_SURVEY_SUBMISSIONS_DIR.isdir():
        # FIXME the dir isn't created
        os.mkdir(settings.POLL_SURVEY_SUBMISSIONS_DIR)

    # To keep the filesystem clean, clean up the dir on a per-user basis.
    cleanup_directory_files(dir_path=settings.POLL_SURVEY_SUBMISSIONS_DIR, user_id=user_id)

    export_polls_submissions(poll_type=REGULAR_POLL_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids)
    export_polls_submissions(poll_type=REGULAR_SURVEY_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids, store_header=False)
    export_polls_submissions(poll_type=OPEN_ENDED_SURVEY_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids, store_header=False)
    export_polls_submissions(poll_type=PRE_COURSE_SURVEY_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids, store_header=False)
    export_polls_submissions(poll_type=POST_COURSE_SURVEY_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids, store_header=False)
    export_polls_submissions(poll_type=COURSE_QUALITY_SURVEY_NAME, filename=filename,
                             chunk_size=chunk_size, courses_ids=courses_ids, store_header=False,
                             rename_from_temp=True)


def export_polls_submissions(poll_type, courses_ids, chunk_size,
                             filename, rename_from_temp=False, store_header=True):
    subs_model_class = define_subs_class(poll_type)
    courses_ids = prepare_course_ids(courses_ids)
    subs_size = define_subs_size(courses_ids=courses_ids, subs_model_class=subs_model_class)
    log.debug("{} subs size: {!s}".format(poll_type, subs_size))

    header = (
        'poll_type',
        'course', 'student_id',
        'question_id', 'question_text',
        'answer_id', 'answer_text',
    )
    kwargs = {"poll_type": poll_type}
    if subs_size:
        for offset in range(0, subs_size, chunk_size):
            store_rows(
                filename=filename,
                header=header,
                store_header=store_header,
                datum_processor=prepare_submission_datum,
                data=fetch_submissions(courses_ids, subs_model_class,
                                       offset, chunk_size),
                datum_processor_kwargs=kwargs,
            )
    # We'll prepare an empty for courses with no polls submissions
    elif store_header:
        create_empty_file(
            filename=filename,
            header=header
        )

    if rename_from_temp:
        os.rename(
            settings.POLL_SURVEY_SUBMISSIONS_DIR / filename + ".tmp",
            settings.POLL_SURVEY_SUBMISSIONS_DIR / filename
        )
