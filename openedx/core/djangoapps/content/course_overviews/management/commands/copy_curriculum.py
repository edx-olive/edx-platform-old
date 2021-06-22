"""
Django management command to copy Curricula.
"""


import json
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from openedx.core.djangoapps.content.course_overviews.models import Curriculum, Series

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
        courses_to_add = courses or source_curriculum.courses.all()
        series_to_add = Series.objects.filter(
            series_id__in=series_ids
        ) if series_ids else source_curriculum.series.all()
        videos_to_add = json.dumps(videos) if videos else source_curriculum.standalone_videos

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

        new_curriculum.courses.set(courses_to_add)
        new_curriculum.series.set(series_to_add)

        self.stdout.write(self.style.SUCCESS('Successfully copied %s curriculum data to %s.' % (curriculum_id, new_id)))
