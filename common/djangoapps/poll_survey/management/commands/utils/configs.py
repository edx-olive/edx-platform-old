"""
Legacy surveys/polls titles, questions, and answers.
"""

from poll_survey import configs


# Dedicated Rating poll
# It's actually a SURVEY in legacy components
# (will become POLL in poll_survey tables).
RATING_POLL_TITLE = "COURSE RATING"
RATING_POLL_QUESTIONS = [
    "How would you rate the overall effectiveness of this course on a scale of 1-5, (where 5 being very good )?",
]
RATING_POLL_ANSWERS = ["1", "2", "3", "4", "5"]

# Dedicated Course quality survey
COURSE_QUALITY_SURVEY_TITLE = "BASED ON THE FOLLOWING ELEMENTS/TOPICS, " \
                              "PLEASE RATE THE OVERALL EXPERIENCE OF THIS COURSE:"
COURSE_QUALITY_SURVEY_QUESTIONS = [
    "Effectively organized content",
    "Provides deeper insights of the Subject",
    "Effective Video materials",
    "Appropriate Quizzes based on the course content",
]
COURSE_QUALITY_SURVEY_ANSWERS = [
    "Strongly disagree",
    "Disagree",
    "Neither",
    "Agree",
    "Strongly Agree",
]

# Dedicated Pre-Course survey
# Its questions are always course specific
PRE_COURSE_SURVEY_TITLE = "BEFORE YOU START THE COURSE, " \
                          "PLEASE RATE YOUR LEVEL OF ABILITY/KNOWLEDGE ON THE FOLLOWING TOPICS:"
PRE_COURSE_SURVEY_ANSWERS = [
    "Not at All",
    "Very little",
    "Neutral",
    "Moderate",
    "Very much",
]

# Dedicated Post-Course survey
# Its questions are always course specific
POST_COURSE_SURVEY_TITLE = "AFTER THE COURSE, " \
                           "PLEASE RATE YOUR LEVEL OF ABILITY/KNOWLEDGE ON THE FOLLOWING TOPICS:"
POST_COURSE_SURVEY_ANSWERS = PRE_COURSE_SURVEY_ANSWERS


# Keep these lists and mappings up-to-date
DEDICATED_POLLS_NAMES_TO_MIGRATE = [
    configs.RATING_POLL_NAME,
    configs.COURSE_QUALITY_SURVEY_NAME,
    configs.PRE_COURSE_SURVEY_NAME,
    configs.POST_COURSE_SURVEY_NAME,
]
# Mapping to check candidate surveys against
POLLS_ELEMENTS_NAMES_MAPPING = {
    configs.RATING_POLL_NAME: {
        "title": RATING_POLL_TITLE,
        "questions": RATING_POLL_QUESTIONS,
        "answers": RATING_POLL_ANSWERS,
    },
    configs.COURSE_QUALITY_SURVEY_NAME: {
        "title": COURSE_QUALITY_SURVEY_TITLE,
        "questions": COURSE_QUALITY_SURVEY_QUESTIONS,
        "answers": COURSE_QUALITY_SURVEY_ANSWERS,
    },
    configs.PRE_COURSE_SURVEY_NAME: {
        "title": PRE_COURSE_SURVEY_TITLE,
        "questions": [],  # Always course-specific
        "answers": PRE_COURSE_SURVEY_ANSWERS,
    },
    configs.POST_COURSE_SURVEY_NAME: {
        "title": POST_COURSE_SURVEY_TITLE,
        "questions": [],  # Always course-specific
        "answers": POST_COURSE_SURVEY_ANSWERS,
    },
}
