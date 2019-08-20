import json
import ssl
from uuid import uuid4

import dogstats_wrapper as dog_stats_api
import os
import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import ugettext as _
from xmodule.modulestore.django import modulestore
from xmodule.tabs import StaticTab
from xmodule.x_module import DEPRECATION_VSCOMPAT_EVENT

from contentstore.views.helpers import create_xblock, usage_key_with_run
from util.json_request import JsonResponse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _create_xblock(parent_locator, user, category, display_name, boilerplate=None, is_entrance_exam=False,
                   child_position=None):
    """
    Performs the actual grunt work of creating items/xblocks -- knows nothing about requests, views, etc.
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

        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if category == 'static_tab':
            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=(
                    "location:create_xblock_static_tab",
                    u"course:{}".format(unicode(dest_usage_key.course_key)),
                )
            )

            display_name = display_name or _("Empty")  # Prevent name being None
            course = store.get_course(dest_usage_key.course_key)
            course.tabs.append(
                StaticTab(
                    name=display_name,
                    url_slug=dest_usage_key.name,
                )
            )
            store.update_item(course, user.id)

        return created_block


def create_section(parent_locator, user, category, display_name, boilerplate=None, child_position=None):
    survey_credit_block = _create_xblock(
        parent_locator=parent_locator,
        user=user,
        category=category,
        display_name=display_name,
        boilerplate=boilerplate,
        child_position=child_position
    )
    return survey_credit_block


class SurveyRequest():
    """
    Legacy SurveyRequest.

    Unrelated to `poll_survey` app.
    """
    method = 'POST'
    body = '{}'


def create_common_xblock(section_name, user_email, parent_locator, update=False, published_on=None):
    from contentstore.views.item import _save_xblock, _get_xblock
    with open(BASE_DIR + "/common_xblock.json") as cxblock_file:
        COMMON_XBLOCK_OBJ = json.load(cxblock_file)
    if update:
        published_on = published_on
    else:
        now = timezone.now()
        published_on = now.strftime("%Y-%m-%d %H:%M:%S%Z")
    user = User.objects.get(email=user_email)
    usage_key_with_run(parent_locator)
    url = '{}{}'.format(settings.FEATURES['GET_CREDIT_SERVICE_URL'], '/commonsection/api/v1/')

    headers = {"content-type": "application/json"}
    if section_name == 'Introduction':
        child_position = 0
    elif section_name == "Survey":
        child_position = None
    else:
        child_position = None
    section = COMMON_XBLOCK_OBJ[section_name]
    chapter_parent = create_section(parent_locator, user, 'chapter', section['display_name'],
                                    child_position=child_position)
    for subsection in section['subsections']:
        sequetial_parent = create_section(unicode(chapter_parent.location), user, 'sequential',
                                          subsection['display_name'])
        if subsection.has_key('units'):
            for unit in subsection['units']:
                vertical_parent = create_section(unicode(sequetial_parent.location), user, 'vertical',
                                                 unit['display_name'])
                if unit.has_key('xblocks'):
                    for xblock in unit['xblocks']:
                        xblock_parent = None
                        if xblock["type"] == "survey" \
                                or xblock["type"] == "poll" \
                                or xblock["type"] == "open_ended_survey":
                            # Importing here since we rely on a custom `poll_survey` Django app
                            from poll_survey.models import SurveyPollCommonsection
                            commonsection_settings = SurveyPollCommonsection.objects.all().last()
                            if commonsection_settings:
                                if (xblock["type"] == "survey" and commonsection_settings.contains_survey) \
                                        or (xblock["type"] == "poll"
                                            and commonsection_settings.contains_poll) \
                                        or (xblock["type"] == "open_ended_survey"
                                            and commonsection_settings.contains_open_ended_survey):
                                    # We apply hardcoded defaults if no poll template was created.
                                    # Ref.: `xblock-poll.poll.poll_survey_storing.defaults.
                                    xblock_parent = create_section(unicode(vertical_parent.location),
                                                                   user,
                                                                   xblock['type'],
                                                                   xblock['display_name'],
                                                                   xblock.get('boilerplate')
                                                                   )
                            else:
                                # We create all sections if no commonsections have been set up on admin.
                                xblock_parent = create_section(unicode(vertical_parent.location),
                                                               user,
                                                               xblock['type'],
                                                               xblock['display_name'],
                                                               xblock.get('boilerplate')
                                                               )
                                # raise ValueError("Please create survey/poll/open-ended survey "
                                #                  "commonsection settings in admin.")
                        else:
                            xblock_parent = create_section(unicode(vertical_parent.location), user, xblock['type'],
                                                           xblock['display_name'], xblock.get('boilerplate'))
                        if xblock.has_key('metadata'):
                            video_metadata = xblock['metadata']
                            video_metadata['youtube_id_1_0'] = u''
                            if xblock_parent:
                                usage_key = usage_key_with_run(unicode(xblock_parent.location))
                                _save_xblock(
                                    user,
                                    _get_xblock(usage_key, user),
                                    metadata=video_metadata
                                )
                        if xblock.has_key('question'):
                            question = xblock.get('question')
                            req = SurveyRequest()
                            with open(BASE_DIR + "/survey_questions/" + question) as question_file:
                                json_question = question_file.read()
                            req.body = json_question
                            descriptor = xblock_parent
                            # descriptor.xmodule_runtime = StudioEditModuleRuntime(user)
                            try:
                                resp = descriptor.handle('studio_submit', req)
                                modulestore().update_item(descriptor, user.id)
                            except:
                                pass

    modulestore().publish(chapter_parent.location, user.id)
    _save_xblock(
        user,
        _get_xblock(chapter_parent.location, user),
        metadata={'start': published_on}
    )
    params = {
        'section': section_name,
        'course_key': unicode(chapter_parent.location),
        'parent_value': parent_locator,
        'created_by': user_email,
        'published_on': published_on
    }
    if update:
        return params
    try:
        response = requests.post(url, data=json.dumps(params), headers=headers, verify=False)
        print response.json()
    except:
        import sys
        print sys.exc_info()
    return chapter_parent


def create_yammer_discussion_page(request):
    from contentstore.views.item import _save_xblock, _get_xblock
    yammer_block = create_xblock(
        parent_locator=request.json['section_info']['parent_value'],
        user=request.user,
        category='static_tab',
        display_name='Yammer Discussion',
        boilerplate='None',
    )
    template_string = '''
    <div id="embedded-feed" style="height: 500px; width: 100%;"></div>
    <script src="https://assets.yammer.com/assets/platform_embed.js">// <![CDATA[

    // ]]></script>
    <script>// <![CDATA[
    var course_id = $("*[data-course-id]").attr("data-course-id")
    if(course_id == undefined) course_id = window.location.href.split("/courses/")[1].split("/courseware/")[0]
    $.get("/get_yammer_group_id", {'course_id': course_id}, function (data) {
           var ygid = JSON.parse(data).ygid;
           setTimeout(function(){
               	yam.connect.embedFeed({
	            "config": {"promptText": "Have feedback or Question?"},
      		    container: "#embedded-feed",
      		    network: "amat.com",
      		    feedType: "group",
      		    feedId: ygid
                });
           }, 2000)
        });
    // ]]></script>
    '''
    _save_xblock(
        request.user,
        _get_xblock(yammer_block.location, request.user),
        data=template_string
    )
    return yammer_block
