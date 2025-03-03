"""
Test the various password reset flows
"""

import json
import re
import unicodedata
import unittest
from datetime import datetime, timedelta

import ddt
from django.conf import settings
from django.contrib.auth.hashers import UNUSABLE_PASSWORD_PREFIX, make_password
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import INTERNAL_RESET_SESSION_TOKEN, PasswordResetConfirmView
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail
from django.core.cache import cache
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.http import int_to_base36
from freezegun import freeze_time
from mock import Mock, patch
from oauth2_provider import models as dot_models
from pytz import UTC

from openedx.core.djangoapps.oauth_dispatch.tests import factories as dot_factories
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.core.djangoapps.user_api.models import UserRetirementRequest
from openedx.core.djangoapps.user_api.tests.test_views import UserAPITestCase
from openedx.core.djangoapps.user_api.accounts import EMAIL_MAX_LENGTH, EMAIL_MIN_LENGTH
from openedx.core.djangoapps.user_authn.views.password_reset import (
    SETTING_CHANGE_INITIATED, password_reset, password_reset_logistration,
    PasswordResetConfirmWrapper)
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from common.djangoapps.student.tests.factories import TEST_PASSWORD, UserFactory
from common.djangoapps.student.tests.test_configuration_overrides import fake_get_value
from common.djangoapps.student.tests.test_email import mock_render_to_string
from common.djangoapps.student.models import AccountRecovery

from common.djangoapps.util.password_policy_validators import create_validator_config
from common.djangoapps.util.testing import EventTestMixin


ENABLE_LOGISTRATION_MICROFRONTEND = settings.FEATURES.copy()
ENABLE_LOGISTRATION_MICROFRONTEND['ENABLE_LOGISTRATION_MICROFRONTEND'] = True


def process_request(request):
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()


@unittest.skipUnless(
    settings.ROOT_URLCONF == "lms.urls",
    "reset password tests should only run in LMS"
)
@ddt.ddt
class ResetPasswordTests(EventTestMixin, CacheIsolationTestCase):
    """
    Tests that clicking reset password sends email, and doesn't activate the user
    """
    request_factory = RequestFactory()
    ENABLED_CACHES = ['default']

    def setUp(self):  # pylint: disable=arguments-differ
        super(ResetPasswordTests, self).setUp('openedx.core.djangoapps.user_authn.views.password_reset.tracker')
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)

        self.user_bad_passwd = UserFactory.create()
        self.user_bad_passwd.is_active = False
        self.user_bad_passwd.password = UNUSABLE_PASSWORD_PREFIX
        self.user_bad_passwd.save()

    def setup_request_session_with_token(self, request):
        """
        Internal helper to setup request session and add token in session.
        """
        process_request(request)
        request.session[INTERNAL_RESET_SESSION_TOKEN] = self.token

    @property
    def password_reset_confirm_url(self):
        """
        Returns Password reset confirm URL
        """
        return reverse("password_reset_confirm", kwargs={"uidb36": self.uidb36, "token": self.token})

    def send_password_reset_request(self):
        """
        Sends GET request on password reset url.
        """
        request = self.request_factory.get(self.password_reset_confirm_url)
        self.setup_request_session_with_token(request)
        return request

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_user_bad_password_reset(self):
        """
        Tests password reset behavior for user with password marked UNUSABLE_PASSWORD_PREFIX
        """

        bad_pwd_req = self.request_factory.post('/password_reset/', {'email': self.user_bad_passwd.email})
        bad_pwd_req.user = AnonymousUser()
        bad_pwd_resp = password_reset(bad_pwd_req)
        # If they've got an unusable password, we return a successful response code
        self.assertEqual(bad_pwd_resp.status_code, 200)
        obj = json.loads(bad_pwd_resp.content.decode('utf-8'))
        self.assertEqual(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_nonexist_email_password_reset(self):
        """
        Now test the exception cases with of reset_password called with invalid email.
        """

        bad_email_req = self.request_factory.post('/password_reset/', {'email': self.user.email + "makeItFail"})
        bad_email_req.user = AnonymousUser()
        bad_email_resp = password_reset(bad_email_req)
        # Note: even if the email is bad, we return a successful response code
        # This prevents someone potentially trying to "brute-force" find out which
        # emails are and aren't registered with edX
        self.assertEqual(bad_email_resp.status_code, 200)
        obj = json.loads(bad_email_resp.content.decode('utf-8'))
        self.assertEqual(obj, {
            'success': True,
            'value': "('registration/password_reset_done.html', [])",
        })
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_password_reset_ratelimited_for_non_existing_user(self):
        """
        Test that reset password endpoint only allow one request per minute
        for non-existing user.
        """
        self.assert_password_reset_ratelimitted('thisdoesnotexist@foo.com', AnonymousUser())
        self.assert_no_events_were_emitted()

    @patch(
        'openedx.core.djangoapps.user_authn.views.password_reset.render_to_string',
        Mock(side_effect=mock_render_to_string, autospec=True)
    )
    def test_password_reset_ratelimited_for_existing_user(self):
        """
        Test that reset password endpoint only allow one request per minute
        for existing user.
        """
        self.assert_password_reset_ratelimitted(self.user.email, self.user)
        self.assert_event_emission_count(SETTING_CHANGE_INITIATED, 1)

    def assert_password_reset_ratelimitted(self, email, user):
        """
        Assert that password reset endpoint allow one request per minute per email.
        """
        cache.clear()
        password_reset_req = self.request_factory.post('/password_reset/', {'email': email})
        password_reset_req.user = user
        password_reset_req.site = Mock(domain='example.com')
        good_resp = password_reset(password_reset_req)
        self.assertEqual(good_resp.status_code, 200)

        # then the rate limiter should kick in and give a HttpForbidden response
        bad_resp = password_reset(password_reset_req)
        self.assertEqual(bad_resp.status_code, 403)

        cache.clear()

    def assert_email_sent_successfully(self, expected):
        """
        Verify that the password confirm email has been sent to the user.
        """
        from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        sent_message = mail.outbox[0]
        body = sent_message.body

        self.assertIn(expected['subject'], sent_message.subject)
        self.assertIn(expected['body'], body)
        self.assertEqual(sent_message.from_email, from_email)
        self.assertEqual(len(sent_message.to), 1)
        self.assertIn(self.user.email, sent_message.to)

    def test_ratelimitted_from_same_ip_with_different_email(self):
        """
        Test that password reset endpoint allow only one request per minute per IP.
        """
        cache.clear()
        good_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist@foo.com'})
        good_req.user = AnonymousUser()
        good_resp = password_reset(good_req)
        self.assertEqual(good_resp.status_code, 200)

        # change the email ID and verify that the rate limiter should kick in and
        # give a Forbidden response if the request is from same IP.
        bad_req = self.request_factory.post('/password_reset/', {'email': 'thisdoesnotexist2@foo.com'})
        bad_req.user = AnonymousUser()
        bad_resp = password_reset(bad_req)
        self.assertEqual(bad_resp.status_code, 403)

        cache.clear()

    def test_ratelimited_from_different_ips_with_same_email(self):
        """
        Test that password reset endpoint allow only two requests per hour
        per email address.
        """
        cache.clear()
        self.request_password_reset(200)
        # now reset the time to 1 min from now in future and change the email and
        # verify that it will allow another request from same IP
        reset_time = datetime.now(UTC) + timedelta(seconds=61)
        with freeze_time(reset_time):
            for status in [200, 403]:
                self.request_password_reset(status)

            # Even changing the IP will not allow more than two requests for same email.
            new_ip = "8.8.8.8"
            self.request_password_reset(403, new_ip=new_ip)

        cache.clear()

    def request_password_reset(self, status, new_ip=None):
        extra_args = {}
        if new_ip:
            extra_args = {'REMOTE_ADDR': new_ip}

        reset_request = self.request_factory.post(
            '/password_reset/',
            {'email': 'thisdoesnotexist@foo.com'},
            **extra_args
        )

        if new_ip:
            self.assertEqual(reset_request.META.get('REMOTE_ADDR'), new_ip)

        reset_request.user = AnonymousUser()
        response = password_reset(reset_request)
        self.assertEqual(response.status_code, status)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data(('plain_text', "You're receiving this e-mail because you requested a password reset"),
              ('html', "You&#39;re receiving this e-mail because you requested a password reset"))
    @ddt.unpack
    def test_reset_password_email(self, body_type, expected_output):
        """Tests contents of reset password email, and that user is not active"""
        good_req = self.request_factory.post('/password_reset/', {'email': self.user.email})
        good_req.user = self.user
        good_req.site = Mock(domain='example.com')
        dot_application = dot_factories.ApplicationFactory(user=self.user)
        dot_access_token = dot_factories.AccessTokenFactory(user=self.user, application=dot_application)
        dot_factories.RefreshTokenFactory(user=self.user, application=dot_application, access_token=dot_access_token)
        good_resp = password_reset(good_req)
        self.assertEqual(good_resp.status_code, 200)
        self.assertFalse(dot_models.AccessToken.objects.filter(user=self.user).exists())
        self.assertFalse(dot_models.RefreshToken.objects.filter(user=self.user).exists())
        obj = json.loads(good_resp.content.decode('utf-8'))
        self.assertTrue(obj['success'])
        self.assertIn('e-mailed you instructions for setting your password', obj['value'])

        from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        sent_message = mail.outbox[0]

        bodies = {
            'plain_text': sent_message.body,
            'html': sent_message.alternatives[0][0],
        }

        body = bodies[body_type]

        self.assertIn("Password reset", sent_message.subject)
        self.assertIn(expected_output, body)
        self.assertEqual(sent_message.from_email, from_email)
        self.assertEqual(len(sent_message.to), 1)
        self.assertIn(self.user.email, sent_message.to)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None,
        )

        # Test that the user is not active
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

        self.assertIn('password_reset_confirm/', body)
        re.search(r'password_reset_confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/', body).groupdict()

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data((False, 'http://'), (True, 'https://'))
    @ddt.unpack
    def test_reset_password_email_https(self, is_secure, protocol):
        """
        Tests that the right url protocol is included in the reset password link
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.site = Mock(domain='example.com')
        req.is_secure = Mock(return_value=is_secure)
        req.user = self.user
        password_reset(req)
        sent_message = mail.outbox[0]
        msg = sent_message.body
        expected_msg = "Please go to the following page and choose a new password:\n\n" + protocol

        self.assertIn(expected_msg, msg)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )

    @override_settings(FEATURES=ENABLE_LOGISTRATION_MICROFRONTEND)
    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data(('Crazy Awesome Site', 'Crazy Awesome Site'), ('edX', 'edX'))
    @ddt.unpack
    def test_reset_password_email_site(self, site_name, platform_name):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        with patch("django.conf.settings.PLATFORM_NAME", platform_name):
            with patch("django.conf.settings.SITE_NAME", site_name):
                req = self.request_factory.post(
                    '/password_reset/', {'email': self.user.email}
                )
                req.user = self.user
                req.site = Mock(domain='example.com')
                password_reset(req)
                sent_message = mail.outbox[0]
                msg = sent_message.body

                reset_msg = u"you requested a password reset for your user account at {}"
                reset_msg = reset_msg.format(site_name)

                self.assertIn(reset_msg, msg)
                self.assertIn(settings.LOGISTRATION_MICROFRONTEND_URL, msg)

                sign_off = u"The {} Team".format(platform_name)
                self.assertIn(sign_off, msg)

                self.assert_event_emitted(
                    SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
                )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    @ddt.data('plain_text', 'html')
    def test_reset_password_email_configuration_override(self, body_type):
        """
        Tests that the right url domain and platform name is included in
        the reset password email
        """
        req = self.request_factory.post(
            '/password_reset/', {'email': self.user.email}
        )
        req.get_host = Mock(return_value=None)
        req.site = Mock(domain='example.com')
        req.user = self.user

        with patch('crum.get_current_request', return_value=req):
            password_reset(req)

        sent_message = mail.outbox[0]
        bodies = {
            'plain_text': sent_message.body,
            'html': sent_message.alternatives[0][0],
        }

        body = bodies[body_type]

        reset_msg = u"you requested a password reset for your user account at {}".format(
            fake_get_value('PLATFORM_NAME')
        )

        self.assertIn(reset_msg, body)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED, user_id=self.user.id, setting=u'password', old=None, new=None
        )
        self.assertEqual(sent_message.from_email, "no-reply@fakeuniversity.com")

    @ddt.data(
        ('invalidUid', 'invalid_token'),
        (None, 'invalid_token'),
        ('invalidUid', None),
    )
    @ddt.unpack
    def test_reset_password_bad_token(self, uidb36, token):
        """
        Tests bad token and uidb36 in password reset
        """
        if uidb36 is None:
            uidb36 = self.uidb36
        if token is None:
            token = self.token

        bad_request = self.request_factory.get(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb36": uidb36, "token": token}
            )
        )
        process_request(bad_request)
        bad_request.user = AnonymousUser()
        PasswordResetConfirmWrapper.as_view()(bad_request, uidb36=uidb36, token=token)
        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)

    def test_reset_password_good_token(self):
        """
        Tests good token and uidb36 in password reset.

        Scenario:
        When the password reset url is opened
        Then the page is redirected to url without token
        And token gets set in session
        When the redirected page is visited with token in session
        Then reset password page renders
        And inactive user is set to active
        """
        good_reset_req = self.send_password_reset_request()
        good_reset_req.user = self.user
        redirect_response = PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)

        good_reset_req = self.request_factory.get(redirect_response.url)
        self.setup_request_session_with_token(good_reset_req)
        good_reset_req.user = self.user
        # set-password is the new token representation in the redirect url
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token='set-password')

        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_reset_password_good_token_with_anonymous_user(self):
        """
        Tests good token and uidb36 in password reset for anonymous user.

        Scenario:
        When the password reset url is opened with anonymous user in request
        Then the page is redirected to url without token
        And token gets set in session
        When the redirected page is visited with token in session
        Then reset password page renders
        And inactive user associated with token is set to active
        """
        good_reset_req = self.send_password_reset_request()
        good_reset_req.user = AnonymousUser()
        redirect_response = PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)

        good_reset_req = self.request_factory.get(redirect_response.url)
        self.setup_request_session_with_token(good_reset_req)
        good_reset_req.user = AnonymousUser()
        # set-password is the new token representation in the redirect url
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token='set-password')

        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_password_reset_fail(self):
        """
        Tests that if we provide mismatched passwords, user is not marked as active.
        """
        self.assertFalse(self.user.is_active)

        request_params = {'new_password1': 'password1', 'new_password2': 'password2'}
        confirm_request = self.request_factory.post(self.password_reset_confirm_url, data=request_params)
        self.setup_request_session_with_token(confirm_request)
        confirm_request.user = self.user

        # Make a password reset request with mismatching passwords.
        resp = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        # Verify the response status code is: 200 with password reset fail and also verify that
        # the user is not marked as active.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_password_reset_retired_user_fail(self):
        """
        Tests that if a retired user attempts to reset their password, it fails.
        """
        self.assertFalse(self.user.is_active)

        # Retire the user.
        UserRetirementRequest.create_retirement_request(self.user)

        reset_req = self.request_factory.get(self.password_reset_confirm_url)
        reset_req.user = self.user
        resp = PasswordResetConfirmWrapper.as_view()(reset_req, uidb36=self.uidb36, token=self.token)

        # Verify the response status code is: 200 with password reset fail and also verify that
        # the user is not marked as active.
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.get(pk=self.user.pk).is_active)

    def test_password_reset_normalize_password(self):
        # pylint: disable=anomalous-unicode-escape-in-string
        """
        Tests that if we provide a not properly normalized password, it is saved using our normalization
        method of NFKC.
        In this test, the input password is u'p\u212bssword'. It should be normalized to u'p\xc5ssword'
        """
        password = u'p\u212bssword'
        request_params = {'new_password1': password, 'new_password2': password}
        confirm_request = self.request_factory.post(self.password_reset_confirm_url, data=request_params)
        process_request(confirm_request)
        confirm_request.session[INTERNAL_RESET_SESSION_TOKEN] = self.token
        confirm_request.user = self.user
        confirm_request.site = Mock(domain='example.com')
        __ = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        user = User.objects.get(pk=self.user.pk)
        salt_val = user.password.split('$')[1]
        expected_user_password = make_password(unicodedata.normalize('NFKC', u'p\u212bssword'), salt_val)
        self.assertEqual(expected_user_password, user.password)

        self.assert_email_sent_successfully({
            'subject': 'Password reset completed',
            'body': 'This is to confirm that you have successfully changed your password'
        })

    @override_settings(AUTH_PASSWORD_VALIDATORS=[
        create_validator_config(
            'common.djangoapps.util.password_policy_validators.MinimumLengthValidator', {'min_length': 2}
        ),
        create_validator_config(
            'common.djangoapps.util.password_policy_validators.MaximumLengthValidator', {'max_length': 10}
        ),
    ])
    @ddt.data(
        {
            'password': '1',
            'error_message': 'This password is too short. It must contain at least 2 characters.',
        },
        {
            'password': '01234567891',
            'error_message': 'This password is too long. It must contain no more than 10 characters.',
        }
    )
    def test_password_reset_with_invalid_length(self, password_dict):
        """
        Tests that if we provide password characters less then PASSWORD_MIN_LENGTH,
        or more than PASSWORD_MAX_LENGTH, password reset will fail with error message.
        """
        request_params = {'new_password1': password_dict['password'], 'new_password2': password_dict['password']}
        confirm_request = self.request_factory.post(self.password_reset_confirm_url, data=request_params)
        self.setup_request_session_with_token(confirm_request)
        confirm_request.user = self.user

        # Make a password reset request with minimum/maximum passwords characters.
        response = PasswordResetConfirmWrapper.as_view()(confirm_request, uidb36=self.uidb36, token=self.token)

        self.assertEqual(response.context_data['err_msg'], password_dict['error_message'])

    @patch.object(PasswordResetConfirmView, 'dispatch')
    @patch("openedx.core.djangoapps.site_configuration.helpers.get_value", fake_get_value)
    def test_reset_password_good_token_configuration_override(self, reset_confirm):
        """
        Tests password reset confirmation page for site configuration override.
        """
        good_reset_req = self.send_password_reset_request()
        good_reset_req.user = self.user
        PasswordResetConfirmWrapper.as_view()(good_reset_req, uidb36=self.uidb36, token=self.token)
        confirm_kwargs = reset_confirm.call_args[1]
        self.assertEqual(confirm_kwargs['extra_context']['platform_name'], 'Fake University')
        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', "Test only valid in LMS")
    @ddt.data('Crazy Awesome Site', 'edX')
    def test_reset_password_email_subject(self, platform_name):
        """
        Tests that the right platform name is included in
        the reset password email subject
        """
        with patch("django.conf.settings.PLATFORM_NAME", platform_name):
            req = self.request_factory.post(
                '/password_reset/', {'email': self.user.email}
            )
            req.user = self.user
            req.site = Mock(domain='example.com')
            password_reset(req)
            sent_message = mail.outbox[0]
            subj = sent_message.subject

            self.assertIn(platform_name, subj)

    def test_reset_password_with_other_user_link(self):
        """
        Tests that user should not be able to reset password through other user's token
        """
        reset_request = self.request_factory.get(self.password_reset_confirm_url)
        reset_request.user = UserFactory.create()

        self.assertRaises(Http404, PasswordResetConfirmWrapper.as_view(), reset_request, uidb36=self.uidb36,
                          token=self.token)


@ddt.ddt
@skip_unless_lms
class PasswordResetViewTest(UserAPITestCase):
    """Tests of the user API's password reset endpoint. """

    def setUp(self):
        super(PasswordResetViewTest, self).setUp()
        self.url = reverse("user_api_password_reset")

    @ddt.data("get", "post")
    def test_auth_disabled(self, method):
        self.assertAuthDisabled(method, self.url)

    def test_allowed_methods(self):
        self.assertAllowedMethods(self.url, ["GET", "HEAD", "OPTIONS"])

    def test_put_not_allowed(self):
        response = self.client.put(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_delete_not_allowed(self):
        response = self.client.delete(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_patch_not_allowed(self):
        response = self.client.patch(self.url)
        self.assertHttpMethodNotAllowed(response)

    def test_password_reset_form(self):
        # Retrieve the password reset form
        response = self.client.get(self.url, content_type="application/json")
        self.assertHttpOK(response)

        # Verify that the form description matches what we expect
        form_desc = json.loads(response.content.decode('utf-8'))
        assert form_desc['method'] == 'post'
        assert form_desc['submit_url'] == reverse('password_change_request')
        assert form_desc['fields'] ==\
               [{'name': 'email', 'defaultValue': '', 'type': 'email', 'exposed': True,
                 'required': True, 'label': 'Email', 'placeholder': 'username@domain.com',
                 'instructions': 'The email address you used to register with {platform_name}'
                .format(platform_name=settings.PLATFORM_NAME),
                 'restrictions': {'min_length': EMAIL_MIN_LENGTH,
                                  'max_length': EMAIL_MAX_LENGTH},
                 'errorMessages': {}, 'supplementalText': '',
                 'supplementalLink': '',
                 'loginIssueSupportLink': 'https://support.example.com/login-issue-help.html'}]


@skip_unless_lms
class PasswordResetTokenValidateViewTest(UserAPITestCase):
    """Tests of the user API's password reset endpoint. """

    def setUp(self):
        super(PasswordResetTokenValidateViewTest, self).setUp()
        self.user = UserFactory.create()
        self.user.is_active = False
        self.user.save()
        self.token = '{uidb36}-{token}'.format(
            uidb36=int_to_base36(self.user.id),
            token=default_token_generator.make_token(self.user)
        )
        self.url = reverse("user_api_password_reset_token_validate")

    def test_reset_password_valid_token(self):
        """
        Verify that API valid token response and activate user if not active.
        """
        response = self.client.post(self.url, data={'token': self.token})
        json_response = json.loads(response.content.decode('utf-8'))
        self.assertTrue(json_response.get('is_valid'))

        self.user = User.objects.get(pk=self.user.pk)
        self.assertTrue(self.user.is_active)

    def test_reset_password_invalid_token(self):
        """
        Verify that API invalid token response if token is invalid.
        """
        response = self.client.post(self.url, data={'token': 'invalid-token'})
        json_response = json.loads(response.content.decode('utf-8'))
        self.assertFalse(json_response.get('is_valid'))

    def test_reset_password_token_with_other_user(self):
        """
        Verify that API returns invalid token response if the user different.
        """
        different_user = UserFactory.create(password=TEST_PASSWORD)
        self.client.login(username=different_user.username, password=TEST_PASSWORD)

        response = self.client.post(self.url, {'token': self.token})
        json_response = json.loads(response.content.decode('utf-8'))
        self.assertFalse(json_response.get('is_valid'))

        self.user = User.objects.get(pk=self.user.pk)
        self.assertFalse(self.user.is_active)


@ddt.ddt
@unittest.skipUnless(
    settings.ROOT_URLCONF == "lms.urls",
    "reset password tests should only run in LMS"
)
class ResetPasswordAPITests(EventTestMixin, CacheIsolationTestCase):
    """Tests of the logistration API's password reset endpoint. """
    request_factory = RequestFactory()
    ENABLED_CACHES = ['default']

    def setUp(self):
        super(ResetPasswordAPITests, self).setUp('openedx.core.djangoapps.user_authn.views.password_reset.tracker')
        self.user = UserFactory.create()
        self.user.save()
        self.token = default_token_generator.make_token(self.user)
        self.uidb36 = int_to_base36(self.user.id)
        self.secondary_email = 'secondary@test.com'
        AccountRecovery.objects.create(user=self.user, secondary_email=self.secondary_email)

    def create_reset_request(self, uidb36, token, is_account_recovery, new_password2='new_password1'):
        """Helper to create reset password post request"""

        request_param = {'new_password1': 'new_password1', 'new_password2': new_password2}
        query_param = "?track=pwreset&is_account_recovery=true" if is_account_recovery else "?track=pwreset"
        post_request = self.request_factory.post(
            reverse(
                "logistration_password_reset",
                kwargs={"uidb36": uidb36, "token": token}
            ) + query_param,
            request_param
        )
        return post_request

    @ddt.data(
        (None, None, True),
        (None, 'invalid_token', False),
    )
    @ddt.unpack
    def test_password_reset_request(self, uidb36, token, status):
        """Tests password reset request with valid/invalid token"""

        uidb36 = uidb36 or self.uidb36
        token = token or self.token

        post_request = self.create_reset_request(uidb36, token, False)
        post_request.user = AnonymousUser()
        json_response = password_reset_logistration(post_request, uidb36=uidb36, token=token)
        json_response = json.loads(json_response.content.decode('utf-8'))
        self.assertEqual(json_response.get('reset_status'), status)

    def test_none_token_in_password_reset_request(self):
        """
        Test that user should not be able to reset password through no token/uidb36
        """
        uidb36 = None
        token = None

        post_request = self.create_reset_request(self.uidb36, self.token, False)
        post_request.user = AnonymousUser()
        self.assertRaises(Exception, password_reset_logistration(post_request, uidb36=uidb36, token=token))

    def test_password_mismatch_in_reset_request(self):
        """
        Test that user should not be able to reset password with password mismatch
        """
        post_request = self.create_reset_request(self.uidb36, self.token, False, 'new_password2')
        post_request.user = AnonymousUser()
        json_response = password_reset_logistration(post_request, uidb36=self.uidb36, token=self.token)
        json_response = json.loads(json_response.content.decode('utf-8'))
        self.assertFalse(json_response.get('reset_status'))

    def test_account_recovery_using_forgot_password(self):
        """
        Test that with is_account_recovery query param available, primary
        email is updated with linked secondary email.
        """
        post_request = self.create_reset_request(self.uidb36, self.token, True)
        post_request.user = AnonymousUser()
        password_reset_logistration(post_request, uidb36=self.uidb36, token=self.token)

        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.email, self.secondary_email)

        self.assert_event_emitted(
            SETTING_CHANGE_INITIATED,
            user_id=self.user.id,
            setting=u'email',
            old=self.user.email,
            new=updated_user.email
        )

    def test_password_reset_email_sent_on_account_recovery_email(self):
        """
        Test that with is_account_recovery query param available, password
        reset email is sent to newly updated email address.
        """
        post_request = self.create_reset_request(self.uidb36, self.token, True)
        post_request.user = AnonymousUser()
        post_request.site = Mock(domain='example.com')
        password_reset_logistration(post_request, uidb36=self.uidb36, token=self.token)
        updated_user = User.objects.get(id=self.user.id)

        from_email = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
        sent_message = mail.outbox[0]
        body = sent_message.body

        self.assertIn('Password reset completed', sent_message.subject)
        self.assertIn('This is to confirm that you have successfully changed your password', body)
        self.assertEqual(sent_message.from_email, from_email)
        self.assertEqual(len(sent_message.to), 1)
        self.assertIn(updated_user.email, sent_message.to[0])
