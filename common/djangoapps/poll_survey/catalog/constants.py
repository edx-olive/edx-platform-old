"""
Custom AMAT API constants.

The AMAT Catalog (Pathway) API call results are located and marked
to the extent necessary for the background task "catalog_rating_polls"
monitoring and scripts re-running.
"""

import httplib

from enum import Enum

# Source id, with "od" signifying the AMAT Appliedx ONDEMAND platform.
APPLIEDX_PLATFORM_NAME = "od"
# NOTE: Remember to update this setting if rating polls scale gets updated.
ALLOWED_POLL_RATINGS = ["1", "2", "3", "4", "5"]


class BaseCatalogEnum(Enum):
    """
    Base behaviour for Catalog enums.
    """

    @property
    def code(self):
        """
        Get a catalog marker code.
        """
        return self.value[0]

    @property
    def message(self):
        """
        Get a detailed message explaining a marker code.
        """
        return self.value[1]


class CatalogApiSuccessCases(BaseCatalogEnum):
    """
    Catalog/Pathway API: success cases nomenclature.

    Naming should start with "CATALOG_".
    """

    # General Catalog API cases
    CATALOG_DEFAULT_CASE = ("CATALOG_DEFAULT_CASE", "Default.")

    # Transfer-Rating specific cases
    CATALOG_RATING_SUCCESS = ("CATALOG_RATING_SUCCESS", "Rating was successfully pushed to the Catalog.")


class CatalogApiErrors(BaseCatalogEnum):
    """
    Catalog/Pathway API: error cases nomenclature.

    Naming should start with "CATALOG_".
    """

    # General Catalog API cases
    CATALOG_SERVER_ERROR = ("CATALOG_SERVER_ERROR", "Catalog server error occurred.")
    CATALOG_BAD_GATEWAY_ERROR = ("CATALOG_BAD_GATEWAY_ERROR", "Catalog bad gateway error occurred.")
    CATALOG_AUTH_ERROR = ("CATALOG_AUTH_ERROR", "Unauthorized call to the Catalog.")
    CATALOG_FORBIDDEN_ERROR = ("CATALOG_FORBIDDEN_ERROR", "Forbidden call to the Catalog.")
    CATALOG_CONNECTION_ERROR = ("CATALOG_CONNECTION_ERROR", "AMAT Catalog connection error occurred.")
    CATALOG_RESPONSE_PARSING_ERROR = (
        "CATALOG_RESPONSE_PARSING_ERROR",
        "Can't parse unexpected response during POST request to AMAT Catalog API."
    )
    CATALOG_OTHER_ERROR = ("CATALOG_OTHER_ERROR", "AMAT Catalog API error occurred.")

    # Endpoint specific Catalog API cases
    CATALOG_RATING_BAD_REQUEST = (
        "CATALOG_RATING_BAD_REQUEST",
        # e.g. User is not identified
        "Catalog Transfer-Rating API responded with a Bad Request error."
    )
    CATALOG_RATING_OTHER_ERROR = (
        "CATALOG_RATING_OTHER_ERROR",
        "Rating wasn't pushed to the Catalog (undefined error)."
    )


class CatalogDataValidationErrors(BaseCatalogEnum):
    """
    Errors caused by data validation logic (edX side).
    """

    # Validation for the Transfer-Rating endpoint
    RATING_INCORRECT_USER_ID = (
        "RATING_INCORRECT_USER_ID",
        # i.e. rating was submitted by a non-fulltime/contractor user
        "Provided user id is unacceptable for the Catalog Transfer-Rating API endpoint."
    )
    RATING_USER_WITHOUT_EMPLOYEE_ID = (
        "RATING_USER_WITHOUT_EMPLOYEE_ID",
        "Rating was submitted by a user without employee id."
    )
    RATING_INVALID_RATING = ("RATING_INVALID_RATING", "Rating isn't on a 1-5 scale.")
    RATING_INVALID_COURSE_ID = ("RATING_INVALID_COURSE_ID", "Invalid course id in a rating submission.")
    RATING_NON_EXISTING_COURSE = ("RATING_NON_EXISTING_COURSE", "Non-existing course.")


class CatalogDataPushingErrors(BaseCatalogEnum):
    """
    Errors caused by various edX issues.

    Including business logic and environmental issues.
    NOTE consider adding specific cases e.g. Celery is down.
    """

    EDX_ERROR = ("EDX_ERROR", "Data wasn't pushed to the Catalog (edx error).")


# Low-level Catalog Transfer-Rating API mapping.
RATING_API_RESPONSE_MARKER_MAPPING = {
    httplib.OK: CatalogApiSuccessCases.CATALOG_RATING_SUCCESS.code,
    httplib.BAD_REQUEST: CatalogApiErrors.CATALOG_RATING_BAD_REQUEST.code,
    httplib.UNAUTHORIZED: CatalogApiErrors.CATALOG_AUTH_ERROR.code,
    httplib.FORBIDDEN: CatalogApiErrors.CATALOG_FORBIDDEN_ERROR.code,
    httplib.INTERNAL_SERVER_ERROR: CatalogApiErrors.CATALOG_SERVER_ERROR.code,
    # We get Bad Gateway when changing "user_id" payload param, e.g. "2222222"
    # (getting OK if changing to valid user id e.g. employee id of an existing full-time user).
    httplib.BAD_GATEWAY: CatalogApiErrors.CATALOG_BAD_GATEWAY_ERROR.code,
    "default": CatalogApiErrors.CATALOG_OTHER_ERROR.code,
}
