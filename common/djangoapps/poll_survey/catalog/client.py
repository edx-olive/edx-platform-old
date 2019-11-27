"""
AMAT Catalog API clients.
"""
import httplib
import logging
import requests

from django.conf import settings

from poll_survey.catalog.constants import (
    APPLIEDX_PLATFORM_NAME,
    CatalogDataPushingErrors,
    RATING_API_RESPONSE_MARKER_MAPPING,
)
from poll_survey.catalog.exceptions import (
    AmatCatalogApiConnectionException,
    AmatCatalogApiResponseParsingException,
    AmatCatalogInvalidCourseIdException,
    AmatCatalogInvalidRatingException,
    AmatCatalogNonExistingCourseException,
    AmatCatalogRatingNonExistingUserIdException,
    AmatCatalogRatingUnacceptableUserIdException,
)
from poll_survey.catalog.utils import (
    prepare_course_agu_id,
    prepare_employee_user_id,
    prepare_poll_rating,
    validate_payload_nomenclature,
)
from poll_survey.catalog.constants import CatalogApiErrors

log = logging.getLogger(__name__)


class AmatCatalogBaseApiClient(object):
    """
    Low level AMAT Catalog (Pathway) API client.
    """

    def __init__(self, auth_user=None):
        """
        Initialize a base AMAT Pathway client.

        Arguments:
            auth_user (str): user name required for authorized API calls.
        """
        self.auth_user = auth_user or settings.AMAT_CATALOG_USER
        if not self.auth_user:
            raise ValueError("Please configure the 'AMAT_CATALOG_USER' env variable.")

    def post(self, url, payload, headers=None, can_retry=False):
        """
        Issue REST POST request to a given URL.

        Arguments:
            url (str): API url to fetch a resource from.
            payload (dict): POST data.
            headers (dict): Headers necessary as per API.
            can_retry (bool): True to retry a call.
        Returns:
            endpoint response with custom data (dict). 'status_code' is required for
                marking in 'common.djangoapps.poll_survey.tasks.catalog_rating_polls'.
        """
        headers_ = {
            "content-type": "application/json",
            "testingUser": self.auth_user,
        }
        if headers is not None:
            headers_.update(headers)
        try:
            resp = requests.post(url, json=payload, headers=headers_)
            resp_dict = resp.json()
            resp_dict["status_code"] = resp.status_code  # See the docstring for rationale
            log.debug(
                "AMAT Catalog API response: %s, msg: '%s', success: '%s'",
                resp.status_code,
                resp_dict.get(u'msg'),
                resp_dict.get(u'success'),
            )
            if resp.status_code != httplib.OK and can_retry:
                return self.post(url, payload, headers, can_retry=False)
            return resp_dict
        # Note: consider catching Timeout, TooManyRedirects, etc (see the docs on `requests` exceptions)
        except requests.exceptions.ConnectionError:
            message = AmatCatalogApiConnectionException.marker.message
            log.exception(message)
            raise AmatCatalogApiConnectionException
        except ValueError:
            message = AmatCatalogApiResponseParsingException.marker.message
            log.exception(message)
            raise AmatCatalogApiResponseParsingException


class AmatCatalogApiClient(AmatCatalogBaseApiClient):
    """
    Encapsulate API logic for specific AMAT Catalog features.

    Docs:
        https://documenter.getpostman.com/view/8398148/SVYupcDN?version=latest
    """

    def __init__(self, auth_user=None, base_url=None):
        """
        Initialize a high-level AMAT Pathway client.

        Arguments:
            auth_user (str): user name required for authorized API calls.
            base_url (str): base URL of API calls, e.g.
                "https://xxxxxxxxxx.execute-api.us-west-2.amazonaws.com/Prod/"
        """
        self.base_url = base_url or settings.AMAT_CATALOG_BASE_URL
        if not self.base_url:
            raise ValueError("Please configure the 'AMAT_CATALOG_BASE_URL' env variable.")
        super(AmatCatalogApiClient, self).__init__(auth_user)

    def transfer_rating(self, data, validate=True):
        """
        Store poll rating.

        Docs:
            https://documenter.getpostman.com/view/8398148/SVYupcDN?version=latest#5f82e6c4-004f-4eba-894a-70bf19d02cc7

        Arguments:
            data (dict): custom payload. NOTE: all of Catalog-required payload values should be of `str` type.
            validate (bool): instruction to run data validation. Careful with setting to False:
                internal logic might throw an uncaught error.
        Returns:
            marker (str): a marker based on payload validation or
                API call results; first value (marker code) defined in enumerators
                in 'common.djangoapps.poll_survey.catalog.constants'.
        """
        endpoint_path = "content/rateext"
        expected_params = [
            "user_id",
            "course_id",
            "rating",
            "course_agu_id",  # Not required by the API endpoint (not Catalog-required)
        ]

        try:
            validate_payload_nomenclature(data, expected_params)
        except ValueError:
            # Consider creating some sort of programming error exception
            return CatalogDataPushingErrors.EDX_ERROR.code

        course_agu_id = None
        if validate:
            try:
                _ = prepare_employee_user_id(data["user_id"])
                _ = prepare_poll_rating(data["rating"])
                # If None, we still have to run into exception and mark a submission respectively
                course_agu_id = data["course_agu_id"] or prepare_course_agu_id(data["course_id"])
            except (
                AmatCatalogRatingNonExistingUserIdException,
                AmatCatalogRatingUnacceptableUserIdException,
                AmatCatalogInvalidRatingException,
                AmatCatalogInvalidCourseIdException,
                AmatCatalogNonExistingCourseException,
            ), e:
                return e.marker.code

        # Uncaught error might be thrown (left for higher-level logic to handle)
        course_agu_id = course_agu_id or data["course_agu_id"] or prepare_course_agu_id(data["course_id"])

        payload = {
            "user_id": data["user_id"],
            "course_id": course_agu_id,
            "rating": data["rating"],
            "source": APPLIEDX_PLATFORM_NAME,
        }

        try:
            resp_dict = self.post(
                url=self.base_url + endpoint_path,
                payload=payload,
            )
            return RATING_API_RESPONSE_MARKER_MAPPING.get(
                resp_dict.get("status_code"),
                RATING_API_RESPONSE_MARKER_MAPPING["default"]
            )
        except (
            AmatCatalogApiConnectionException,
            AmatCatalogApiResponseParsingException,
        ) as e:
            return e.marker.code
        # Can't afford failing the pipeline, need to mark a submission
        except Exception as e:
            log.exception(
                "An error occurred when rating polls's submission transferring to the Catalog. "
                "Error: '{!s}'; "
                "rating submission data: '{!s}'."
                .format(e, data)
            )
            return CatalogApiErrors.CATALOG_OTHER_ERROR.code
