"""
Django management command to copy Series.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.content.course_overviews.models import Series, CourseOverview

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Clone a Series.

    Can perform full copy or override title, description and courses.
    seriesID and new-seriesID are required.

    Example usage:
        $ ./manage.py lms copy_series SE-003 --new-seriesID SE-007 --title 'Clone title' --description 'clone description' --courses course-v1:edX+DemoX+Demo_Course course-v1:org-1+CS111+2015_T1 --settings=devstack_docker
        $ ./manage.py lms copy_series SE-003 --new-seriesID SE-007 --settings=devstack_docker
    """
    help = 'Copy existing series, optionally update title, description and courses.'

    def add_arguments(self, parser):
        parser.add_argument(
            'seriesID',
            help='Target series id to copy from.'
        )
        parser.add_argument(
            '--new-seriesID',
            dest='new_id',
            help='New series id.'
        )
        parser.add_argument(
            '--title',
            required=False,
            help='New series title.'
        )
        parser.add_argument(
            '--description',
            required=False,
            help='New series description.'
        )
        parser.add_argument(
            '--courses',
            nargs='*',
            default=[],
            help='New series courses ids list.'
        )

    def handle(self, *args, **options):
        series_id = options.get('seriesID')
        new_id = options.get('new_id')
        courses = options.get('courses')
        title = options.get('title')
        description = options.get('description')
        source_series = Series.objects.filter(series_id=series_id).first()
        if not source_series:
            raise CommandError('Series [%s] not found. Provide a valid series id.' % series_id)

        title_to_add = title or source_series.title
        description_to_add = description or source_series.description

        if courses:
            courses_to_add = []
            for course_id in courses:
                try:
                    CourseOverview.objects.get(id=course_id)
                    courses_to_add.append(course_id)
                except (InvalidKeyError, IntegrityError, CourseOverview.DoesNotExist):
                    log.warning('Course id [%s] seems to be invalid, skipping...' % course_id)
            if not courses_to_add:
                raise CommandError('Could not copy the Series. All the provided course ids are not valid, '
                                   'that is not allowed, Series must contain at least one course. ')
        else:
            courses_to_add = source_series.courses.all()

        try:
            new_series = Series.objects.create(
                title=title_to_add,
                description=description_to_add,
                image=source_series.image,
                series_id=new_id
            )
        except IntegrityError:
            raise CommandError('Series with id [%s] already exists.' % new_id)

        new_series.courses.set(courses_to_add)

        self.stdout.write(self.style.SUCCESS('Successfully copied %s series data to %s.' % (series_id, new_id)))
