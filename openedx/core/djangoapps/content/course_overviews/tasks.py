

import logging

import six
from celery import task
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.conf import settings
from opaque_keys.edx.keys import CourseKey
from six.moves import range  # pylint: disable=ungrouped-imports

from ccx_keys.locator import CCXLocator
from xmodule.modulestore.django import modulestore

log = logging.getLogger(__name__)


DEFAULT_ALL_COURSES = False

DEFAULT_CHUNK_SIZE = 50

DEFAULT_FORCE_UPDATE = False


def chunks(sequence, chunk_size):
    return (sequence[index: index + chunk_size] for index in range(0, len(sequence), chunk_size))


def _task_options(routing_key):
    task_options = {}
    if getattr(settings, 'HIGH_MEM_QUEUE', None):
        task_options['routing_key'] = settings.HIGH_MEM_QUEUE
    if routing_key:
        task_options['routing_key'] = routing_key
    return task_options


def enqueue_async_course_overview_update_tasks(
        course_ids,
        all_courses=False,
        force_update=False,
        chunk_size=DEFAULT_CHUNK_SIZE,
        routing_key=None
):
    if all_courses:
        course_keys = [course.id for course in modulestore().get_course_summaries()]
    else:
        course_keys = [CourseKey.from_string(id) for id in course_ids]

    for course_key_group in chunks(course_keys, chunk_size):
        course_key_strings = [six.text_type(key) for key in course_key_group]

        options = _task_options(routing_key)
        async_course_overview_update.apply_async(
            args=course_key_strings,
            kwargs={'force_update': force_update},
            **options
        )


@task(base=LoggedPersistOnFailureTask)
def async_course_overview_update(*args, **kwargs):
    # import here to avoid ciclic import
    from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
    course_keys = [CourseKey.from_string(arg) for arg in args]
    CourseOverview.update_select_courses(course_keys, force_update=kwargs['force_update'])


@task
def task_reindex_courses(course_ids=[], series_id=None, curriculum_id=None):
    """
    Do reindex for given course_id's list, series_id or curriculum_id.

    Args:
        course_ids (list, optional): list of course id's (str). Defaults to [].
        series_id (string, optional): series id for reindexing all courses in the series.
        curriculum_id (string, optional): pk for the curriculum to reindex all its courses.
    """
    from cms.djangoapps.contentstore.courseware_index import CoursewareSearchIndexer
    courses = set(course_ids) if course_ids else set()

    if series_id:
        from openedx.core.djangoapps.content.course_overviews.models import Series
        series = Series.objects.filter(id=series_id).first()
        if series:
            series_courses_ids = series.courses.values_list('id', flat=True)
            courses.update(str(x) for x in series_courses_ids)

    if curriculum_id:
        from openedx.core.djangoapps.content.course_overviews.models import Curriculum
        curriculum = Curriculum.objects.filter(id=series_id).first()
        if curriculum:
            curriculum_courses = set(str(x.id) for x in curriculum.courses.all())
            curriculum_courses.update(str(c[0]) for c in curriculum.series.all().values_list('courses'))
            courses.union(curriculum_courses)

    for course_id in courses:
        course_key = CourseKey.from_string(course_id)
        # ccx courses are breaking indexing
        if isinstance(course_id, CCXLocator):
            continue
        CoursewareSearchIndexer.do_course_reindex(modulestore(), course_key)
