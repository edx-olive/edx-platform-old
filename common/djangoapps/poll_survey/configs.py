"""Polls configs shared across the platform."""

from poll_survey.models import (
    PollSubmission,
    SurveySubmission,
    OpenEndedSurveySubmission,
    PreCourseSurveySubmission,
    PostCourseSurveySubmission,
    CourseQualitySurveySubmission,
)


# Polls namings
REGULAR_POLL_NAME = "poll"

# Surveys namings
REGULAR_SURVEY_NAME = "survey"
PRE_COURSE_SURVEY_NAME = "pre_course_survey"
POST_COURSE_SURVEY_NAME = "post_course_survey"
COURSE_QUALITY_SURVEY_NAME = "course_quality_survey"

# Other polls namings
OPEN_ENDED_SURVEY_NAME = "open_ended_survey"

# Keep this list updated
ALLOWED_POLLS_NAMES = [
    REGULAR_POLL_NAME,
    REGULAR_SURVEY_NAME,
    OPEN_ENDED_SURVEY_NAME,
    PRE_COURSE_SURVEY_NAME,
    POST_COURSE_SURVEY_NAME,
    COURSE_QUALITY_SURVEY_NAME,
]

POLLS_SUBMISSIONS_MAPPING = {
    REGULAR_POLL_NAME: PollSubmission,
    REGULAR_SURVEY_NAME: SurveySubmission,
    OPEN_ENDED_SURVEY_NAME: OpenEndedSurveySubmission,
    PRE_COURSE_SURVEY_NAME: PreCourseSurveySubmission,
    POST_COURSE_SURVEY_NAME: PostCourseSurveySubmission,
    COURSE_QUALITY_SURVEY_NAME: CourseQualitySurveySubmission
}
