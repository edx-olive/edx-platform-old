"""Utility functions that have to do with the courseware."""


import datetime
import logging

import six
from course_modes.models import CourseMode
from django.conf import settings
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from pytz import utc
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID
from xmodule.partitions.partitions_service import PartitionService

from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.content.block_structure.exceptions import BlockStructureNotFound
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference

log = logging.getLogger(__name__)


def verified_upgrade_deadline_link(user, course=None, course_id=None):
    """
    Format the correct verified upgrade link for the specified ``user``
    in a course.

    One of ``course`` or ``course_id`` must be supplied. If both are specified,
    ``course`` will take priority.

    Arguments:
        user (:class:`~django.contrib.auth.models.User`): The user to display
            the link for.
        course (:class:`.CourseOverview`): The course to render a link for.
        course_id (:class:`.CourseKey`): The course_id of the course to render for.

    Returns:
        The formatted link that will allow the user to upgrade to verified
        in this course.
    """
    if course is not None:
        course_id = course.id
    return EcommerceService().upgrade_url(user, course_id)


def can_show_verified_upgrade(user, enrollment, course=None):
    """
    Return whether this user can be shown upgrade message.

    Arguments:
        user (:class:`.AuthUser`): The user from the request.user property
        enrollment (:class:`.CourseEnrollment`): The enrollment under consideration.
            If None, then the enrollment is considered to be upgradeable.
        course (:class:`.ModulestoreCourse`): Optional passed in modulestore course.
            If provided, it is expected to correspond to `enrollment.course.id`.
            If not provided, the course will be loaded from the modulestore.
            We use the course to retrieve user partitions when calculating whether
            the upgrade link will be shown.
    """
    # Return `true` if user is not enrolled in course
    if enrollment is None:
        return False
    partition_service = PartitionService(enrollment.course.id, course=course)
    enrollment_track_partition = partition_service.get_user_partition(ENROLLMENT_TRACK_PARTITION_ID)
    group = partition_service.get_group(user, enrollment_track_partition)
    current_mode = None
    if group:
        try:
            current_mode = [
                mode.get('slug') for mode in settings.COURSE_ENROLLMENT_MODES.values() if mode['id'] == group.id
            ].pop()
        except IndexError:
            pass
    upgradable_mode = not current_mode or current_mode in CourseMode.UPSELL_TO_VERIFIED_MODES

    if not upgradable_mode:
        return False

    upgrade_deadline = enrollment.upgrade_deadline

    if upgrade_deadline is None:
        return False

    if datetime.datetime.now(utc).date() > upgrade_deadline.date():
        return False

    # Show the summary if user enrollment is in which allow user to upsell
    return enrollment.is_active and enrollment.mode in CourseMode.UPSELL_TO_VERIFIED_MODES


def get_video_library_blocks(request, requested_fields=['type', 'display_name']):
    """
    Get the list of all video blocks from the video library course.

    Args:
        request: django request
        requested_fields (list, optional): Indicates which additional fields to return for each block.
            Supported fields are listed in transformers.SUPPORTED_FIELDS. Defaults to ['type', 'display_name'].

    Returns:
        list: List of dicts with video blocks data in following format (default requested_fields):
        [
            {'id': 'block-v1:00+00+00+type@video+block@5e01125c2b3944448fd0712aacd086f0',
            'lms_web_url': 'http://localhost:18000/courses/course-v1:00+00+00/jump_to/block-v1:00+00+00+type@video+block@5e01125c2b3944448fd0712aacd086f0',
            'type': 'video',
            'display_name': '',
            'student_view_url': 'http://localhost:18000/xblock/block-v1:00+00+00+type@video+block@5e01125c2b3944448fd0712aacd086f0',
            'block_id': '5e01125c2b3944448fd0712aacd086f0'}
        ]
    """
    # Import here to avoid cilic import
    from lms.djangoapps.course_api.blocks.api import get_blocks
    video_library_id = getattr(settings, 'VIDEO_LIBRARY_COURSE', '')
    try:
        library_usage_key = modulestore().make_course_usage_key(CourseKey.from_string(video_library_id))
        return get_blocks(
            request,
            library_usage_key,
            requested_fields=requested_fields,
            block_types_filter=['video'],
            return_type='list'
        )
    except (InvalidKeyError, BlockStructureNotFound, ItemNotFoundError):
        log.warning(
            "Failed to get course blocks for library id [{}]. "
            "Please, check that VIDEO_LIBRARY_COURSE setting was set correctly.".format(video_library_id)
        )
        return []


def get_video_library_blocks_no_request():
    """
    Get the list of all video blocks from the video library course.

    Unlike the 1st version, doesn't use request.

    Returns:
        list with dicts in format:
        [
            {'name': 'Library vid unit2 #1', 'id': 'block-v1:00+00+00+type@video+block@1974e9f1ff584bf9a7f1d3a272570a8d'},
            {'name': 'Test video from the library', 'id': 'block-v1:00+00+00+type@video+block@5e01125c2b3944448fd0712aacd086f0'},
            {'name': 'Library video #2', 'id': 'block-v1:00+00+00+type@video+block@deb8aa5796f3445391ff0d7326b2ab7d'}
        ]
    """
    video_library_id = getattr(settings, 'VIDEO_LIBRARY_COURSE', '')
    try:
        library_key = CourseKey.from_string(video_library_id)
        block_structure = get_course_in_cache(library_key)
    except (InvalidKeyError, BlockStructureNotFound, ItemNotFoundError):
        log.warning(
            "Failed to get course blocks for library id [{}]. "
            "Please, check that VIDEO_LIBRARY_COURSE setting was set correctly.".format(video_library_id)
        )
        return []

    library = []
    for block_key in block_structure:
        block_type = block_structure.get_xblock_field(block_key, 'category')
        if block_type == 'video':
            library.append(
                {'id': six.text_type(block_key), 'name': block_structure.get_xblock_field(block_key, 'display_name')}
            )

    return library

def check_user_prefered_language_available_for_enroll(request, options, default='English'):
    """
    Check if any of user language preferences suits any available enroll option.

    The LanguageProficiency has a priority over UserPreference.

    Args:
        request (Request): Django request;
        options (dict): enrollment options e.g. {language(str): course_id(str), ...};
        default (str): the default to return if there are no suitable language.

    Returns:
        str: language full name (localized) or default value
    """
    lang_pref = None
    lang_available = False

    lang_pref_code = request.user.profile.language_proficiencies.first()
    if lang_pref_code:
        lang_pref = settings.LANGUAGE_DICT.get(lang_pref_code.code)
        lang_available = bool(options.get(lang_pref))

    if not lang_pref_code or not lang_available:
        lang_pref_code = get_user_preference(request.user, LANGUAGE_KEY)
        lang_pref = settings.LANGUAGE_DICT.get(lang_pref_code)
        lang_available = bool(options.get(lang_pref))

    return lang_pref if lang_pref and lang_available else default
