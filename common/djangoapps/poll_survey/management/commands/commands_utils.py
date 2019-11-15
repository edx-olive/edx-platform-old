"""Convenient functionality for `poll_survey` management commands."""

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.models import StudentModule


class UserService(object):
    """Service logic to manipulate `User` model."""

    @staticmethod
    def get_user(user_id):
        """
        Get a user entry.

        Returns:
            result (`User` obj | None): None if none found,
               object itself if found.
        """
        try:
            return User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return None


class UserSocialAuthService(object):
    """
    Service logic to manipulate `UserSocialAuth` model.
    """

    @staticmethod
    def get_user_social_auth_entry(user):
        """
        Get a user entry.

        Arguments:
            user (`User` obj): user model.
        Returns:
            result (`UserSocialAuth` obj | None): None if none found,
               object itself if found.
        """
        try:
            return user.social_auth.get(provider='tpa-saml')
        except ObjectDoesNotExist:
            return None


def get_comma_separated_args(option, opt, value, parser):
    """Parse command comma-separated argument to a list of long values."""
    try:
        setattr(parser.values, option.dest, [long(v) for v in value.split(",")])
    except ValueError:
        setattr(parser.values, option.dest, value.split(","))


def prepare_submissions_entries(
        module_type,
        submission_date_to,
        from_pk=1,
        exclude_ids=None,
        courses_ids=None,
        offset=0,
        chunk_size=2000):
    """Fetch submissions entries."""

    if exclude_ids:
        print("Fetching {!s} xblock submissions starting from pk {!s} (if there are any), "
              "excluding the next ids: {!s}..."
              .format(module_type, from_pk, exclude_ids))
        if courses_ids:
            return StudentModule.objects.filter(
                    pk__gte=from_pk,
                    created__lte=submission_date_to,
                    course_id__in=courses_ids,
                    module_type=module_type).exclude(id__in=exclude_ids)[offset:chunk_size+offset]
        else:
            return StudentModule.objects.filter(
                    pk__gte=from_pk,
                    created__lte=submission_date_to,
                    module_type=module_type).exclude(id__in=exclude_ids)[offset:chunk_size+offset]
    else:
        print("Fetching {!s} xblock submissions starting from pk {!s} (if there are any)..."
              .format(module_type, from_pk))
        if courses_ids:
            return StudentModule.objects.filter(
                pk__gte=from_pk,
                created__lte=submission_date_to,
                course_id__in=courses_ids,
                module_type=module_type)[offset:chunk_size+offset]
        else:
            return StudentModule.objects.filter(
                pk__gte=from_pk,
                created__lte=submission_date_to,
                module_type=module_type)[offset:chunk_size+offset]


def fetch_xblock(module_state_key):
    """Fetch an xblock from the modulestore."""

    xblock = None
    store = modulestore()
    try:
        # Xblock will provide questions/answers text information.
        xblock = store.get_item(module_state_key)
        print("XBlock component has been found: {!s}.".format(module_state_key))
    except ItemNotFoundError:
        # If xblock is not found, we won't persist its submissions
        # since there is no available questions/answers text
        # to recognize particular surveys.
        print("XBlock {!s} must have been removed from the courseware. "
              "Won't persist its submissions.".format(module_state_key))
    return xblock


def get_employee_id(user):
    """
    Get PingSSO employee id.
    """

    social = UserSocialAuthService.get_user_social_auth_entry(user)
    if social and getattr(social, "uid", None):
        return social.uid.split(':')[1] if ":" in social.uid else None
