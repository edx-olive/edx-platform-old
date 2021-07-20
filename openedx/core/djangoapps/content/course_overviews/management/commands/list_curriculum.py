"""
Django management command to list Curriculum data.
"""


import json
import logging
import warnings


from django.core.management.base import BaseCommand, CommandError

from openedx.core.djangoapps.content.course_overviews.models import Curriculum

from lms.djangoapps.courseware.utils import get_video_library_blocks_no_request

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    List curriculum's data.

    Example usage:
        $ ./manage.py lms list_curriculum RL-003 --settings=devstack_docker
    """
    help = 'List curriculum\'s data.'

    def add_arguments(self, parser):
        parser.add_argument(
            'curriculumID',
            help='Curriculum ID.'
        )

    def handle(self, *args, **options):
        # hide warnings from django which would pop out during printing curriculum data
        warnings.filterwarnings("ignore")

        curriculum_id = options.get('curriculumID')
        curriculum = Curriculum.objects.filter(curriculum_id=curriculum_id).first()
        if not curriculum:
            raise CommandError('Curriculum not found. Provide a valid value for curriculumID.')

        series = curriculum.series.all()
        courses = curriculum.courses.all()
        videos = []
        if curriculum.standalone_videos:
            video_library = get_video_library_blocks_no_request()
            videos_keys = json.loads(curriculum.standalone_videos.replace('\'', '"'))
            videos = [video for video in video_library if video['id'] in videos_keys]
        self.stdout.write(self.style.SUCCESS(
            'Printing data for curriculum with ID: {curriculum_id}\n'
            '\nTitle: {title}'
            '\nType: {type}'
            '\nDescription: {description}'
            '\nCreated by: {created_by}'
            '\nCreation date: {creation_date}'
            '\nLast modified: {last_modified}'.format(
                curriculum_id=curriculum_id,
                title=curriculum.title,
                description=curriculum.description,
                type=curriculum.get_collection_type_display(),
                created_by=curriculum.created_by,
                creation_date=curriculum.creation_date.strftime("%m/%d/%Y %H:%M"),
                last_modified=curriculum.last_modified.strftime("%m/%d/%Y %H:%M"),
            )
        ))
        if series.exists():
            self.stdout.write(self.style.SUCCESS('Series: ['))
            for ser in series:
                self.stdout.write(self.style.SUCCESS('\t { ID: %s, Title: %s },') % (ser.series_id, ser.title))
            self.stdout.write(self.style.SUCCESS(']'))
        if courses.exists():
            self.stdout.write(self.style.SUCCESS('Courses: ['))
            for course in courses:
                self.stdout.write(self.style.SUCCESS('\t { ID: %s, Title: %s },') % (course.id, course.display_name))
            self.stdout.write(self.style.SUCCESS(']'))
        if videos:
            self.stdout.write(self.style.SUCCESS('Standalone videos: ['))
            for video in videos:
                self.stdout.write(self.style.SUCCESS('\t { ID: %s, Title: %s },') % (video['id'], video['name']))
            self.stdout.write(self.style.SUCCESS(']'))
