"""
Helper methods for Studio views.
"""

from __future__ import absolute_import

import urllib
from uuid import uuid4

from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock

import dogstats_wrapper as dog_stats_api
from contentstore.utils import reverse_course_url, reverse_library_url, reverse_usage_url
from edxmako.shortcuts import render_to_string
from models.settings.course_grading import CourseGradingModel
from util.milestones_helpers import is_entrance_exams_enabled
from xmodule.modulestore.django import modulestore
from xmodule.tabs import StaticTab, VideoTab
from xmodule.x_module import DEPRECATION_VSCOMPAT_EVENT

__all__ = ['event']

# Note: Grader types are used throughout the platform but most usages are simply in-line
# strings.  In addition, new grader types can be defined on the fly anytime one is needed
# (because they're just strings). This dict is an attempt to constrain the sprawl in Studio.
GRADER_TYPES = {
    "HOMEWORK": "Homework",
    "LAB": "Lab",
    "ENTRANCE_EXAM": "Entrance Exam",
    "MIDTERM_EXAM": "Midterm Exam",
    "FINAL_EXAM": "Final Exam"
}

# The data is very specific to AMAT.
CUSTOM_VIDEO_METADATA = {
        "html5_sources":
            [
                # Custom AMAT video: Gary's Welcome
                "https://d2a8rd6kt4zb64.cloudfront.net/course-v1_Appliedx_AX001_Self-Paced/Appliedx_Gary-Promo_edit3(720p)HB2.mp4",
            ],
        "youtube_id_1_0": "",
    }
CUSTOM_STATIC_TAB_DISPLAY_NAME = "Learning on appliedx"


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def get_parent_xblock(xblock):
    """
    Returns the xblock that is the parent of the specified xblock, or None if it has no parent.
    """
    locator = xblock.location
    parent_location = modulestore().get_parent_location(locator)

    if parent_location is None:
        return None
    return modulestore().get_item(parent_location)


def is_unit(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock is a vertical that is treated as a unit.
    A unit is a vertical that is a direct child of a sequential (aka a subsection).
    """
    if xblock.category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        parent_category = parent_xblock.category if parent_xblock else None
        return parent_category == 'sequential'
    return False


def xblock_has_own_studio_page(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock has an associated Studio page. Most xblocks do
    not have their own page but are instead shown on the page of their parent. There
    are a few exceptions:
      1. Courses
      2. Verticals that are either:
        - themselves treated as units
        - a direct child of a unit
      3. XBlocks that support children
    """
    category = xblock.category

    if is_unit(xblock, parent_xblock):
        return True
    elif category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        return is_unit(parent_xblock) if parent_xblock else False

    # All other xblocks with children have their own page
    return xblock.has_children


def xblock_studio_url(xblock, parent_xblock=None):
    """
    Returns the Studio editing URL for the specified xblock.
    """
    if not xblock_has_own_studio_page(xblock, parent_xblock):
        return None
    category = xblock.category
    if category == 'course':
        return reverse_course_url('course_handler', xblock.location.course_key)
    elif category in ('chapter', 'sequential'):
        return u'{url}?show={usage_key}'.format(
            url=reverse_course_url('course_handler', xblock.location.course_key),
            usage_key=urllib.quote(unicode(xblock.location))
        )
    elif category == 'library':
        library_key = xblock.location.course_key
        return reverse_library_url('library_handler', library_key)
    else:
        return reverse_usage_url('container_handler', xblock.location)


def xblock_type_display_name(xblock, default_display_name=None):
    """
    Returns the display name for the specified type of xblock. Note that an instance can be passed in
    for context dependent names, e.g. a vertical beneath a sequential is a Unit.

    :param xblock: An xblock instance or the type of xblock.
    :param default_display_name: The default value to return if no display name can be found.
    :return:
    """

    if hasattr(xblock, 'category'):
        category = xblock.category
        if category == 'vertical' and not is_unit(xblock):
            return _('Vertical')
    else:
        category = xblock
    if category == 'chapter':
        return _('Section')
    elif category == 'sequential':
        return _('Subsection')
    elif category == 'vertical':
        return _('Unit')
    component_class = XBlock.load_class(category, select=settings.XBLOCK_SELECT_FUNCTION)
    if hasattr(component_class, 'display_name') and component_class.display_name.default:
        return _(component_class.display_name.default)    # pylint: disable=translation-of-non-string
    else:
        return default_display_name


def xblock_primary_child_category(xblock):
    """
    Returns the primary child category for the specified xblock, or None if there is not a primary category.
    """
    category = xblock.category
    if category == 'course':
        return 'chapter'
    elif category == 'chapter':
        return 'sequential'
    elif category == 'sequential':
        return 'vertical'
    return None


def usage_key_with_run(usage_key_string):
    """
    Converts usage_key_string to a UsageKey, adding a course run if necessary
    """
    usage_key = UsageKey.from_string(usage_key_string)
    usage_key = usage_key.replace(course_key=modulestore().fill_in_run(usage_key.course_key))
    return usage_key


def remove_entrance_exam_graders(course_key, user):
    """
    Removes existing entrance exam graders attached to the specified course
    Typically used when adding/removing an entrance exam.
    """
    grading_model = CourseGradingModel.fetch(course_key)
    graders = grading_model.graders
    for i, grader in enumerate(graders):
        if grader['type'] == GRADER_TYPES['ENTRANCE_EXAM']:
            CourseGradingModel.delete_grader(course_key, i, user)


def create_xblock(parent_locator, user, category, display_name, boilerplate=None, is_entrance_exam=False, is_video_tab=False, update_custom_tabs_order=False):
    """
    Performs the actual grunt work of creating items/xblocks -- knows nothing about requests, views, etc.

    AMAT customization:
        is_video_tab (bool): indication that a custom video static tab (`VideoTab` obj)
            should be created.
        update_custom_tabs_order (bool): indication to reorder course tabs accordingly to
            the specific AMAT rules.
    """
    store = modulestore()
    usage_key = usage_key_with_run(parent_locator)
    with store.bulk_operations(usage_key.course_key):
        parent = store.get_item(usage_key)
        dest_usage_key = usage_key.replace(category=category, name=uuid4().hex)

        # get the metadata, display_name, and definition from the caller
        metadata = {}
        data = None
        template_id = boilerplate
        if template_id:
            clz = parent.runtime.load_block_type(category)
            if clz is not None:
                template = clz.get_template(template_id)
                if template is not None:
                    metadata = template.get('metadata', {})
                    data = template.get('data')

        if display_name is not None:
            metadata['display_name'] = display_name

        # We should use the 'fields' kwarg for newer module settings/values (vs. metadata or data)
        fields = {}

        # Entrance Exams: Chapter module positioning
        child_position = None
        if is_entrance_exams_enabled():
            if category == 'chapter' and is_entrance_exam:
                fields['is_entrance_exam'] = is_entrance_exam
                fields['in_entrance_exam'] = True  # Inherited metadata, all children will have it
                child_position = 0

        if category == 'video' and is_video_tab:
            fields['hide_from_courseware'] = True

        # TODO need to fix components that are sending definition_data as strings, instead of as dicts
        # For now, migrate them into dicts here.
        if isinstance(data, basestring):
            data = {'data': data}

        created_block = store.create_child(
            user.id,
            usage_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            fields=fields,
            definition_data=data,
            metadata=metadata,
            runtime=parent.runtime,
            position=child_position,
        )

        # Entrance Exams: Grader assignment
        if is_entrance_exams_enabled():
            course_key = usage_key.course_key
            course = store.get_course(course_key)
            if hasattr(course, 'entrance_exam_enabled') and course.entrance_exam_enabled:
                if category == 'sequential' and parent_locator == course.entrance_exam_id:
                    # Clean up any pre-existing entrance exam graders
                    remove_entrance_exam_graders(course_key, user)
                    grader = {
                        "type": GRADER_TYPES['ENTRANCE_EXAM'],
                        "min_count": 0,
                        "drop_count": 0,
                        "short_label": "Entrance",
                        "weight": 0
                    }
                    grading_model = CourseGradingModel.update_grader_from_json(
                        course.id,
                        grader,
                        user
                    )
                    CourseGradingModel.update_section_grader_type(
                        created_block,
                        grading_model['type'],
                        user
                    )

        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if category == 'static_tab' or category == 'video' and is_video_tab:

            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=(
                    "location:create_xblock_static_tab",
                    u"course:{}".format(unicode(dest_usage_key.course_key)),
                )
            )

            display_name = display_name or _("Empty")  # Prevent name being None
            course = store.get_course(dest_usage_key.course_key)
            if category == 'static_tab':
                if update_custom_tabs_order:
                    static_tab = StaticTab(
                        name=display_name,
                        url_slug=dest_usage_key.name,
                    )
                    _update_custom_tabs_order(course, static_tab)
                else:
                    course.tabs.append(
                        StaticTab(
                            name=display_name,
                            url_slug=dest_usage_key.name,
                        )
                    )
            elif category == 'video' and is_video_tab:
                course.tabs.append(
                    VideoTab(
                        name=display_name,
                        url_slug=dest_usage_key.name,
                    )
                )
            store.update_item(course, user.id)

        return created_block


def _update_custom_tabs_order(course, static_tab):
    """
    Place a new static_tab in course tabs.

    Placement should happen in accordance with the specific order rules:
    - page location: after "About the Course" page;
    - add the page only if doesn't exist already.
    """
    original_tabs = course.tabs[:]
    course_names = [tab["name"] for tab in course.tabs]
    if CUSTOM_STATIC_TAB_DISPLAY_NAME in course_names:
        return

    # "About the Course" element follows the "Progress" page and is not a static tab per se,
    # see `lms/templates/courseware/tabs.html`.
    new_tab_order_i = None
    for i, tab in enumerate(course.tabs):
        if tab.name == "Progress":
            new_tab_order_i = i + 1
            break

    # Go ahead if there is a "Progress" page in the course pages list
    if new_tab_order_i is not None:

        # Check if there are tabs after the "Progress" page
        if len(course.tabs) >= new_tab_order_i - 1:

            try:
                course.tabs = course.tabs[:new_tab_order_i]
                course.tabs.append(static_tab)

                # Append the remaining tabs, preserving sequence
                for j, tab in enumerate(original_tabs[new_tab_order_i:]):
                    course.tabs.append(tab)

            except IndexError as e:
                raise Exception(
                    "IndexError happened when trying to create "
                    "a custom AMAT static tab: {!s}".format(
                        e,
                    )
                )

        else:
            course.tabs.append(static_tab)


def is_item_in_course_tree(item):
    """
    Check that the item is in the course tree.

    It's possible that the item is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = item.get_parent()
    while ancestor is not None and ancestor.location.category != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None
