"""
Context dictionary for templates that use the ace_common base template.
"""


from django.conf import settings
from django.urls import NoReverseMatch, reverse

from common.djangoapps.edxmako.shortcuts import marketing_link
from openedx.core.djangolib.markup import HTML
from openedx.core.djangoapps.theming.helpers import get_config_value_from_site_or_settings


def get_base_template_context(site):
    """
    Dict with entries needed for all templates that use the base template.
    """
    # When on LMS and a dashboard is available, use that as the dashboard url.
    # Otherwise, use the home url instead.
    default_logo_url = getattr(settings, 'DEFAULT_EMAIL_LOGO_URL')
    try:
        dashboard_url = reverse('dashboard')
    except NoReverseMatch:
        dashboard_url = reverse('home')

    theme_dir = settings.DEFAULT_SITE_THEME

    if site is not None and site.themes.first() is not None:
        theme_dir = getattr(site.themes.first(), 'theme_dir_name')

    platform_name = get_config_value_from_site_or_settings(
        'PLATFORM_NAME',
        site=site,
        site_config_name='PLATFORM_NAME',
    )

    lms_url_root = get_config_value_from_site_or_settings('LMS_ROOT_URL', site=site)

    return {
        # Platform information
        'homepage_url': marketing_link('ROOT'),
        'dashboard_url': dashboard_url,
        'template_revision': getattr(settings, 'EDX_PLATFORM_REVISION', None),
        'platform_name': platform_name,
        'platform_name_tag': HTML("<a href='{lms_url_root}'><span dir='ltr'>{platform_name}</span></a>").format(
            lms_url_root=lms_url_root,
            platform_name=platform_name
        ),
        'contact_email': get_config_value_from_site_or_settings(
            'CONTACT_EMAIL', site=site, site_config_name='contact_email'),
        'contact_mailing_address': get_config_value_from_site_or_settings(
            'CONTACT_MAILING_ADDRESS', site=site, site_config_name='contact_mailing_address'),
        'social_media_urls': get_config_value_from_site_or_settings('SOCIAL_MEDIA_FOOTER_URLS', site=site),
        'mobile_store_urls': get_config_value_from_site_or_settings('MOBILE_STORE_URLS', site=site),
        'logo_url': '{lms_url_root}/static/{theme_dir}/images/'.format(
            lms_url_root=lms_url_root,
            theme_dir=theme_dir
        ),
        'support_contact_url': getattr(settings, 'CAMPUS_SUPPORT_CONTACT_URL', ''),
    }
