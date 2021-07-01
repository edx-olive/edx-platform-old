"""
Test cases for custom login_required decorator.
"""

import urllib

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.test.client import RequestFactory
from django.http import HttpResponse

from lms.djangoapps.courseware.views.utils import custom_login_required


class CustomLoginRequiredDecoratorTestCase(TestCase):
    """
    Test custom login_required decorator.
    """
    factory = RequestFactory()

    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(username='test', password='qwerty')
        cls.anonymous = AnonymousUser()

    @staticmethod
    def run_decorated_view(request):
        @custom_login_required()
        def a_view(view_request):
            return HttpResponse()

        return a_view(request)

    def test_authorized(self):
        """Test that authorized user receives requested view and does not get redirected to the login page."""
        request = self.factory.get('/random_url')
        request.user = self.user
        self.assertEqual(request.user.is_authenticated(), True)
        response = self.run_decorated_view(request)
        self.assertEqual(response.status_code, 200)

    def test_unauthorized(self):
        """
        Test that not authorized user gets redirected to the login page and next parameter
        of the login url is the absolute url of the initially requested view.
        """
        request = self.factory.get('/random_url')
        request.user = self.anonymous
        self.assertEqual(request.user.is_authenticated(), False)
        response = self.run_decorated_view(request)
        expected_redirect_url = '/login?next=%s' % request.build_absolute_uri()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urllib.unquote(response.url),
            expected_redirect_url,
        )
