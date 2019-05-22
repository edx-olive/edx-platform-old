"""
Course API Serializers.  Representing course catalog data
"""

import urllib
import ast
import json
import requests

from django.core.urlresolvers import reverse
from django.conf import settings
from rest_framework import serializers

from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.lib.api.fields import AbsoluteURLField

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class _MediaSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a media object.
    """

    def __init__(self, uri_attribute, *args, **kwargs):
        super(_MediaSerializer, self).__init__(*args, **kwargs)
        self.uri_attribute = uri_attribute

    uri = serializers.SerializerMethodField(source='*')

    def get_uri(self, course_overview):
        """
        Get the representation for the media resource's URI
        """
        return getattr(course_overview, self.uri_attribute)


class ImageSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Collection of URLs pointing to images of various sizes.

    The URLs will be absolute URLs with the host set to the host of the current request. If the values to be
    serialized are already absolute URLs, they will be unchanged.
    """
    raw = AbsoluteURLField()
    small = AbsoluteURLField()
    large = AbsoluteURLField()


class _CourseApiMediaCollectionSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Nested serializer to represent a collection of media objects
    """
    course_image = _MediaSerializer(source='*', uri_attribute='course_image_url')
    course_video = _MediaSerializer(source='*', uri_attribute='course_video_url')
    image = ImageSerializer(source='image_urls')


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing minimal data about the course.
    Compare this with CourseDetailSerializer.
    """

    blocks_url = serializers.SerializerMethodField()
    effort = serializers.CharField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()
    id = serializers.CharField()  # pylint: disable=invalid-name
    media = _CourseApiMediaCollectionSerializer(source='*')
    name = serializers.CharField(source='display_name_with_default_escaped')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    short_description = serializers.CharField()
    start = serializers.DateTimeField()
    start_display = serializers.CharField()
    start_type = serializers.CharField()
    pacing = serializers.CharField()
    mobile_available = serializers.BooleanField()
    hidden = serializers.SerializerMethodField()
    invitation_only = serializers.BooleanField()

    # 'course_id' is a deprecated field, please use 'id' instead.
    course_id = serializers.CharField(source='id', read_only=True)

    def get_hidden(self, course_overview):
        """
        Get the representation for SerializerMethodField `hidden`
        Represents whether course is hidden in LMS
        """
        catalog_visibility = course_overview.catalog_visibility
        return catalog_visibility in ['about', 'none']

    def get_blocks_url(self, course_overview):
        """
        Get the representation for SerializerMethodField `blocks_url`
        """
        base_url = '?'.join([
            reverse('blocks_in_course'),
            urllib.urlencode({'course_id': course_overview.id}),
        ])
        return self.context['request'].build_absolute_uri(base_url)


class CourseDetailSerializer(CourseSerializer):  # pylint: disable=abstract-method
    """
    Serializer for Course objects providing additional details about the
    course.

    This serializer makes additional database accesses (to the modulestore) and
    returns more data (including 'overview' text). Therefore, for performance
    and bandwidth reasons, it is expected that this serializer is used only
    when serializing a single course, and not for serializing a list of
    courses.
    """

    overview = serializers.SerializerMethodField()
    appliedx_mobile_available =  serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    vr_enabled = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    streams = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    objectives = serializers.SerializerMethodField()
    course_prerequisites = serializers.SerializerMethodField()
    instructors = serializers.SerializerMethodField()
    instructor_designers = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    standard = serializers.SerializerMethodField()
    enrollment_url = serializers.SerializerMethodField()

    def get_overview(self, course_overview):
        """
        Get the representation for SerializerMethodField `overview`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        return CourseDetails.fetch_about_attribute(course_overview.id, 'overview')

# Extra details appliedx customs

    def get_verified(self, course_overview):
        """
        Get the representation for SerializerMethodField `verified`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        verified = CourseDetails.fetch_about_attribute(course_overview.id, 'verified')
        if verified == "true":
            return True
        else:
            return False

    def get_vr_enabled(self, course_overview):
        """
        Get the representation for SerializerMethodField `vr_enabled`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        vr_enabled = CourseDetails.fetch_about_attribute(course_overview.id, 'vr_enabled')
        if vr_enabled == "true":
            return True
        else:
            return False

    def get_level(self, course_overview):
        """
        Get the representation for SerializerMethodField `level`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            level = CourseDetails.fetch_about_attribute(course_overview.id, 'level')
            return level if level != '' else None
        except:
            return None

    def get_streams(self, course_overview):
        """
        Get the representation for SerializerMethodField `stream`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            streams = CourseDetails.fetch_about_attribute(course_overview.id, 'streams')
            if streams not in ['[]', None]:
                return ast.literal_eval(streams)
            else:
                return None
        except:
            return None

    def get_tags(self, course_overview):
        """
        Get the representation for SerializerMethodField `tags`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            tags = CourseDetails.fetch_about_attribute(course_overview.id, 'tags')
            if tags not in ['[]', None]:
                return ast.literal_eval(tags)
            else:
                return None
        except:
            return None

    def get_objectives(self, course_overview):
        """
        Get the representation for SerializerMethodField `objectives`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            objectives = CourseDetails.fetch_about_attribute(course_overview.id, 'objectives').encode('ascii','ignore')
            return ast.literal_eval(objectives) if objectives not in ['[]', None] else None
        except:
            return None

    def get_course_prerequisites(self, course_overview):
        """
        Get the representation for SerializerMethodField `prerequisites`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            course_prerequisites = CourseDetails.fetch_about_attribute(course_overview.id, 'course_prerequisites').encode('ascii','ignore')
            return ast.literal_eval(course_prerequisites) if course_prerequisites not in ['[]', None] else None
        except:
            return None

    def get_instructors(self, course_overview):
        """
        Get the representation for SerializerMethodField `instructor`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            instructors_raw = CourseDetails.fetch_about_attribute(course_overview.id, 'instructors')
            if len(instructors_raw) > 0:
                instructors = ast.literal_eval(instructors_raw)
                instructor_list = []
                null = None
                for instructor in instructors:
                    instructor_dict = {}
                    req = requests.get('https://services.appliedx.amat.com/appliedx_controls/instructor_details?name='+instructor, verify=False)
                    #response = eval(req.text)[0]
                    #instructor_dict['name'] = response['name'] if response['name'] is not '' else None
                    #instructor_dict['image_url'] = response['image_url'] if response['image_url'] is not '' else None
                    #instructor_dict['description'] = response['description'] if response['description'] is not '' else None
                    instructor_list.append(json.loads(req.text)[0])
                return instructor_list
            else:
                return None
        except:
            return None

    def get_instructor_designers(self, course_overview):
        """
        Get the representation for SerializerMethodField `instructor_designers`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            instructor_designers_raw = CourseDetails.fetch_about_attribute(course_overview.id, 'instructor_designers')
            if len(instructor_designers_raw) > 0:
                instructor_designers = ast.literal_eval(CourseDetails.fetch_about_attribute(course_overview.id, 'instructor_designers'))
                instructor_designer_list = []
                null = None
                for instructor_designer in instructor_designers:
                    instructor_designer_dict = {}
                    req = requests.get('https://services.appliedx.amat.com/appliedx_controls/instructor_details?name='+instructor_designer, verify=False)
                    response = eval(req.text)[0]
                    #instructor_designer_dict['name'] = response['name'] if response['name'] is not '' else None
                    #instructor_designer_dict['image_url'] = response['image_url'] if response['image_url'] is not '' else None
                    #instructor_designer_dict['description'] = response['description'] if response['description'] is not '' else None
                    #instructor_designer_list.append(instructor_designer_dict)
                    instructor_designer_list.append(json.loads(req.text)[0])
                return instructor_designer_list
            else:
                return None
        except:
            return None

    def get_price(self, course_overview):
        """
        Get the representation for SerializerMethodField `price`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            price = CourseDetails.fetch_about_attribute(course_overview.id, 'price')
            return price if price not in ['', None] else None
        except:
            return None

    def get_standard(self, course_overview):
        """
        Get the representation for SerializerMethodField `standard`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            standard = CourseDetails.fetch_about_attribute(course_overview.id, 'standard')
            return standard if standard not in ['', None] else None
        except:
            return None

    def get_enrollment_url(self,course_overview):
        """
        Get the representation for SerializerMethodField `enrollment_url`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        course_about = reverse('about_course',args=[course_overview.id.to_deprecated_string()])
        url = 'https://'+settings.SITE_NAME+course_about
        return url

    def get_appliedx_mobile_available(self, course_overview):
        """
        Get the representation for SerializerMethodField `appliedx_mobile_available`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        appliedx_mobile_available = CourseDetails.fetch_about_attribute(course_overview.id, 'mobile')
        if appliedx_mobile_available in ['Yes', 'YES', 'True', 'true', 'TRUE', 'yes']:
            return True
        else:
            return False


class AppliedXCourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method

    effort = serializers.CharField()
    end = serializers.DateTimeField()
    enrollment_start = serializers.DateTimeField()
    enrollment_end = serializers.DateTimeField()
    id = serializers.CharField()  # pylint: disable=invalid-name
    media = _CourseApiMediaCollectionSerializer(source='*')
    name = serializers.CharField(source='display_name_with_default_escaped')
    number = serializers.CharField(source='display_number_with_default')
    org = serializers.CharField(source='display_org_with_default')
    short_description = serializers.CharField()
    start = serializers.DateTimeField()
    start_display = serializers.CharField()
    start_type = serializers.CharField()
    pacing = serializers.CharField()
    mobile_available = serializers.BooleanField()
    invitation_only = serializers.BooleanField()
    appliedx_mobile_available =  serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    vr_enabled = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()
    streams = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    objectives = serializers.SerializerMethodField()
    course_prerequisites = serializers.SerializerMethodField()
    instructors = serializers.SerializerMethodField()
    instructor_designers = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    standard = serializers.SerializerMethodField()
    enrollment_url = serializers.SerializerMethodField()
    pathway = serializers.SerializerMethodField()
    availibility_status = serializers.SerializerMethodField()
    saba_details = serializers.SerializerMethodField()
    language = serializers.CharField()

    # 'course_id' is a deprecated field, please use 'id' instead.

    course_id = serializers.CharField(source='id', read_only=True)

    def get_verified(self, course_overview):
        """
        Get the representation for SerializerMethodField `verified`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            verified = CourseDetails.fetch_about_attribute(course_overview.id, 'verified')
            if verified == "true":
                return True
            else:
                return False
        except:
            return False

    def get_vr_enabled(self, course_overview):
        """
        Get the representation for SerializerMethodField `vr_enabled`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            vr_enabled = CourseDetails.fetch_about_attribute(course_overview.id, 'vr_enabled')
            if vr_enabled == "true":
                return True
            else:
                return False
        except:
            return False

    def get_level(self, course_overview):
        """
        Get the representation for SerializerMethodField `level`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            level = CourseDetails.fetch_about_attribute(course_overview.id, 'level')
            return level if level != '' else None
        except:
            return None

    def get_streams(self, course_overview):
        """
        Get the representation for SerializerMethodField `stream`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            streams = CourseDetails.fetch_about_attribute(course_overview.id, 'streams').encode('ascii','ignore')
            if streams not in ['[]', None]:
                return ast.literal_eval(streams)
            else:
                return None
        except:
            return None

    def get_tags(self, course_overview):
        """
        Get the representation for SerializerMethodField `tags`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            tags = CourseDetails.fetch_about_attribute(course_overview.id, 'tags').encode('ascii','ignore')
            if tags not in ['[]', None]:
                return ast.literal_eval(tags)
            else:
                return None
        except:
            return None

    def get_objectives(self, course_overview):
        """
        Get the representation for SerializerMethodField `objectives`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            objectives = CourseDetails.fetch_about_attribute(course_overview.id, 'objectives').encode('ascii','ignore')
            return ast.literal_eval(objectives) if objectives not in ['[]', None] else None
        except:
            return None

    def get_course_prerequisites(self, course_overview):
        """
        Get the representation for SerializerMethodField `prerequisites`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            course_prerequisites = CourseDetails.fetch_about_attribute(course_overview.id, 'course_prerequisites').encode('ascii','ignore')
            return ast.literal_eval(course_prerequisites) if course_prerequisites not in ['[]', None] else None
        except:
            return None

    def get_instructors(self, course_overview):
        """
        Get the representation for SerializerMethodField `instructor`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            instructors_raw = CourseDetails.fetch_about_attribute(course_overview.id, 'instructors')
            if len(instructors_raw) > 0:
                instructors = ast.literal_eval(instructors_raw)
                instructor_list = []
                null = None
                for instructor in instructors:
                    instructor_dict = {}
                    req = requests.get('https://services.appliedx.amat.com/appliedx_controls/instructor_details_plain?name='+instructor, verify=False)
                    #response = eval(req.text)[0]
                    #instructor_dict['name'] = response['name'] if response['name'] is not '' else None
                    #instructor_dict['image_url'] = response['image_url'] if response['image_url'] is not '' else None
                    #instructor_dict['description'] = response['description'] if response['description'] is not '' else None
                    instructor_list.append(json.loads(req.text)[0])
                return instructor_list
            else:
                return None
        except:
            return None

    def get_instructor_designers(self, course_overview):
        """
        Get the representation for SerializerMethodField `instructor_designers`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            instructor_designers_raw = CourseDetails.fetch_about_attribute(course_overview.id, 'instructor_designers')
            if len(instructor_designers_raw) > 0:
                instructor_designers = ast.literal_eval(CourseDetails.fetch_about_attribute(course_overview.id, 'instructor_designers'))
                instructor_designer_list = []
                null = None
                for instructor_designer in instructor_designers:
                    instructor_designer_dict = {}
                    req = requests.get('https://services.appliedx.amat.com/appliedx_controls/instructor_details_plain?name='+instructor_designer, verify=False)
                    #response = eval(req.text)[0]
                    #instructor_designer_dict['name'] = response['name'] if response['name'] is not '' else None
                    #instructor_designer_dict['image_url'] = response['image_url'] if response['image_url'] is not '' else None
                    #instructor_designer_dict['description'] = response['description'] if response['description'] is not '' else None
                    #instructor_designer_list.append(instructor_designer_dict)
                    instructor_designer_list.append(json.loads(req.text)[0])
                return instructor_designer_list
            else:
                return None
        except:
            return None

    def get_price(self, course_overview):
        """
        Get the representation for SerializerMethodField `price`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            price = CourseDetails.fetch_about_attribute(course_overview.id, 'price')
            return price if price not in ['', None] else None
        except:
            return None

    def get_standard(self, course_overview):
        """
        Get the representation for SerializerMethodField `standard`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            standard = CourseDetails.fetch_about_attribute(course_overview.id, 'standard')
            return standard if standard not in ['', None] else None
        except:
            return None

    def get_enrollment_url(self,course_overview):
        """
        Get the representation for SerializerMethodField `enrollment_url`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            course_about = reverse('about_course',args=[course_overview.id.to_deprecated_string()])
            url = 'https://'+settings.SITE_NAME+course_about
            return url
        except:
            return None

    def get_appliedx_mobile_available(self, course_overview):
        """
        Get the representation for SerializerMethodField `appliedx_mobile_available`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            appliedx_mobile_available = CourseDetails.fetch_about_attribute(course_overview.id, 'mobile')
            if appliedx_mobile_available in ['Yes', 'YES', 'True', 'true', 'TRUE', 'yes']:
                return True
            else:
                return False
        except:
            return False

    def get_pathway(self, course_overview):
        """
        Get the representation for SerializerMethodField `pathway`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            pathway = CourseDetails.fetch_about_attribute(course_overview.id, 'pathway')
            if pathway == 'true':
                pathway = True
            elif pathway == 'false':
                pathway = False
            return pathway if pathway != '' else None
        except:
            return None

    def get_availibility_status(self, course_overview):
        """
        Get the representation for SerializerMethodField `availibility_status`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            availibility_status = CourseDetails.fetch_about_attribute(course_overview.id, 'availibility_status')
            return availibility_status if availibility_status != '' else None
        except:
            return None

    def get_saba_details(self, course_overview):
        """
        Get the representation for SerializerMethodField `saba`
        """
        # Note: This makes a call to the modulestore, unlike the other
        # fields from CourseSerializer, which get their data
        # from the CourseOverview object in SQL.
        try:
            course_id = course_overview.id.to_deprecated_string()
            # logger.error('Course API ' + str(course_id))
            if course_id:
                payload = {'course_id': course_id}
                headers = {'content-type': "application/json"}
                url = "https://services.appliedx.amat.com/saba/api/v1/get_saba_details_from_db/"
                req = requests.post(url, json=payload, headers=headers, verify=False)
                response = req.text
                return json.loads(response)
            else:
                return None
        except:
            return None
