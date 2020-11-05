from django.core.exceptions import ObjectDoesNotExist


def get_employee_id(user):
    """
    Get PingSSO employee id.
    """
    try:
        social = user.social_auth.filter(provider='tpa-saml').last()
    except ObjectDoesNotExist:
        social = None

    if social and getattr(social, "uid", None):
        return social.uid.split(':')[1] if ":" in social.uid else None

    return None
