"""
Custom AMAT API exceptions.
"""

from poll_survey.catalog.constants import (
    CatalogApiErrors,
    CatalogDataValidationErrors,
)


class AmatCatalogApiException(Exception):
    """
    AMAT Catalog related exception.
    """

    marker = CatalogApiErrors.CATALOG_OTHER_ERROR

    def __init__(self, marker=None):
        self.marker = marker or self.marker
        super(AmatCatalogApiException, self).__init__(self.marker.message)

    def __str__(self):
        """
        Override string representation of an exceptions object.

        Returns:
            marker code (str): marker code from `poll_survey.catalog.constants` enums.
        """
        return self.marker.code


class AmatCatalogApiConnectionException(AmatCatalogApiException):
    """
    Custom exception for AMAT Catalog API ConnectionError.
    """

    marker = CatalogApiErrors.CATALOG_CONNECTION_ERROR


class AmatCatalogApiResponseParsingException(AmatCatalogApiException):
    """
    Custom exception occurring when AMAT Catalog API client response parsing.
    """

    marker = CatalogApiErrors.CATALOG_RESPONSE_PARSING_ERROR


class AmatCatalogRatingUnacceptableUserIdException(AmatCatalogApiException):
    """
    Custom exception occurring when rating validation for AMAT Catalog API.
    """

    marker = CatalogDataValidationErrors.RATING_INCORRECT_USER_ID


class AmatCatalogRatingNonExistingUserIdException(AmatCatalogApiException):
    """
    Custom exception occurring user id validation for AMAT Catalog API.

    Might happen, but quite rarely (it's just that
    `poll_survey.models.SubmissionBase` can take None for `employee_id`).
    """

    marker = CatalogDataValidationErrors.RATING_USER_WITHOUT_EMPLOYEE_ID


class AmatCatalogInvalidRatingException(AmatCatalogApiException):
    """
    Custom exception occurring when rating validation for AMAT Catalog API.
    """

    marker = CatalogDataValidationErrors.RATING_INVALID_RATING


class AmatCatalogInvalidCourseIdException(AmatCatalogApiException):
    """
    Custom exception occurred when course id validating for AMAT Catalog API.
    """

    marker = CatalogDataValidationErrors.RATING_INVALID_COURSE_ID


class AmatCatalogNonExistingCourseException(AmatCatalogApiException):
    """
    Custom exception occurred when course id preparing for AMAT Catalog API.
    """

    marker = CatalogDataValidationErrors.RATING_NON_EXISTING_COURSE
