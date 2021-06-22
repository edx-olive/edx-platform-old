"""
Django management command to edit curricula.
"""


import logging
import json

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from opaque_keys import InvalidKeyError
from openedx.core.djangoapps.content.course_overviews.models import Curriculum, Series, CourseOverview
from lms.djangoapps.courseware.utils import get_video_library_blocks_no_request


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Edit curriculum data.

    curriculumID is required.

    Example usage:
        $ ./manage.py lms edit_curriculum RL-003 --add-series ser2 --remove-courses course-v1:edX+DemoX+Demo_Course --settings=devstack_docker
        $ ./manage.py lms edit_curriculum RL-003 --title 'test new title' --description 'Brand new description' --add-courses course-v1:du+du+du --remove-courses course-v1:du+du+du course-v1:edX+DemoX+Demo_Course --remove-videos block-v1:00+00+00+type@video+block@deb8aa5796f3445391ff0d7326b2ab7d --add-videos block-v1:00+00+00+type@video+block@deb8aa5796f3445391ff0d7326b2ab7d block-v1:00+00+00+type@video+block@1974e9f1ff584bf9a7f1d3a272570a8d --add-series test_series --remove-series ser2 ser3 --settings=devstack_docker
    """
    help = 'Edit existing curriculum, optionally update title, description, series, courses and standalone videos.'

    def add_arguments(self, parser):
        parser.add_argument(
            'curriculumID',
            help='Target curriculum id.'
        )
        parser.add_argument(
            '--title',
            required=False,
            help='Title to set for the curriculum.'
        )
        parser.add_argument(
            '--description',
            required=False,
            help='Description to set for the curriculum.'
        )
        parser.add_argument(
            '--add-courses',
            nargs='*',
            dest='add_courses',
            default=[],
            help='Courses ids to add to the curriculum.'
        )
        parser.add_argument(
            '--remove-courses',
            nargs='*',
            dest='remove_courses',
            default=[],
            help='Courses ids to remove from curriculum.'
        )
        parser.add_argument(
            '--add-series',
            nargs='*',
            dest='add_series',
            default=[],
            help='Series_ids to add to the curriculum.'
        )
        parser.add_argument(
            '--remove-series',
            nargs='*',
            dest='remove_series',
            default=[],
            help='Series_id to remove from the curriculum.'
        )
        parser.add_argument(
            '--add-videos',
            nargs='*',
            dest='add_videos',
            default=[],
            help='Videos locators to add to the curriculum.'
        )
        parser.add_argument(
            '--remove-videos',
            nargs='*',
            dest='remove_videos',
            default=[],
            help='Videos locators to remove from the curriculum.'
        )

    def _get_videos(self, curriculum):
        """
        Helper method to deserialize curriculum standalone videos.

        Args:
            curriculum (Curriculum): Curriculum objects to get videos from.

        Returns:
            list: list of assigned video locators.
        """
        # Use replace for quotes to ensure videos are deserializable
        return json.loads(curriculum.standalone_videos.replace('\'', '"')) if curriculum.standalone_videos else []

    def _process_videos(self, curriculum, videos_to_add, videos_to_remove):
        """
        Helper method to process videos that should be updated.

        Args:
            curriculum (Curriculum): target Curriculum to update
            videos_to_add (list): list of video locators to add to curriculum
            videos_to_remove (list): list of video locators to remove from the curriculum

        Returns:
            resulting list of video locators curriculum should include or None
        """
        if not videos_to_add and not videos_to_remove:
            return

        library = get_video_library_blocks_no_request()
        if not library:
            log.warning(
                (
                    'Can\'t process videos. Video library is empty, '
                    'try to add videos to library first.'
                )
            )
            return
        library_videos = [vid['id'] for vid in library]
        curriculum_videos = self._get_videos(curriculum)
        videos_to_process = []

        for video in videos_to_add:
            if video not in library_videos:
                log.warning(
                    ('Video [%s] does not exist in the library. Skipping...' % video)
                )
            elif video in curriculum_videos:
                log.warning('Video [%s] already added to the curriculum. Skipping...' % video)
            else:
                videos_to_process.append(video)

        if curriculum_videos != videos_to_process:
            videos_to_process = curriculum_videos + videos_to_process
            if videos_to_remove:
                has_courses_or_series = any([curriculum.courses.count(), curriculum.series.count()])
                for v in videos_to_remove:
                    if not has_courses_or_series and len(videos_to_process) == 1:
                        log.warning(
                            (
                                'Can\'t remove video [%s], Curriculum should include at least one series, '
                                'course or standalone video.' % v
                            )
                        )
                        continue
                    try:
                        videos_to_process.remove(v)
                    except ValueError:
                        log.warning(
                            (
                                'Can\'t remove video [%s]. Check that video id is correct.' % v
                            )
                        )
            return videos_to_process
        return

    def handle(self, *args, **options):
        curriculum_id = options.get('curriculumID')
        courses_to_add = options.get('add_courses')
        courses_to_remove = options.get('remove_courses')
        series_ids_to_add = options.get('add_series')
        series_ids_to_remove = options.get('remove_series')
        videos_to_add = options.get('add_videos')
        videos_to_remove = options.get('remove_videos')
        title = options.get('title')
        description = options.get('description')
        curriculum = Curriculum.objects.filter(curriculum_id=curriculum_id).first()
        if not curriculum:
            raise CommandError('Curriculum not found. Provide a valid value for curriculumID.')

        for course_id in courses_to_add:
            if curriculum.courses.filter(id=course_id):
                log.warning(
                    (
                        'Course with id [%s] has been already added to this curriculum '
                        'or provided value is invalid.' % course_id
                    )
                )
            else:
                try:
                    CourseOverview.objects.get(id=course_id)
                    curriculum.courses.add(course_id)
                except (InvalidKeyError, IntegrityError, CourseOverview.DoesNotExist):
                    log.warning(
                        'Course id [%s] seems to be invalid, skipping...' % course_id
                    )

        for series_id in series_ids_to_add:
            try:
                series = Series.objects.get(series_id=series_id)
            except Series.DoesNotExist:
                log.warning(
                    (
                        'Series with id [%s] seems to be invalid, skipping...' % series_id
                    )
                )
                continue

            if curriculum.series.filter(series_id=series.series_id).exists():
                log.warning(
                    (
                        'Series with id [%s] has been already added to this curriculum '
                        'or provided value is invalid.' % series
                    )
                )
            else:
                curriculum.series.add(series)

        has_series_or_videos = any([curriculum.series.count(), len(self._get_videos(curriculum))])
        for course_id in courses_to_remove:
            if not has_series_or_videos and curriculum.courses.count() == 1:
                log.warning(
                    (
                        'Can\'t remove course [%s], Curriculum should include at least one series, '
                        'course or standalone video.' % course_id
                    )
                )
                continue
            try:
                curriculum.courses.get(id=course_id)
                curriculum.courses.remove(course_id)
            except CourseOverview.DoesNotExist:
                log.warning(
                    (
                        'Course with id [%s] does not belong to this curriculum. '
                        'Skipping...' % course_id
                    )
                )

        has_courses_or_videos = any([curriculum.courses.count(), len(self._get_videos(curriculum))])
        series_to_remove = Series.objects.filter(series_id__in=series_ids_to_remove)
        for series in series_to_remove:
            if not has_courses_or_videos and curriculum.series.count() == 1:
                log.warning(
                    (
                        'Can\'t remove series [%s], Curriculum should include at least one series, '
                        'course or standalone video.' % series.series_id
                    )
                )
                continue
            try:
                curriculum.series.get(series_id=series.series_id)
                curriculum.series.remove(series)
            except Series.DoesNotExist:
                log.warning(
                    (
                        'Series with id [%s] does not belong to this curriculum '
                        'or provided value is invalid.' % series
                    )
                )

        videos_to_update = self._process_videos(curriculum, videos_to_add, videos_to_remove)

        videos_changed = videos_to_update != None
        if videos_changed:
            curriculum.standalone_videos = json.dumps(videos_to_update)

        if title:
            curriculum.title = title

        if description:
            curriculum.description = description

        if any((title, description, videos_changed)):
            curriculum.save()


        self.stdout.write(self.style.SUCCESS('Successfully processed curriculum [%s] update.' % curriculum_id))

