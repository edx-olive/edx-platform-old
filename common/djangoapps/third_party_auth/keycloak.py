import jwt

from django.conf import settings
from social_core.backends.keycloak import KeycloakOAuth2


class CustomKeycloakBackend(KeycloakOAuth2):
    def user_data(self, access_token, *args, **kwargs):  # pylint: disable=unused-argument
        """Decode user data from the access_token
        You can specialize this method to e.g. get information
        from the Keycloak backend if you do not want to include
        the user information in the access_token.
        """
        return jwt.decode(
            access_token,
            key=self.public_key(),
            algorithms=self.algorithm(),
            audience=settings.SSO_AUDIENCE,
        )
