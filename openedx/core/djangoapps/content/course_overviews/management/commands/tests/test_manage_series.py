"""
Tests for the manage_series management command
"""


from django.core.management.base import CommandError

from openedx.core.djangoapps.content.course_overviews.management.commands import manage_series
from openedx.core.djangoapps.content.course_overviews.models import Series
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory, SeriesFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

LOGGER_NAME = 'openedx.core.djangoapps.content.course_overviews.management.commands.manage_series'


class TestManageSeries(ModuleStoreTestCase):
    """
    Tests for the manage_series management command
    """
    def setUp(self):
        super(TestManageSeries, self).setUp()
        self.series_id = SeriesFactory.create().series_id
        self.courses = CourseOverviewFactory.create_batch(3)
        self.courses_ids = [str(course.id) for course in self.courses]
        self.course_id_1 = CourseOverviewFactory.create().id
        self.course_id_2 = CourseOverviewFactory.create().id
        self.command = manage_series.Command()

    def _add_all_courses_to_series(self):
        """
        Simply adds all the courses to the series.
        """
        self.command.handle(courses_ids=self.courses_ids, series_id=self.series_id)
        self.assertEqual(
            Series.objects.filter(series_id=self.series_id).first().courses.count(),
            len(self.courses_ids)
        )

    def test_invalid_series_id(self):
        """
        Test 'manage_series' command with invalid series_id
        """
        errstring = "Series not found. Provide a valid value for series_id."
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(self.courses_ids, series_id='fake-series-id')

    def test_course_already_added(self):
        """
        Test command logs a warning when trying to add course that already exists in the series.
        """
        self._add_all_courses_to_series()
        errstring = 'Course with id [{}] has been already added to this series or provided value is invalid.'.format(
            self.courses_ids[0]
        )
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self.command.handle(courses_ids=[self.courses_ids[0]], series_id=self.series_id)
            self.assertIn(errstring, cm.output[0])

    def test_remove_last_course(self):
        """
        Test command should keep at least 1 course in the series.
        """
        self._add_all_courses_to_series()
        errstring = 'Series should include at least 1 course.'
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(courses_ids=self.courses_ids, series_id=self.series_id, remove=True)

    def test_success(self):
        """
        Test positive flow for adding/removing courses.
        """
        self.assertEqual(
            Series.objects.filter(series_id=self.series_id).first().courses.count(),
            0
        )
        self._add_all_courses_to_series()

        self.command.handle(courses_ids=self.courses_ids[:-1], series_id=self.series_id, remove=True)
        self.assertEqual(
            Series.objects.filter(series_id=self.series_id).first().courses.count(),
            1
        )


