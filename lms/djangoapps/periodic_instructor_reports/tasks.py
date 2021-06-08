"""
Celery tasks used by periodic_instructor_reports
"""
import logging
from datetime import date

from celery import task
from django.contrib.auth.models import User
from django.http.request import HttpRequest

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from lms.djangoapps.ccx.models import CustomCourseForEdX
from instructor_task.api import (
    submit_calculate_grades_csv,
    submit_calculate_students_features_csv,
    submit_problem_grade_report,
)

logger = logging.getLogger(__name__)

PERIODIC_REPORT_TASKS = {
    "calculate_grades_csv": submit_calculate_grades_csv,
    "calculate_students_features_csv": submit_calculate_students_features_csv,
    "calculate_problem_grade_report": submit_problem_grade_report,
}


@task # pylint: disable=not-callable
def periodic_task_wrapper(course_ids, *args, **kwargs):
    """
    Call instructor tasks in a periodic way.
    """

    task_name = kwargs.get("task_name")
    report_task = PERIODIC_REPORT_TASKS.get(task_name)

    if not report_task:
        logger.error('Periodic report generation called for an unknown task: "%s"', task_name)
        return

    creator_email = kwargs.get("creator_email", "")
    creator = User.objects.filter(email=creator_email)

    if not creator.exists():
        logger.error('Periodic report creator email does not exist: "%s"', creator_email)
        return

    # Create a fake request object as it is needed for the instructor tasks
    request = HttpRequest()
    request.user = creator.last()

    # Assign metadata needed for parsing the request properly
    request.META = {
        "REMOTE_ADDR": "0.0.0.0",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": 0,
    }

    include_related_ccx = kwargs.get("include_ccx", False)
    only_ccx = kwargs.get("only_ccx", False)
    upload_folder_prefix = kwargs.get("upload_folder_prefix", "")
    use_folders_by_date = kwargs.get("use_folders_by_date", False)
    filename = kwargs.get("filename", None)

    course_ids = [
        SlashSeparatedCourseKey.from_deprecated_string(course_id)
        for course_id in course_ids
    ]

    if include_related_ccx:
        custom_courses = CustomCourseForEdX.objects.filter(course_id__in=course_ids)
        ccx_course_ids = list({ccx.locator for ccx in custom_courses})

        if only_ccx:
            course_ids = ccx_course_ids
        else:
            course_ids.extend(ccx_course_ids)

    for course_id in course_ids:
        task_kwargs = {}

        if filename:
            task_kwargs.update({
                "filename": filename
            })

        if use_folders_by_date:
            task_kwargs.update({
                "upload_parent_dir": "{prefix}{folder}".format(
                    prefix=upload_folder_prefix,
                    folder=date.today().strftime("%Y/%m/%d")
                )
            })
        elif upload_folder_prefix:
            task_kwargs.update({
                "upload_parent_dir": upload_folder_prefix
            })

        logger.info('Calling periodic "%s" for course "%s"', task_name, course_id)
        report_task(request, course_id, *args, **task_kwargs)
