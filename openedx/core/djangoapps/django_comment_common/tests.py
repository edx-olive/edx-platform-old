# pylint: disable=missing-docstring


import six
import mock
from contracts import new_contract
from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from six import text_type

from openedx.core.djangoapps.course_groups.cohorts import CourseCohortsSettings
from openedx.core.djangoapps.django_comment_common.models import (
    CourseDiscussionSettings,
    Role,
    ForumsConfig,
    follow_new_thread,
    FORUM_ROLE_ADMINISTRATOR
)
from openedx.core.djangoapps.django_comment_common.utils import (
    get_course_discussion_settings,
    set_course_discussion_settings
)
from student.models import CourseEnrollment, User
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

new_contract('basestring', six.string_types[0])


class RoleAssignmentTest(ModuleStoreTestCase):
    """
    Basic checks to make sure our Roles get assigned and unassigned as students
    are enrolled and unenrolled from a course.
    """

    def setUp(self):
        super(RoleAssignmentTest, self).setUp()
        # Check a staff account because those used to get the Moderator role
        self.staff_user = User.objects.create_user(
            "patty",
            "patty@fake.edx.org",
        )
        self.staff_user.is_staff = True

        self.student_user = User.objects.create_user(
            "hacky",
            "hacky@fake.edx.org"
        )
        self.course_key = CourseLocator("edX", "Fake101", "2012")
        CourseEnrollment.enroll(self.staff_user, self.course_key)
        CourseEnrollment.enroll(self.student_user, self.course_key)

    def test_enrollment_auto_role_creation(self):
        student_role = Role.objects.get(
            course_id=self.course_key,
            name="Student"
        )

        self.assertEqual([student_role], list(self.staff_user.roles.all()))
        self.assertEqual([student_role], list(self.student_user.roles.all()))

    # The following was written on the assumption that unenrolling from a course
    # should remove all forum Roles for that student for that course. This is
    # not necessarily the case -- please see comments at the top of
    # django_comment_client.models.assign_default_role(). Leaving it for the
    # forums team to sort out.
    #
    # def test_unenrollment_auto_role_removal(self):
    #     another_student = User.objects.create_user("sol", "sol@fake.edx.org")
    #     CourseEnrollment.enroll(another_student, self.course_id)
    #
    #     CourseEnrollment.unenroll(self.student_user, self.course_id)
    #     # Make sure we didn't delete the actual Role
    #     student_role = Role.objects.get(
    #         course_id=self.course_id,
    #         name="Student"
    #     )
    #     self.assertNotIn(student_role, self.student_user.roles.all())
    #     self.assertIn(student_role, another_student.roles.all())

    @mock.patch('openedx.core.djangoapps.django_comment_common.models.thread_followed')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.user.User.follow')
    @mock.patch('openedx.core.djangoapps.django_comment_common.models.get_course_threads')
    def test_posts_followed_when_discussion_admin_added(
        self,
        mock_get_course_threads,
        mock_user_follow,
        mock_thread_followed
    ):
        # Need to enable forum config to subscribe for updates
        config = ForumsConfig.current()
        config.enabled = True
        config.save()
        # assign admin role
        discussion_admin_role, created = Role.objects.get_or_create(
            course_id=self.course_key,
            name=FORUM_ROLE_ADMINISTRATOR
        )
        self.assertTrue(created)

        mock_get_course_threads.return_value = [{'id': 1}, {'id': 3}]
        discussion_admin_role.users.add(self.student_user)
        mock_get_course_threads.assert_called_once_with(str(self.course_key))
        self.assertIn(discussion_admin_role, self.student_user.roles.all())
        mock_user_follow.assert_called()
        self.assertEqual(mock_user_follow.call_count, 2)

    @mock.patch('openedx.core.djangoapps.django_comment_common.models.CourseKey.from_string')
    @mock.patch('openedx.core.djangoapps.django_comment_common.models.User')
    @mock.patch('openedx.core.djangoapps.django_comment_common.comment_client.user.User.follow')
    def test_admin_follow_new_thread(self, mock_cc_user, mock_django_user, mock_course_key):
        post = mock.Mock()
        user = mock.Mock()
        mock_course_key.return_value = self.course_key
        mock_django_user.objects.filter.return_value = [user(1), user(2)]
        follow_new_thread(None, post)
        mock_course_key.assert_called_once()
        self.assertEqual(mock_cc_user.call_count, 2)


class CourseDiscussionSettingsTest(ModuleStoreTestCase):

    def setUp(self):
        super(CourseDiscussionSettingsTest, self).setUp()
        self.course = CourseFactory.create()

    def test_get_course_discussion_settings(self):
        discussion_settings = get_course_discussion_settings(self.course.id)
        self.assertEqual(CourseDiscussionSettings.NONE, discussion_settings.division_scheme)
        self.assertEqual([], discussion_settings.divided_discussions)
        self.assertFalse(discussion_settings.always_divide_inline_discussions)

    def test_get_course_discussion_settings_legacy_settings(self):
        self.course.cohort_config = {
            'cohorted': True,
            'always_cohort_inline_discussions': True,
            'cohorted_discussions': ['foo']
        }
        modulestore().update_item(self.course, ModuleStoreEnum.UserID.system)
        discussion_settings = get_course_discussion_settings(self.course.id)
        self.assertEqual(CourseDiscussionSettings.COHORT, discussion_settings.division_scheme)
        self.assertEqual(['foo'], discussion_settings.divided_discussions)
        self.assertTrue(discussion_settings.always_divide_inline_discussions)

    def test_get_course_discussion_settings_cohort_settings(self):
        CourseCohortsSettings.objects.get_or_create(
            course_id=self.course.id,
            defaults={
                'is_cohorted': True,
                'always_cohort_inline_discussions': True,
                'cohorted_discussions': ['foo', 'bar']
            }
        )
        discussion_settings = get_course_discussion_settings(self.course.id)
        self.assertEqual(CourseDiscussionSettings.COHORT, discussion_settings.division_scheme)
        self.assertEqual(['foo', 'bar'], discussion_settings.divided_discussions)
        self.assertTrue(discussion_settings.always_divide_inline_discussions)

    def test_set_course_discussion_settings(self):
        set_course_discussion_settings(
            course_key=self.course.id,
            divided_discussions=['cohorted_topic'],
            division_scheme=CourseDiscussionSettings.ENROLLMENT_TRACK,
            always_divide_inline_discussions=True,
        )
        discussion_settings = get_course_discussion_settings(self.course.id)
        self.assertEqual(CourseDiscussionSettings.ENROLLMENT_TRACK, discussion_settings.division_scheme)
        self.assertEqual(['cohorted_topic'], discussion_settings.divided_discussions)
        self.assertTrue(discussion_settings.always_divide_inline_discussions)

    def test_invalid_data_types(self):
        exception_msg_template = "Incorrect field type for `{}`. Type must be `{}`"
        fields = [
            {'name': 'division_scheme', 'type': six.string_types[0]},
            {'name': 'always_divide_inline_discussions', 'type': bool},
            {'name': 'divided_discussions', 'type': list}
        ]
        invalid_value = 3.14

        for field in fields:
            with self.assertRaises(ValueError) as value_error:
                set_course_discussion_settings(self.course.id, **{field['name']: invalid_value})

            self.assertEqual(
                text_type(value_error.exception),
                exception_msg_template.format(field['name'], field['type'].__name__)
            )
