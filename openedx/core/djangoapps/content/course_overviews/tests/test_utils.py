"""
Tests for the course_overview utils.
"""


from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.utils import (
    get_course_language_options,
    clean_course_number_from_lang_suffix,
    get_course_lang_from_number
)


LOGGER_NAME = 'openedx.core.djangoapps.content.course_overviews.utils'


class TestUtils(ModuleStoreTestCase):
    """
    Tests for the CourseOverview utills.
    """
    def setUp(self):
        super().setUp()
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.default_display_name = 'Test'
            self.default_num = 'num'
            self.default_org = 'org'
            self.default_run = 'run1'
            self.course_en = CourseFactory.create(
                org=self.default_org,
                number=self.default_num,
                run=self.default_run,
                display_name=self.default_display_name,
            )
            self.course_uk = CourseFactory.create(
                org=self.default_org,
                number=self.default_num + '-uk',
                run=self.default_run,
                display_name=self.default_display_name,
            )
            self.overview_en = CourseOverview.get_from_id(self.course_en.id)
            self.overview_uk = CourseOverview.get_from_id(self.course_uk.id)

    def test_get_course_language_options(self):
        """
        Test get_course_language_options positive flow.
        """
        result = get_course_language_options(self.course_en)
        expected = {'Українська': str(self.course_uk.id), 'English': str(self.course_en.id)}
        self.assertEqual(result, expected)

    def test_get_course_language_options_default_lang(self):
        """
        Test get_course_language_options for standalone course without lang suffix and options.
        """
        course_without_options = CourseFactory.create(
            org=self.default_org,
            number='custom_num',
            run=self.default_run,
            display_name=self.default_display_name,
        )
        CourseOverview.get_from_id(course_without_options.id)
        result = get_course_language_options(course_without_options)
        self.assertEqual(result, {'English': str(course_without_options.id)})

    def test_get_course_lang_duplicate_lang(self):
        """
        Test get_course_language_options with duplicate language.

        Probably a vary rare case.
        """
        second_en_course = CourseFactory.create(
            org=self.default_org,
            number=self.default_num + '-en',
            run=self.default_run,
            display_name=self.default_display_name,
        )
        CourseOverview.get_from_id(second_en_course.id)
        errstring = 'Found duplicate language option'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            result = get_course_language_options(self.course_uk)
            self.assertIn(errstring, cm.output[0])
            self.assertIn(str(second_en_course.id), cm.output[0])
            self.assertIn(str(self.course_en.id), cm.output[0])
            self.assertEqual(len(result), 2)

    def test_clean_course_number_from_lang_suffix(self):
        """
        Test clean_course_number_from_lang_suffix positive flow.
        """
        result = clean_course_number_from_lang_suffix(self.course_uk.display_number_with_default)
        self.assertEqual(result, self.default_num)

    def test_clean_course_number_from_lang_suffix_no_underscores(self):
        """
        Test clean_course_number_from_lang_suffix for number without underscores.
        """
        course = CourseFactory.create(number=self.default_num)
        result = clean_course_number_from_lang_suffix(course.display_number_with_default)
        self.assertEqual(result, self.default_num)

    def test_clean_course_number_from_lang_suffix_suffix_is_not_lang(self):
        """
        Test clean_course_number_from_lang_suffix for number without language code.
        """
        num_with_underscores = 'has_underscores_but_no_language_code'
        course = CourseFactory.create(number=num_with_underscores)
        result = clean_course_number_from_lang_suffix(course.display_number_with_default)
        self.assertEqual(result, num_with_underscores)

    def test_get_course_lang_from_number(self):
        """
        Test get_course_lang_from_number positive flow.
        """
        result = get_course_lang_from_number(self.course_uk.display_number_with_default)
        self.assertEqual(result, 'Українська')

    def test_get_course_lang_from_number_no_underscores(self):
        """
        Test get_course_lang_from_number for number without underscores.
        """
        course = CourseFactory.create(number=self.default_num)
        result = get_course_lang_from_number(course.display_number_with_default)
        self.assertEqual(result, 'English')

    def test_get_course_lang_from_number_suffix_is_not_lang(self):
        """
        Test get_course_lang_from_number for number without language code.
        """
        num_with_underscores = 'has_underscores_but_no_language_code'
        course = CourseFactory.create(number=num_with_underscores)
        result = get_course_lang_from_number(course.display_number_with_default)
        self.assertEqual(result, 'English')
