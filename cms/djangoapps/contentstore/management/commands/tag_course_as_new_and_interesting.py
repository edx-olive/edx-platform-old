"""
Django management command to tag a course as new and interesting
"""


from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import NewAndInterestingTag, CourseOverview


class Command(BaseCommand):
    """
    Tag a course as new and interesting. Takes two arguments:
    <course_id>: ID of a course you want to tag as new and interesting
    <end_date>: Date after which a course stops being tagged. Format: MM/DD/YYYY
    """

    help = 'Tag a course as new and interesting.'

    def add_arguments(self, parser):
        parser.add_argument('course_id',
                            help='ID of a course to be tagged')
        parser.add_argument('end_date',
                            help="Date after which a course stops being tagged. Format: MM/DD/YYYY")

    def handle(self, *args, **options):
        try:
            course_key = CourseKey.from_string(options['course_id'])
            end_date = datetime.strptime(options['end_date'], '%m/%d/%Y')
        except InvalidKeyError:
            raise CommandError("Invalid course key.")
        except ValueError:
            raise CommandError("End date is in the wrong format, the correct format is: MM/DD/YYYY.")

        if end_date.date() < datetime.now().date():
            raise CommandError("End date cannot be in the past.")

        try:
            course = CourseOverview.get_from_id(course_key)
        except CourseOverview.DoesNotExist:
            raise CommandError("Course not found.")

        if not course:
            raise CommandError("Course not found.")

        NewAndInterestingTag.objects.update_or_create(
            course=course,
            defaults={'expiration_date': end_date}
        )

        message = 'Successfully tagged course %s as new and interesting till %s.'
        self.stdout.write(self.style.SUCCESS(message % (course, end_date.strftime("%b %d %Y"))))
