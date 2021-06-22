"""
Tests for the copy_curriculum management command.
"""

import json

from django.conf import settings
from django.core.management.base import CommandError
from six import text_type
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_overviews.management.commands import copy_curriculum
from openedx.core.djangoapps.content.course_overviews.models import Curriculum
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
    CurriculumFactory,
    SeriesFactory
)

LOGGER_NAME = 'openedx.core.djangoapps.content.course_overviews.management.commands.copy_curriculum'


class TestCopyCurriculum(ModuleStoreTestCase):
    """
    Tests for the copy_curriculum management command.
    """
    def setUp(self):
        super().setUp()
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.video_course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.video_course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_1 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.video_2 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.vertical_2 = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_3 = ItemFactory.create(category="video", parent_location=self.vertical_2.location)
        self.courses = CourseOverviewFactory.create_batch(3)
        self.series = SeriesFactory.create_batch(3)
        self.curriculum = CurriculumFactory.create(
            courses=self.courses, standalone_videos=json.dumps([text_type(self.video_1.location)]), series=self.series
        )
        self.command = copy_curriculum.Command()
        settings.VIDEO_LIBRARY_COURSE = text_type(self.video_course.id)

    def _call_comand(self, **kwargs):
        """
        Simply call the copy command.
        """
        self.assertEqual(
            Curriculum.objects.all().count(),
            1
        )
        self.command.handle(curriculumID=self.curriculum.curriculum_id, **kwargs)
        self.assertEqual(
            Curriculum.objects.all().count(),
            2
        )

    def test_invalid_curriculum_id(self):
        """
        Test command call with invalid target curriculum id.
        """
        errstring = "Provide a valid curriculum id.".format(self.curriculum.curriculum_id)
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle('fake_id')

    def test_new_id_exists(self):
        """
        Test command error when provided new id has been already used.
        """
        errstring = ' already exist.'.format(
            self.curriculum.curriculum_id
        )
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(curriculumID=self.curriculum.curriculum_id, new_id=self.curriculum.curriculum_id)

    def test_full_copy(self):
        """
        Test positive flow for coping without fields update.
        """
        self._call_comand(new_id='curriculum002')

        old, new = Curriculum.objects.all()

        self.assertEqual(new.title, old.title)
        self.assertEqual(new.description, old.description)
        self.assertEqual(len(new.courses.all()), len(old.courses.all()))
        self.assertEqual(len(new.series.all()), len(old.series.all()))
        self.assertEqual(new.standalone_videos, old.standalone_videos)


    def test_copy_with_update(self):
        """
        Test positive flow for coping with fields update.
        """
        new_videos = json.dumps([text_type(self.video_3.location)])

        self._call_comand(
            new_id='curriculum002',
            title='New title',
            description='New description',
            courses=[self.courses[0]],
            series=[self.series[0].series_id],
            videos=json.loads(new_videos)
        )

        old, new = Curriculum.objects.all()

        self.assertEqual(new.title, 'New title')
        self.assertEqual(new.description, 'New description')
        self.assertEqual(len(new.courses.all()), 1)
        self.assertEqual(len(new.series.all()), 1)
        self.assertEqual(new.standalone_videos, new_videos)

        self.assertNotEqual(new.title, old.title)
        self.assertNotEqual(new.description, old.description)
        self.assertNotEqual(len(new.courses.all()), len(old.courses.all()))
        self.assertNotEqual(len(new.series.all()), len(old.series.all()))
        self.assertNotEqual(new.standalone_videos, old.standalone_videos)
