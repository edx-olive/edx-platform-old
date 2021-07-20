"""
Tests for the list_curriculum management command.
"""

import json
from io import StringIO
from contextlib import redirect_stdout
from unittest import skip

from django.conf import settings
from django.core.management.base import CommandError
from six import text_type
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_overviews.management.commands import list_curriculum
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
    CurriculumFactory,
    SeriesFactory
)


class TestlistCurriculum(ModuleStoreTestCase):
    """
    Tests for the list_curriculum management command.
    """
    def setUp(self):
        super().setUp()
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.video_course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.video_course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video = ItemFactory.create(category="video", parent_location=self.vertical.location)
        self.courses = CourseOverviewFactory.create_batch(3)
        self.series = SeriesFactory.create_batch(3)
        self.curriculum = CurriculumFactory.create(
            courses=self.courses, standalone_videos=json.dumps([text_type(self.video.location)]), series=self.series
        )
        self.command = list_curriculum.Command()
        settings.VIDEO_LIBRARY_COURSE = text_type(self.video_course.id)

    def test_invalid_curriculum_id(self):
        """
        Test command error when passing invalid curriculum id.
        """
        errstring = "Curriculum not found. Provide a valid value for curriculumID."
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(curriculumID='fake_id')

    @skip('Could not figure out how to capture stdout outputs')
    def test_valid_id(self):
        """
        Test positive flow for listing curriculum data.
        """
        f = StringIO()
        with redirect_stdout(f):
            self.command.handle(curriculumID=self.curriculum.curriculum_id)
        output = f.getvalue()
        expected_output = """
        Printing data for curriculum with ID: curriculum_0

        Title: curriculum_title_0
        Type: Role
        Description: Test description
        Created by: None
        Creation date: 07/16/21 09:28
        Last modified: 07/16/21 09:28
        Series: [
                 { ID: series_0, Title: series_title_0 },
                 { ID: series_1, Title: series_title_1 },
                 { ID: series_2, Title: series_title_2 },
        ]
        Courses: [
                 { ID: course-v1:edX+toy+2012_Fall_0, Title: course-v1:edX+toy+2012_Fall_0 Course },
                 { ID: course-v1:edX+toy+2012_Fall_1, Title: course-v1:edX+toy+2012_Fall_1 Course },
                 { ID: course-v1:edX+toy+2012_Fall_2, Title: course-v1:edX+toy+2012_Fall_2 Course },
        ]
        Standalone videos: [
                 { ID: i4x://org.0/course_0/video/video_4, Title: video 4 },
        ]
        """
        self.assertIn(expected_output, output)
