"""
Celery tasks for Sysadmin.
"""

import logging

from celery.task import task

from lms.djangoapps.dashboard.background_download.tasks_utils import export_courses_grades

log = logging.getLogger('edx.celery.task')


@task()
def export_courses_grades_csv_data(**kwargs):
    """
    Export overall courses grades report.
    Asynchronously export given data as a CSV file.
    """
    user_id = kwargs.get("user_id", "")
    log.info(f"Starting the task on grades report export for a user with id {user_id}")
    export_courses_grades(user_id=user_id)
    log.info(f"Finished the task on grades report export for a user with id {user_id}")
