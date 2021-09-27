"""
Utils for CourseOverview.
"""

import logging

from datetime import datetime
from pytz import UTC
from django.conf import settings

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


log = logging.getLogger(__name__)


def get_course_lang_from_number(course_number):
    """
    Parse course number to get course language.

    Expecting that language suffix placed at the end of the number string.

    Args:
        course_number (str): course number (display_number_with_default).

    Returns:
        str: language name (localized).
    """
    split_num = course_number.split('-')
    course_lang = len(split_num) > 1 and settings.LANGUAGE_DICT_EXTENDED.get(str(split_num[-1]).lower())
    return course_lang if course_lang else 'English'


def clean_course_number_from_lang_suffix(course_number):
    """
    Get course number cleaned from language prefix.

    Expecting that language suffix placed at the end of the number string.

    Args:
        course_number (str): course number (display_number_with_default).

    Returns:
        str: cleaned course number
    """
    split_num = course_number.split('-')
    has_lang_suffix = len(split_num) > 1 and settings.ALL_LANGUAGES_DICT.get(str(split_num[-1]).lower())
    return '-'.join(split_num[:-1]) if has_lang_suffix else '-'.join(split_num)


def get_course_language_options(course):
    """
    Find similar courses available in different languages.

    Expecting that language suffix placed at the end of the number string.
    Duplicated languages are skipped.

    Args:
        course (CourseOverview): CourseOverview object.

    Returns:
        dict: available language options in format {language(str): course_id(str), ...}
    """
    number = clean_course_number_from_lang_suffix(course.display_number_with_default)
    result = {}
    lang_options_courses = CourseOverview.objects.filter(
        org=course.org,
        display_number_with_default__contains=number,
    ).exclude(
        id=course.id
    )
    if is_enrollment_open(course):
        course_lang = get_course_lang_from_number(course.display_number_with_default)
        result[course_lang] = str(course.id)

    for course_option in lang_options_courses:
        enrollment_open = is_enrollment_open(course)
        course_number = course_option.display_number_with_default
        if enrollment_open and (course_number.startswith(number + '-') or course_number == number):
            option_lang = get_course_lang_from_number(course_number)
            if result.get(option_lang):
                log.warning(
                    'Found duplicate language option [%s]. Please, check courses %s and '
                    '%s in the studio.' % (option_lang, str(course_option.id), result[option_lang])
                )
            else:
                result[option_lang] = str(course_option.id)

    return result


def is_enrollment_open(course):
    """
    Check whether enrollment is open for the course

    Args:
        course (CourseOverview): CourseOverview object.

    Returns:
        bool: indicates if enrollment is open
    """
    now = datetime.now(UTC)
    enrollment_start = course.enrollment_start or datetime.min.replace(tzinfo=UTC)
    enrollment_end = course.enrollment_end or datetime.max.replace(tzinfo=UTC)
    return enrollment_start <= now <= enrollment_end
