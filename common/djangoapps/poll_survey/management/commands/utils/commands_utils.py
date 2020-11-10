"""Convenient functionality for `poll_survey` management commands."""

import os
import json

from django.conf import settings
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
            return user.social_auth.filter(provider='tpa-saml').last()
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
    """Fetch xblock submissions entries."""

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


class HardcodedSurveyXblock(object):
    """
    Hardcoded survey/poll xBlock data.

    Support a specific case AMATX-526.
    """
    def __init__(self, block_id, answers, block_name, questions=None, question=None):
        self.block_id = block_id  # Added for information
        self.answers = answers
        self.block_name = block_name  # XBlock title
        self.questions = questions  # Surveys
        self.question = question # Rating poll


def fetch_hardcoded_xblock(module_state_key):
    """
    Fetch an xblock from hardcoded data.

    Support a specific case AMATX-526.

    Survey questions and answers  should be hardcoded like real xblock's
    (`xblock.internal.SurveyBlockWithMixins` obj):
    ```
    (Pdb) xblock.answers
    [[u'8', u'aaaaaa'], [u'9', u'aaaa2']]
    (Pdb) xblock.questions
    [[u'6', {u'img': u'', u'img_alt': u'', u'label': u'qqqqq'}],]
    ```
    """
    xblock = None

    # Open and process the file for every xblock component, for the sake of code simplicity.
    # We don't have a lot of data anyway.
    with open(os.path.join(
        settings.COMMON_ROOT,
        # Hardcoded xblock structures and definitions taken from the DEV modulestore dump
        "djangoapps/poll_survey/management/commands/resources/amatx_526_xblocks_dev.json"
    )) as f:
        surveys = json.load(f)
        for survey in surveys:
            # Stored in modulestore.structures
            org = survey.get("org", "PDE1")
            run = survey.get("run", "Anytime")
            course = survey.get("course", "217")
            block_id = survey.get("block_id")
            questions = survey.get("questions")
            answers = survey.get("answers")
            # Stored in modulestore.definitions
            block_name = survey.get("block_name")

            if (
                block_id == module_state_key.html_id()
                and course == module_state_key.course
                and org == module_state_key.org
                and run == module_state_key.run
            ):
                xblock = HardcodedSurveyXblock(
                    block_id=block_id,
                    answers=answers,
                    block_name=block_name,
                    questions=questions,
                )
                break

    if xblock:
        print("XBlock component has been found: {!s}.".format(module_state_key))
    else:
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
