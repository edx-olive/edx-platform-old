"""
Django management command to list Series' data.
"""


import logging
import warnings


from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.content.course_overviews.models import Series

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    List series' data.

    Example usage:
        $ ./manage.py lms list_series SE-003 --settings=devstack_docker
    """
    help = 'List series\' data.'

    def add_arguments(self, parser):
        parser.add_argument(
            'seriesID',
            help='Series ID.'
        )

    def handle(self, *args, **options):
        # hide warnings from django which would pop out during printing series' data
        warnings.filterwarnings("ignore")

        series_id = options.get('seriesID')
        series = Series.objects.filter(series_id=series_id).first()
        if not series:
            raise CommandError('Series not found. Provide a valid value for seriesID.')

        courses = series.courses.all()

        self.stdout.write(self.style.SUCCESS(
            'Printing data for series with ID: {series_id}\n'
            '\nTitle: {title}'
            '\nDescription: {description}'
            '\nCreated by: {created_by}'
            '\nCreation date: {creation_date}'
            '\nLast modified: {last_modified}'.format(
                series_id=series_id,
                title=series.title,
                description=series.description,
                created_by=series.created_by,
                creation_date=series.creation_date.strftime("%m/%d/%Y %H:%M"),
                last_modified=series.last_modified.strftime("%m/%d/%Y %H:%M"),
            )
        ))
        if courses.exists():
            self.stdout.write(self.style.SUCCESS('Courses: ['))
            for course in courses:
                self.stdout.write(self.style.SUCCESS('\t { ID: %s, Title: %s },') % (course.id, course.display_name))
            self.stdout.write(self.style.SUCCESS(']'))
