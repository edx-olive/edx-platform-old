import crum
from django.conf import settings
from django.utils.translation import get_language

from openedx.core.djangoapps.user_api.errors import UserAPIInternalError, UserNotFound
from openedx.core.djangoapps.user_api.preferences.api import get_user_preference


def get_preference_language():
    """
        Return the preference language user or if user is not authenticated return the language
        is installed in the browser.
    """
    preference_language = get_language()
    request = crum.get_current_request()

    if hasattr(request, 'user') and request.user.is_authenticated:

        try:
            return get_user_preference(request.user, 'pref-lang')

        except (UserNotFound, UserAPIInternalError):
            return preference_language

    return preference_language


def get_current_tos_privacy_url(page_name):
    """
        Returns the URL of the current static page with the given preferred language.

        Arguments:
            page_name (str): name of the static page

        Returns:
            str: url on the current static page
    """
    preference_language = get_preference_language()
    if page_name == 'tos' and settings.CAMPUS_TOS_URLS:
        current_url = (
            settings.CAMPUS_TOS_URLS.get(preference_language)
            if preference_language in settings.CAMPUS_TOS_URLS else
            settings.CAMPUS_TOS_URLS.get('en')
        )
    elif page_name == 'privacy' and settings.CAMPUS_PRIVACY_URLS:
        current_url = (
            settings.CAMPUS_PRIVACY_URLS.get(preference_language)
            if preference_language in settings.CAMPUS_TOS_URLS else
            settings.CAMPUS_PRIVACY_URLS.get('en')
        )
    else:
        current_url = settings.CAMPUS_DEFAULT_TOS_PRIVACY_URL

    return current_url
