"""
Tests for custom AMAT views and utils.
"""
import datetime
import time
from unittest.mock import patch, mock_open
from urllib.parse import urlparse, parse_qs

from django.test import TestCase
import requests

from util.custom_views import form_cloudfront_url


class FormCloudfrontUrlTestCase(TestCase):
    """ Tests for sign Cloudfront URL function """
    def setUp(self):
        """ Set valid video url from content store """
        super(FormCloudfrontUrlTestCase, self).setUp()
        self.resource_url = "https://d2a8rd6kt4zb64.cloudfront.net/course-v1_Appliedx_AX001_Self-Paced/Appliedx_Gary-Promo_edit3(720p)HB2.mp4"

    def test_sign_url(self):
        """ Tests that url is successfully signed """
        response = requests.get(self.resource_url)
        self.assertEqual(response.status_code, 403)

        signed_url = form_cloudfront_url(self.resource_url)
        self.assertNotEqual(self.resource_url, signed_url)

        response = requests.get(signed_url)
        self.assertEqual(response.status_code, 200)

    def test_broken_url(self):
        """ Tests that changed url is not valid """
        signed_url = form_cloudfront_url(self.resource_url)

        response = requests.get(signed_url)
        self.assertEqual(response.status_code, 200)

        broken_signed_url = signed_url[:150] + "brokensign" + signed_url[150:]
        response = requests.get(self.resource_url)
        self.assertEqual(response.status_code, 403)

    def test_timestamp(self):
        """ Tests that botocore returns right timestamp """
        def replace_seconds(dtime):
            """ Replace seconds and microseconds for datetime object"""
            return dtime.replace(second=0).replace(microsecond=0)

        signed_url = form_cloudfront_url(self.resource_url)
        timestamp = replace_seconds(datetime.datetime.now() + datetime.timedelta(minutes=10))

        parsed_url = urlparse(signed_url)
        query_params = parse_qs(parsed_url.query)
        expiration_date = replace_seconds(datetime.datetime.fromtimestamp(int(query_params.get('Expires')[0])))

        self.assertEqual(expiration_date, timestamp)

    @patch("util.custom_views.datetime")
    def test_url_expire(self, dt_mock):
        """ Tests that access is restricted after expiration time """
        dt_mock.timedelta.return_value = datetime.timedelta(seconds=3)
        dt_mock.datetime.now.return_value = datetime.datetime.now()
        signed_url = form_cloudfront_url(self.resource_url)

        response = requests.get(signed_url)
        self.assertEqual(response.status_code, 200)

        time.sleep(3)

        response = requests.get(signed_url)
        self.assertEqual(response.status_code, 403)


    @patch("builtins.open", mock_open(read_data=
        """
        -----BEGIN RSA PRIVATE KEY-----
        notvalidkey
        -----END RSA PRIVATE KEY-----
        """
    ))
    def test_broken_key(self):
        """ Tests that URL can't be signed if broken signing key is provided """
        signed_url = form_cloudfront_url(self.resource_url)
        self.assertEqual(signed_url, "")
