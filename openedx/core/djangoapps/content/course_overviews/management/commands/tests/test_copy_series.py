"""
Tests for the copy_series management command.
"""
from django.core.management.base import CommandError
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from openedx.core.djangoapps.content.course_overviews.management.commands import copy_series
from openedx.core.djangoapps.content.course_overviews.models import Series
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
    SeriesFactory
)

LOGGER_NAME = 'openedx.core.djangoapps.content.course_overviews.management.commands.copy_series'


class TestCopySeries(ModuleStoreTestCase):
    """
    Tests for the copy_series management command.
    """
    def setUp(self):
        super().setUp()
        self.courses = CourseOverviewFactory.create_batch(3)
        self.series = SeriesFactory.create()
        self.series.courses.set(self.courses)
        self.command = copy_series.Command()

    def _call_command(self, **kwargs):
        """
        Call the copy command with provided kwargs.
        """
        self.assertEqual(
            Series.objects.all().count(),
            1
        )
        self.command.handle(seriesID=self.series.series_id, **kwargs)
        self.assertEqual(
            Series.objects.all().count(),
            2
        )

    def test_invalid_series_id(self):
        """
        Test command call with invalid target series id.
        """
        errstring = "Provide a valid series id.".format(self.series.series_id)
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle('fake_id')

    def test_new_id_exists(self):
        """
        Test command error when provided new id has already been used.
        """
        errstring = ' already exists.'.format(self.series.series_id)
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(seriesID=self.series.series_id, new_id=self.series.series_id)

    def test_full_copy(self):
        """
        Test positive flow for copying without fields update.
        """
        self._call_command(new_id='series002')

        new_series = Series.objects.get(series_id='series002')

        self.assertEqual(new_series.title, self.series.title)
        self.assertEqual(new_series.description, self.series.description)
        self.assertEqual(len(new_series.courses.all()), len(self.series.courses.all()))

    def test_copy_with_update(self):
        """
        Test positive flow for copying with fields update.
        """
        self._call_command(
            new_id='series002',
            title='New title',
            description='New description',
            courses=[self.courses[0].id],
        )

        new_series = Series.objects.get(series_id='series002')

        self.assertEqual(new_series.title, 'New title')
        self.assertEqual(new_series.description, 'New description')
        self.assertEqual(len(new_series.courses.all()), 1)
        self.assertEqual(new_series.courses.all()[0].id, self.courses[0].id)
