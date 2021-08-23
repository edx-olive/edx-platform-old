"""
Management command `get_registration` returns "is registered:<email>" or "not registered:<email>"
/edx/app/edxapp/edx-platform/cms/djangoapps/contentstore/management/commands
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Prints user_id if the user exists, email address if not'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, email, *args, **options):
        try:
            user = get_user_model().objects.get(email=email).username
            print("is registered:{0}".format(email))
        except Exception:
            print("not registered:{0}".format(email))
