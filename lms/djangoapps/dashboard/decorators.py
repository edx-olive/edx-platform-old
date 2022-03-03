from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect


def redirect_sysadmin_url(view_func):
    """
    View decorator that redirects to the sysadmin page if the
    feature ENABLE_SYSADMIN_COURSES_TAB = False.
    """
    def wrap(request, *args, **kwargs):
        if settings.FEATURES.get('ENABLE_SYSADMIN_COURSES_TAB', False):
            return view_func(request, *args, **kwargs)
        else:
            return redirect(reverse('sysadmin'))
    return wrap
