"""
Tests for the tag_course_as_new_and_interesting management command
"""


import datetime
import six

from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand, CommandError

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, NewAndInterestingTag


class TestTagAsNewAndInteresting(SharedModuleStoreTestCase):
    """
    Tests for the tag_course_as_new_and_interesting management command
    """

    @classmethod
    def setUpClass(cls):
        super(TestTagAsNewAndInteresting, cls).setUpClass()
        cls.course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        cls.course_overview = CourseOverview.get_from_id(cls.course.id)
        cls.command = Command()
        cls.default_end_date = (datetime.date.today() + datetime.timedelta(days=10)).strftime('%m/%d/%Y')

    def test_no_args(self):
        """
        Test 'tag_course_as_new_and_interesting' command with no arguments
        """
        if six.PY2:
            errstring = "Error: too few arguments"
        else:
            errstring = "Error: the following arguments are required: course_id, end_date"

        with self.assertRaisesRegex(CommandError, errstring):
            call_command('tag_course_as_new_and_interesting')

    def test_invalid_course_id(self):
        """
        Test 'tag_course_as_new_and_interesting' command with invalid course id
        """
        errstring = "Invalid course key."
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('tag_course_as_new_and_interesting', 'TestX/TS01', self.default_end_date)

    def test_too_many_arguments(self):
        """
        Test 'tag_course_as_new_and_interesting' command with more than 2 arguments
        """
        errstring = "Error: unrecognized arguments: invalid-arg"
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('tag_course_as_new_and_interesting', six.text_type(self.course.id),
                         '10/10/2020', 'invalid-arg')

    def test_end_date_wrong_format(self):
        """
        Test 'tag_course_as_new_and_interesting' command with wrong end date format
        """
        errstring = "End date is in the wrong format, the correct format is: MM/DD/YYYY."
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('tag_course_as_new_and_interesting', self.course.id, '25/10/2021')

    def test_end_date_in_past(self):
        """
        Test 'tag_course_as_new_and_interesting' command with end date in the past
        """
        errstring = "End date cannot be in the past."
        past_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime('%m/%d/%Y')
        with self.assertRaisesRegex(CommandError, errstring):
            call_command('tag_course_as_new_and_interesting', self.course.id, past_date)

    def test_correct_input(self):
        """
        Test 'tag_course_as_new_and_interesting' command with correct input
        """

        self.assertFalse(NewAndInterestingTag.objects.filter(course=self.course_overview).exists())
        call_command('tag_course_as_new_and_interesting', self.course.id, self.default_end_date)
        tag = NewAndInterestingTag.objects.get(course=self.course_overview)
        self.assertTrue(tag.expiration_date.strftime('%m/%d/%Y'), self.default_end_date)

    def test_correct_input_second_tag(self):
        """
        Test 'tag_course_as_new_and_interesting' command with correct input to tag a course which
        is already tagged
        """

        prev_tag = NewAndInterestingTag.objects.filter(course=self.course_overview).first()
        if not prev_tag:
            prev_tag = NewAndInterestingTag.objects.create(
                course=self.course_overview,
                expiration_date=(datetime.datetime.now() + datetime.timedelta(days=5)).date()
            )

        call_command('tag_course_as_new_and_interesting', self.course.id, self.default_end_date)
        new_tag = NewAndInterestingTag.objects.get(course=self.course_overview)

        self.assertFalse(new_tag.expiration_date == prev_tag.expiration_date)
