"""
Django management command to add/delete courses to Series.
"""


import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.content.course_overviews.models import Series


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Add/remove courses in the Series.

    Example usage:
        $ ./manage.py lms manage_series course-v1:edX+DemoX+Demo_Course course-v1:edX+E2E-101+course -s SeriesX --settings=devstack_docker
        $ ./manage.py lms manage_series course-v1:edX+DemoX+Demo_Course --series_id SeriesX -r --settings=devstack_docker
    """
    args = '<course_id course_id ...>'
    help = 'Add/remove courses in the Series. Default action is adding, to remove use the -r or --remove flag.'

    def add_arguments(self, parser):
        parser.add_argument(
            'courses_ids',
            nargs='+',
            help='Courses ids to add/remove.'
        )
        parser.add_argument(
            '--series_id', '-s',
            required=True,
            help='Series_id to manage.'
        )
        parser.add_argument(
            '--remove', '-r',
            action='store_true',
            help='Remove couses instead of adding to the Series. Series should include at least 1 course.'
        )

    def handle(self, *args, **options):
        series_id = options.get('series_id')
        course_ids = options.get('courses_ids')
        removing = options.get('remove')
        series = Series.objects.filter(series_id=series_id).first()
        if not series:
            raise CommandError('Series not found. Provide a valid value for series_id.')

        for course_id in course_ids:
            if removing:
                if series.courses.count() == 1:
                    raise CommandError(
                        'Series should include at least 1 course. Course [%s] was not removed.' % course_id
                    )
                try:
                    series.courses.remove(course_id)
                except InvalidKeyError:
                    log.warning('Provided course_id [%s] is not valid.' % course_id)
            else:
                try:
                    series.courses.add(course_id)
                except IntegrityError:
                    log.warning(
                        (
                            'Course with id [%s] has been already added to this series '
                            'or provided value is invalid.' % course_id
                        )
                    )
                except InvalidKeyError:
                    log.warning('Provided course_id [%s] is not valid.' % course_id)

        msg = 'Successfully processed courses with ids %s for series [%s].' % (
            course_ids,
            series_id
        )

        self.stdout.write(self.style.SUCCESS(msg))
