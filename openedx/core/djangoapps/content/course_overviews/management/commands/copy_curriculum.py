"""
Django management command to copy Curricula.
"""


import json
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, Curriculum, Series
from lms.djangoapps.courseware.utils import get_video_library_blocks_no_request

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Clone the curriculum.

    Can perform full copy or override title, description, courses, series and videos.
    curriculumID and new_id are required.

    Example usage:
        $ ./manage.py lms copy_curriculum RL-003 --new-curriculumID RL-007 --title 'Clone #6' --description 'clone description' --series ser2 ser3 --courses course-v1:edX+DemoX+Demo_Course course-v1:du+du+du --videos block-v1:00+00+00+type@video+block@deb8aa5796f3445391ff0d7326b2ab7d block-v1:00+00+00+type@video+block@5e01125c2b3944448fd0712aacd086f0+block@5e01125c2b3944448fd0712aacd086f0 --settings=devstack_docker
        $ ./manage.py lms copy_curriculum RL-003 --new-curriculumID RL-007 --settings=devstack_docker
    """
    help = 'Copy existing curriculum, optionally update title, description, series, courses and standalone videos.'

    def add_arguments(self, parser):
        parser.add_argument(
            'curriculumID',
            help='Target curriculum id to copy from.'
        )
        parser.add_argument(
            '--new-curriculumID',
            dest='new_id',
            required=True,
            help='New curriculum id.'
        )
        parser.add_argument(
            '--title',
            required=False,
            help='New curriculum title.'
        )
        parser.add_argument(
            '--description',
            required=False,
            help='New curriculum description.'
        )
        parser.add_argument(
            '--courses',
            nargs='*',
            default=[],
            help='New curriculum courses ids list.'
        )
        parser.add_argument(
            '--series',
            nargs='*',
            default=[],
            help='New curriculum series ids list.'
        )
        parser.add_argument(
            '--videos',
            nargs='*',
            default=[],
            help='New curriculum videos ids list.'
        )

    def handle(self, *args, **options):
        curriculum_id = options.get('curriculumID')
        new_id = options.get('new_id')
        courses = options.get('courses')
        series_ids = options.get('series')
        videos = options.get('videos')
        title = options.get('title')
        description = options.get('description')
        source_curriculum = Curriculum.objects.filter(curriculum_id=curriculum_id).first()
        if not source_curriculum:
            raise CommandError('Curriculum [%s] not found. Provide a valid curriculum id.' % curriculum_id)

        title_to_add = title or source_curriculum.title
        description_to_add = description or source_curriculum.description

        if videos:
            library = get_video_library_blocks_no_request()
            videos_to_add = []
            if not library:
                log.warning('Can\'t add videos. Video library is empty, try to add videos to library first.')
            else:
                library_videos = [vid['id'] for vid in library]
                for video in videos:
                    if video not in library_videos:
                        log.warning('Video [%s] does not exist in the video library. Skipping...' % video)
                    else:
                        videos_to_add.append(video)
                if videos_to_add:
                    videos_to_add = json.dumps(videos_to_add)
        else:
            videos_to_add = source_curriculum.standalone_videos

        if courses:
            courses_to_add = []
            for course_id in courses:
                try:
                    CourseOverview.objects.get(id=course_id)
                    courses_to_add.append(course_id)
                except (InvalidKeyError, CourseOverview.DoesNotExist):
                    log.warning('Course id [%s] seems to be invalid, skipping...' % course_id)
        else:
            courses_to_add = source_curriculum.courses.all()

        if series_ids:
            series_to_add = []
            for series_id in series_ids:
                try:
                    series = Series.objects.get(series_id=series_id)
                    series_to_add.append(series.id)
                except Series.DoesNotExist:
                    log.warning('Series with id [%s] seems to be invalid, skipping...' % series_id)
                    continue
        else:
            series_to_add = source_curriculum.series.all()

        if not any((videos_to_add, series_to_add, courses_to_add)):
            raise CommandError('Could not copy the curriculum, all of the values you provided '
                               'for series, courses and standalone videos are invalid. '
                               'This is not allowed, curriculum must include at least one '
                               'series, course or standalone video.')

        try:
            new_curriculum = Curriculum.objects.create(
                title=title_to_add,
                description=description_to_add,
                collection_type=source_curriculum.collection_type,
                image=source_curriculum.image,
                standalone_videos=videos_to_add,
                curriculum_id=new_id
            )
        except IntegrityError:
            raise CommandError('Curriculum with id [%s] already exist.' % new_id)

        if courses_to_add:
            new_curriculum.courses.set(courses_to_add)
        if series_to_add:
            new_curriculum.series.set(series_to_add)

        self.stdout.write(self.style.SUCCESS('Successfully copied %s curriculum data to %s.' % (curriculum_id, new_id)))
