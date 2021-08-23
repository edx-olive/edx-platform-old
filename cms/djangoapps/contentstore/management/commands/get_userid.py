"""
Management command `get_userid` returns user_id if the user exists, blank if not.
/edx/app/edxapp/edx-platform/cms/djangoapps/contentstore/management/commands
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Prints user_id if the user exists, blank if not'

    def add_arguments(self, parser):
        parser.add_argument('email')

    def handle(self, email, *args, **options):
        try:
            user = get_user_model().objects.get(email=email).username
            print("{0}".format(user))
        except Exception:
            print("")
