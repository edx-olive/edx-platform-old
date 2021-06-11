# coding=utf-8

"""
Tests for search_video_library Django management command.
"""


from django.conf import settings
from six import text_type

from lms.djangoapps.courseware.utils import get_video_library_blocks_no_request
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory


LOGGER_NAME = 'lms.djangoapps.courseware.utils'


class TestGetVideoLibraryV2(ModuleStoreTestCase):
    """
    Tests for `get_video_library_blocks_no_request` management command.
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

    def test_get_video_library_v2(self):
        """
        Test the positive flow.
        """
        settings.VIDEO_LIBRARY_COURSE = text_type(self.course.id)
        result_locators = [video['id'] for video in get_video_library_blocks_no_request()]
        expected_locators = [
            text_type(v.location) for v in [self.video_1, self.video_2, self.video_3]
        ]
        for locator in result_locators:
            self.assertIn(locator, expected_locators)
        self.assertEqual(len(result_locators), 3)

    def test_wrong_library_id(self):
        """
        Test invalid library course id in the settings.
        """
        settings.VIDEO_LIBRARY_COURSE = 'course-v1:fake+fake+0'
        msg = 'Please, check that VIDEO_LIBRARY_COURSE setting was set correctly.'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            result = get_video_library_blocks_no_request()
            self.assertIn(msg, cm.output[0])
            self.assertEqual(len(result), 0)

    def test_no_library_id(self):
        """
        Test no VIDEO_LIBRARY_COURSE setting present.
        """
        msg = 'Please, check that VIDEO_LIBRARY_COURSE setting was set correctly.'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            result = get_video_library_blocks_no_request()
            self.assertIn(msg, cm.output[0])
            self.assertEqual(len(result), 0)

    def test_no_videos_in_library(self):
        """
        Test case when there is no videos in the video library course.
        """
        course = CourseFactory.create()
        settings.VIDEO_LIBRARY_COURSE = text_type(course.id)
        result = get_video_library_blocks_no_request()
        self.assertEqual(len(result), 0)
