"""
Tests for the list_series management command.
"""

from io import StringIO
from contextlib import redirect_stdout
from unittest import skip

from django.core.management.base import CommandError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from openedx.core.djangoapps.content.course_overviews.management.commands import list_series
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
    SeriesFactory
)


class TestListSeries(ModuleStoreTestCase):
    """
    Tests for the list_series management command.
    """
    def setUp(self):
        super().setUp()
        self.courses = CourseOverviewFactory.create_batch(3)
        self.series = SeriesFactory.create()
        self.series.courses.set(self.courses)
        self.command = list_series.Command()

    def test_invalid_series_id(self):
        """
        Test command error when passing invalid series id.
        """
        errstring = "Series not found. Provide a valid value for seriesID."
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(seriesID='fake_id')

    @skip('Could not figure out how to capture stdout outputs')
    def test_valid_id(self):
        """
        Test positive flow for listing series' data.
        """
        f = StringIO()
        with redirect_stdout(f):
            self.command.handle(seriesID=self.series.series_id)
        output = f.getvalue()
        expected_output = """
        Printing data for series with ID: series_1

        Title: series_title_1
        Description: Series description
        Created by: None
        Creation date: 07/16/21 13:21
        Last modified: 07/16/21 13:21
        Courses: [
                 { ID: course-v1:edX+toy+2012_Fall_3, Title: course-v1:edX+toy+2012_Fall_3 Course },
                 { ID: course-v1:edX+toy+2012_Fall_4, Title: course-v1:edX+toy+2012_Fall_4 Course },
                 { ID: course-v1:edX+toy+2012_Fall_5, Title: course-v1:edX+toy+2012_Fall_5 Course },
        ]

        """
        self.assertIn(expected_output, output)
