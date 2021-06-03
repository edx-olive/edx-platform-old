# coding=utf-8

"""
Tests for search_video_library Django management command.
"""


from django.core.management.base import CommandError
from six import StringIO

from django.conf import settings
from django.core.management import call_command
from six import text_type

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


class TestSearchVideoLibrary(ModuleStoreTestCase):
    """
    Tests for `search_video_library` management command.
    """
    def setUp(self):
        """
        Setup a dummy course content.
        """
        super().setUp()

        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_1 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.video_2 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.vertical_2 = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_3 = ItemFactory.create(category="video", parent_location=self.vertical_2.location)

    def call_command(self, *args, **kwargs):
        """
        Call management command and return output
        """
        out = StringIO()  # To Capture the output of the command
        call_command('search_video_library', *args, stdout=out, **kwargs)
        out.seek(0)
        return out.read()

    def test_search_video_library(self):
        """
        Test the positive flow.
        """
        settings.VIDEO_LIBRARY_COURSE = text_type(self.course.id)
        output = self.call_command()
        video_locators = [
            text_type(v.location) for v in [self.video_1, self.video_2, self.video_3]
        ]
        for locator in video_locators:
            self.assertIn(locator, output)
        output = output.strip().split('\n')
        self.assertEqual(len(output), 3)

    def test_find_one(self):
        """
        Test the positive flow for concrete course.
        """
        settings.VIDEO_LIBRARY_COURSE = text_type(self.course.id)
        kwargs = {'find_one': text_type(self.video_1.location)}
        output = self.call_command(**kwargs)
        self.assertIn(text_type(self.video_1.location), output)
        self.assertNotIn(text_type(self.video_2.location), output)
        self.assertNotIn(text_type(self.video_3.location), output)
        output = output.strip().split('\n')
        self.assertEqual(len(output), 1)

    def test_wrong_library_id(self):
        """
        Test invalid library course id in the settings.
        """
        settings.VIDEO_LIBRARY_COURSE = 'course-v1:fake+fake+0'
        msg = 'Library course was not found. Please, check the VIDEO_LIBRARY_COURSE setting.'
        with self.assertRaisesRegex(CommandError, msg):
            self.call_command()

    def test_no_library_id(self):
        """
        Test no VIDEO_LIBRARY_COURSE setting present.
        """
        msg = 'There is no VIDEO_LIBRARY_COURSE value in the settings.'
        with self.assertRaisesRegex(CommandError, msg):
            self.call_command()

    def test_wrong_locator(self):
        """
        Test invalid video locator passed through args.
        """
        settings.VIDEO_LIBRARY_COURSE = text_type(self.course.id)
        # this is not a video locator
        kwargs = {'find_one': text_type(self.vertical.location)}
        output = self.call_command(**kwargs)
        self.assertIn('was not found in the library.', output)

    def test_no_videos_in_library(self):
        """
        Test case when there is no videos in the video library course.
        """
        course = CourseFactory.create()
        settings.VIDEO_LIBRARY_COURSE = text_type(course.id)
        output = self.call_command()
        self.assertIn('There are no videos in the library yet.', output)
