"""
Custom AMAT utils for AWS / CloudFront.
"""
import json
import logging
import os
import time

import boto
from boto.exception import NoAuthHandlerFound
from django.conf import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# TODO: DRY (use this util in `custom_views.py` and `video_module.py`)
def get_signed_cloudfront_url(url):
    """
    Sign AWS CloudFront url.

    Arguments:
        url (str):

    Returns:
        signed url (str) | None
    """
    aws_access_key_id = settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
    if aws_access_key_id and aws_secret_access_key:
        try:
            # TODO consider creating clients w/ various exceptions handling
            boto.connect_s3(aws_access_key_id, aws_secret_access_key)
            cf = boto.connect_cloudfront(aws_access_key_id, aws_secret_access_key)
            key_pair_id = settings.CLOUDFRONT_SIGNING_KEY_ID
            priv_key_file = settings.CLOUDFRONT_SIGNING_KEY_FILE
            expires = int(time.time()) + 600
            dist = cf.get_all_distributions()[0].get_distribution()
            if key_pair_id and priv_key_file:
                signed_url = dist.create_signed_url(url, key_pair_id, expires, private_key_file=priv_key_file)
                return signed_url
        except NoAuthHandlerFound:
            logger.error("Failed to sign CloudFront url {!s}.".format(url))
