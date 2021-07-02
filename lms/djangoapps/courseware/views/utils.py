from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import resolve_url
from functools import wraps


def custom_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.

    The difference from default Django decorator is that after redirecting user
    to login page, the next param of the login url contains absolute url of
    the initially requested view, not relative one.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)

            # after user successfully signs in redirect them to the initially
            # requested page using its absolute url
            absolute_path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            return redirect_to_login(absolute_path, resolved_login_url, redirect_field_name)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
