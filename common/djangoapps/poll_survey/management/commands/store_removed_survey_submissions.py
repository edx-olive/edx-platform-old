"""
Save submissions of particular removed surveys to the `poll_survey` tables.

NOTE: this command was never tested or used in production, because legacy
submissions are stored in an unordered way, not corresponding to the natural
order of related `StudentModule` submissions.
We had to come up with another solution for AMATX-526.
Keeping this command for future references.
"""
from __future__ import print_function
from datetime import datetime
import json
from optparse import make_option
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey, UsageKey

from courseware.models import StudentModule
from poll_survey.configs import (
    COURSE_QUALITY_SURVEY_NAME,
    POST_COURSE_SURVEY_NAME,
    PRE_COURSE_SURVEY_NAME,
    RATING_POLL_NAME,
    REGULAR_SURVEY_NAME,
    POLLS_SUBMISSIONS_MAPPING,
)
from poll_survey.management.commands.utils.configs import (
    COURSE_QUALITY_SURVEY_QUESTIONS,
    COURSE_QUALITY_SURVEY_ANSWERS,
    RATING_POLL_QUESTIONS,
    RATING_POLL_ANSWERS,
    PRE_COURSE_SURVEY_ANSWERS,
    POST_COURSE_SURVEY_ANSWERS,
)
from poll_survey.management.commands.utils.commands_utils import (
    get_employee_id,
    UserService,
)
from poll_survey.models import (
    PollAnswerOption,
    PollQuestion,
    SurveyAnswerOption,
    SurveyQuestion,
)


# Configs for our particular case
PRE_COURSE_SURVEY_QUESTIONS_LOW = POST_COURSE_SURVEY_QUESTIONS_LOW = [
    "Explain the need and importance of validation".strip().lower(),
    "Identify minimum viable product through testing value tradeoffs".strip().lower(),
    "Describe validation product roadmap".strip().lower(),
]
COURSE_QUALITY_SURVEY_QUESTIONS_LOW = [item.strip().lower() for item in COURSE_QUALITY_SURVEY_QUESTIONS]
COURSE_QUALITY_SURVEY_ANSWERS_LOW = [item.strip().lower() for item in COURSE_QUALITY_SURVEY_ANSWERS]
RATING_POLL_QUESTIONS_LOW = [item.strip().lower() for item in RATING_POLL_QUESTIONS]
RATING_POLL_ANSWERS_LOW = [item.strip().lower() for item in RATING_POLL_ANSWERS]
PRE_COURSE_SURVEY_ANSWERS_LOW = [item.strip().lower() for item in PRE_COURSE_SURVEY_ANSWERS]
POST_COURSE_SURVEY_ANSWERS_LOW = [item.strip().lower() for item in POST_COURSE_SURVEY_ANSWERS]

# To facilitate messages parsing in logs
WARNING_1 = "WARNING #1. A question or an answer couldn't be found. " \
            "Won't persist the submission {!s} for xblock {!s}. " \
            "StudentModule submission: {!s}. " \
            "Questions mapping: {!s}. Answers mapping: {!s}"
WARNING_2 = "WARNING #2. A question or an answer text differs from the mapping. " \
            "Won't persist the submission {!s} for xblock {!s}. " \
            "StudentModule submission: {!s}. " \
            "Questions mapping: {!s}. Answers mapping: {!s}"
WARNING_3 = "WARNING #3. When mappings creating for xblock {!s}, " \
            "StudentModule and poll_survey submissions differ. " \
            "StudentModule subs: {!s}; poll_survey subs: {!s}" \
            "Intermediate mappings: questions {!s}, answers mapping: {!s}"
WARNING_4 = "WARNING #4. Choices are null in a survey submission state {!s}. " \
            "Won't persist a StudentModule submission {!s} for xblock {!s}."
WARNING_5 = "WARNING #5. Could not store a survey StudentModule " \
            "submission {!s} for xblock {!s}. " \
            "No user with id {!s} or no required submission_model_class was found."

INFO_1 = "INFO #1. No questions and/or answers mappings are made for xblock {!s}. " \
          "Mappings: questions {!s}, answers {!s}"
INFO_2 = "INFO #2. Mappings for xblock {!s}: questions - {!s}, answers - {!s}"


def _create_log_files(survey_type):
    """
    Create log files to store results of the command.

    One-time operation. Supposed to remove logs afterwards.

    Filepath example: '/edx/app/edxapp/data/poll_survey_commands_data/restored_surveys_subs_info_rating_poll_15900699480.txt'
    """

    # Create `/edx/app/edxapp/data/poll_survey_commands_data` dir if non-existent.
    # Using `/edx/app/edxapp/data`, not `/edx/var/`, because of write permissions availability.
    # NOTE: `GITHUB_REPO_ROOT` contains cloned repos of courses
    #  imported via /sysadmin/courses, and third-party modifications can break
    #  the "Load new course from GitHub" functionality.
    saba_credits_data_path = settings.GITHUB_REPO_ROOT / "poll_survey_commands_data"
    # `settings.GITHUB_REPO_ROOT` is of `Path` type
    if not saba_credits_data_path.isdir():
        saba_credits_data_path.mkdir()

    # Mark files with (modified) timestamps to distinguish between command runs
    now = str(time.mktime(datetime.now().timetuple())).replace(".", "")
    info_filepath = os.path.join(
        str(saba_credits_data_path),
        "restored_surveys_subs_info_{}_{}.txt".format(survey_type, now)
    )
    warning_filepath = os.path.join(
        str(saba_credits_data_path),
        "restored_surveys_subs_warnings_{}_{}.txt".format(survey_type, now)
    )

    return info_filepath, warning_filepath


def fprint(filename, *args, **kwargs):
    """
    Redirect print to a particular file.

    Ref.: https://stackoverflow.com/a/14981125
    Avoiding global effects: https://stackoverflow.com/a/51340381
    """
    print(*args, file=filename, **kwargs)


class Command(BaseCommand):
    """
    Command to store particular surveys submissions in `poll_survey` tables.

    This command is crafted to handle a particular situation described in AMATX-526.

    Examples:
    ```
    ./manage.py lms --settings=devstack store_removed_survey_submissions --course_id="course-v1:PDE1+217+Anytime" --survey_type="course_quality_survey" --submission_date_to="2020-10-17"
    ```
    """

    MODULE_TYPE = "survey"
    CHUNK_SIZE = 2000
    FROM_PK = 1L
    MEASURE = 0

    args = ""
    help = "Store removed surveys submissions in poll_survey tables"
    option_list = BaseCommand.option_list + (
        make_option("--course_id",
                    dest="course_id",
                    type="string",
                    help="Run the command for a particular course "
                         "e.g. 'course-v1:PDE1+217+Anytime'"),
        make_option("--survey_type",
                    dest="survey_type",
                    type="string",
                    help="Poll or survey type to handle. Either of: 'pre_course_survey', "
                         "'post_course_survey', 'course_quality_survey', 'rating_poll'."),
        make_option("--submission_date_to",
                    dest="submission_date_to",
                    type="string",
                    help="Student submissions date (will fetch entries created before this date). "
                         "Format: YYYY-MM-DD, e.g. '2019-09-13'"),
        make_option("--measure",
                    dest="measure",
                    type="int",
                    default=MEASURE,
                    help="Instruction to measure submissions processing."),
        make_option("--chunk_size",
                    dest="chunk_size",
                    type="int",
                    default=CHUNK_SIZE,
                    help="Number of submissions in a chunk."))

    def handle(self, *args, **options):
        """
        Save removed surveys historical submissions.

        Store particular surveys submissions in `poll_survey` subs tables.

        Note that respective xblocks were removed from the courseware.
        """
        print("Processing historical surveys...")
        chunk_size = options.get("chunk_size")
        course_id = CourseKey.from_string(options.get("course_id"))
        survey_type = options.get("survey_type")
        submission_date_to = datetime.strptime(options.get("submission_date_to"), '%Y-%m-%d')
        measure = options.get("measure")

        if survey_type not in [
            COURSE_QUALITY_SURVEY_NAME,
            POST_COURSE_SURVEY_NAME,
            PRE_COURSE_SURVEY_NAME,
            RATING_POLL_NAME,
        ]:
            raise ValueError("Provide a correct survey_type.")

        submission_model_class = POLLS_SUBMISSIONS_MAPPING.get(survey_type)
        last_sub = submission_model_class.objects.filter(course=course_id).last()
        if not last_sub:
            # e.g. students haven't submitted yet, previous migrations failed
            print("Subs haven't been stored in the poll_survey table yet.")
            return

        # After this date, StudentModule submissions stopped from being duplicated in `poll_survey`
        #  tables, i.e. this is the date when corresponding xblocks were removed.
        last_sub_creation_date = last_sub.submission_date if last_sub else None

        if submission_date_to < last_sub_creation_date.replace(tzinfo=None):
            raise ValueError(
                "submission_date_to ({!s}) should be bigger than "
                "last_sub_creation_date ({!s}).".format(
                    submission_date_to,
                    last_sub_creation_date,
                ))

        subs_count = StudentModule.objects.filter(
            created__lte=submission_date_to,
            created__gte=last_sub_creation_date,
            course_id=course_id,
            module_type=self.MODULE_TYPE,
        ).count()
        if subs_count:
            print("Found {!s} survey StudentModule submissions.".format(subs_count))
        else:
            print("No survey StudentModule submissions found.")
            return

        # Will group this by xblocks, since state's questions/answers labels can coincide
        qs = StudentModule.objects.filter(
            created__lte=last_sub_creation_date,
            course_id=course_id,
            module_type=self.MODULE_TYPE,
        )
        xblocks_keys = qs.values_list("module_state_key", flat=True).distinct()

        info_filepath, warning_filepath = _create_log_files(survey_type)

        with open(info_filepath, "w+") as info_file, open(warning_filepath, "w+") as warn_file:

            for xblock_key in xblocks_keys:
                print("=============================xblock: {!s}=============================="
                      .format(xblock_key))

                # NOTE: consider checking for duplicated texts
                questions_map, answers_map = self._create_questions_answers_mappings(
                    course_id=course_id,
                    survey_type=survey_type,
                    last_sub_creation_date=last_sub_creation_date,
                    xblock_key=xblock_key,
                    log_files=(info_file, warn_file),
                )

                if not questions_map or not answers_map:
                    # No submissions were made for this xblock
                    msg = INFO_1.format(
                        xblock_key,
                        questions_map,
                        answers_map,
                    )
                    fprint(info_file, msg)
                    print(msg)
                    continue

                msg = INFO_2.format(
                    xblock_key,
                    questions_map,
                    answers_map,
                )
                fprint(info_file, msg)
                print(msg)

                sm_qs = StudentModule.objects.filter(
                    created__lte=submission_date_to,
                    created__gte=last_sub_creation_date,
                    course_id=course_id,
                    module_type=self.MODULE_TYPE,
                    module_state_key=UsageKey.from_string(xblock_key),
                )
                sm_subs_count = sm_qs.count()

                processed_subs_counter = 0
                sub_processing_time = 0

                for offset in range(0, sm_subs_count, chunk_size):
                    print("=====================offset: {!s} for xblock: {!s}=======================\n"
                          "Starting to process survey XBlock submissions from {!s} to {!s}."
                          .format(offset, offset, chunk_size+offset, xblock_key))

                    stud_module_subs = sm_qs[offset:chunk_size+offset]

                    for submission_entry in stud_module_subs:
                        sub_t1 = datetime.now() if measure else 0
                        print(
                            "=============submission entry {!s}, xblock {!s}=============".format(
                                submission_entry.id,
                                xblock_key,
                            ))

                        parsed_submissions = self._get_submissions_data(
                            submission_entry.state,
                            log_data={
                                "sm_sub": submission_entry,
                                "xblock_key": xblock_key,
                            },
                            log_files=(info_file, warn_file,),
                        )

                        if parsed_submissions:
                            print("Starting to process survey subs: {!s}".format(parsed_submissions))
                        for submission in parsed_submissions:
                            print("-------submission datum-------")
                            print("Starting to process submission data: {!s}".format(submission))

                            question_text = questions_map.get(submission[0])
                            answer_text = answers_map.get(submission[1])

                            if question_text and answer_text:

                                if survey_type == RATING_POLL_NAME:
                                    question_model = PollQuestion
                                    answer_model = PollAnswerOption
                                else:
                                    question_model = SurveyQuestion
                                    answer_model = SurveyAnswerOption

                                # We assume that corresponding `poll_survey` questions and answers entries
                                # exist and can be relied on, e.g. no duplicates with the same text exist.
                                question_entry = question_model.objects.filter(
                                    text=question_text.strip().lower(),
                                ).last()
                                answer_entry = answer_model.objects.filter(
                                    text=answer_text.strip().lower(),
                                ).last()
                                if question_entry and answer_entry:
                                    self._store_submission(
                                        question_entry,
                                        answer_entry,
                                        submission_entry,
                                        survey_type=survey_type,
                                        log_data={
                                            "xblock_key": xblock_key,
                                        },
                                        log_files=(info_file, warn_file,),
                                    )
                                else:
                                    msg = WARNING_1.format(
                                        submission,
                                        xblock_key,
                                        submission_entry.pk,
                                        questions_map,
                                        answers_map,
                                    )
                                    fprint(warn_file, msg)
                                    print(msg)

                            else:
                                # NOTE: labels not appearing in historical responses won't be processed
                                #  (lost submissions)
                                msg = WARNING_2.format(
                                    submission,
                                    xblock_key,
                                    submission_entry.pk,
                                    questions_map,
                                    answers_map,
                                )
                                fprint(warn_file, msg)
                                print(msg)

                        processed_subs_counter += 1
                        print("Processed {!s} StudentModule submissions out of {!s} for xblock {!s}.".format(
                            processed_subs_counter,
                            sm_subs_count,
                            xblock_key,
                        ))
                        print("Latest processed submission entry id - {!s}, submission date - {!s}"
                              .format(submission_entry.id, submission_entry.created))
                        print("Current offset: {!s}".format(offset))

                        if measure:
                            sub_t2 = datetime.now()
                            diff = (sub_t2 - sub_t1).microseconds
                            sub_processing_time += diff
                            print("Processing time for one submission_entry: {!s} microseconds"
                                  .format(diff))
                            print("Average processing time for one submission_entry: {!s} microseconds."
                                  .format(float(sub_processing_time / processed_subs_counter)))

                if measure and processed_subs_counter:
                    print(
                        "\n\n\nAverage processing time for one submission_entry for xblock {!s}"
                        "(out of {!s} entries): {!s} microseconds.".format(
                            xblock_key,
                            processed_subs_counter,
                            float(sub_processing_time / processed_subs_counter),
                        )
                    )

        print("============= THE END. =============")

    def _create_questions_answers_mappings(self, survey_type, course_id, last_sub_creation_date, xblock_key, log_files):
        """
        Map StudentModule submission's q/a labels with `poll_survey` submission's q/a text.

        NOTE: this mapping wouldn't be needed if we could retrieve removed xblocks from the store.

        Example of a StudentModule submission:
            ```
            {"submissions_count": 2, "choices": {"enjoy": "Y", "learn": "Y", "1561550057662": "Y"}}
            ```

        Example of a mapping:
            ```
            {"Y": "Yes", "1588550057999": "Yes"}
            ```
        """
        warn_file = log_files[1]
        questions_map = {}
        answers_map = {}

        submission_model_class = POLLS_SUBMISSIONS_MAPPING.get(survey_type)

        studentmodule_qs = StudentModule.objects.filter(
            created__lte=last_sub_creation_date,
            course_id=course_id,
            module_type=self.MODULE_TYPE,
            module_state_key=UsageKey.from_string(xblock_key),
        )
        for sm_sub in studentmodule_qs:
            parsed_sm_subs = self._get_submissions_data(
                sm_sub.state,
                log_data={
                    "xblock_key": xblock_key,
                    "sm_sub": sm_sub,
                },
                log_files=log_files,
            )
            ps_subs = submission_model_class.objects.filter(
                course=course_id,
                student=sm_sub.student,
                submission_date=sm_sub.created,
            )

            # poll_survey submissions mutate, so there might be no related ps_subs
            if not ps_subs:
                continue

            all_questions_mapped = False

            for i, parsed_sm_sub in enumerate(parsed_sm_subs):
                # Questions mapping always fills in earlier than answers', and we can stop
                # updating questions map when complete, to go faster.
                try:
                    if not all_questions_mapped and not questions_map.get(parsed_sm_sub[0]):
                        questions_map[parsed_sm_sub[0]] = ps_subs[i].question.text

                    if not answers_map.get(parsed_sm_sub[1]):
                        answers_map[parsed_sm_sub[1]] = ps_subs[i].answer.text
                except IndexError:
                    # If this happens, it means that corresponding ps_subs haven't been created for
                    # some reason or have been removed.
                    # NOTE: labels not appearing in historical responses won't be processed
                    #  (lost submissions).
                    msg = WARNING_3.format(
                        xblock_key,
                        parsed_sm_sub,
                        ps_subs,
                        questions_map,
                        answers_map,
                    )
                    fprint(warn_file, msg)
                    print(msg)
                    continue

                all_questions_mapped = all_questions_mapped or self._mapping_contains_all(
                    survey_type,
                    questions_map,
                )
                all_answers_mapped = self._mapping_contains_all(
                    survey_type,
                    answers_map,
                    is_questions_map=False,
                )
                if all_questions_mapped and all_answers_mapped:
                    break

        return questions_map, answers_map

    @staticmethod
    def _mapping_contains_all(survey_type, items_map, is_questions_map=True):
        """
        Check if questions or answers mapping contains all items from respective configs.

        It's an additional check to avoid unnecessary calculations.
        """
        config = None
        if survey_type == RATING_POLL_NAME:
            config = RATING_POLL_QUESTIONS_LOW if is_questions_map else RATING_POLL_ANSWERS_LOW
        elif survey_type == COURSE_QUALITY_SURVEY_NAME:
            config = COURSE_QUALITY_SURVEY_QUESTIONS_LOW if is_questions_map else COURSE_QUALITY_SURVEY_ANSWERS_LOW
        elif survey_type == PRE_COURSE_SURVEY_NAME:
            config = PRE_COURSE_SURVEY_QUESTIONS_LOW if is_questions_map else PRE_COURSE_SURVEY_ANSWERS_LOW
        elif survey_type == POST_COURSE_SURVEY_NAME:
            config = POST_COURSE_SURVEY_QUESTIONS_LOW if is_questions_map else POST_COURSE_SURVEY_ANSWERS_LOW

        map_values = items_map.values()
        for conf in config:
            if conf not in map_values:
                return False

        return True

    @staticmethod
    def _get_submissions_data(submission_state, log_data, log_files):
        """
        Parse a submission state and return choices.

        Arguments:
            submission_state (str): submission state from the `courseware_studentmodule` table.
                Example of state (str):
                    ```
                    '{"submissions_count": 1, "choices": {"enjoy": "Y", "recommend": "Y"}}'
                    ```
        Returns:
            submission data (tuple): tuple of tuples: questions/answers data of a submission.
                Nested tuple contains a question label and answer label.
                     Example:
                     ```
                     (("enjoy", "Y"), ("recommend", "Y"))
                     ```
        """
        warn_file = log_files[1]
        data = []
        # FIXME: should have used ordered dict in process_historical_polls_data.py / process_historical_surveys_data.py
        choices = json.loads(submission_state).get("choices")
        if choices:
            for key, value in choices.items():
                data.append((key, value))
        else:
            msg = WARNING_4.format(
                submission_state,
                log_data["sm_sub"].pk,
                log_data["xblock_key"],
            )
            fprint(warn_file, msg)
            print(msg)

        return tuple(data)

    @staticmethod
    def _store_submission(question_entry, answer_entry, submission_entry, survey_type, log_data, log_files):
        """
        Persist survey submission data.
        """
        warn_file = log_files[1]
        survey_type = survey_type or REGULAR_SURVEY_NAME
        user = UserService.get_user(user_id=submission_entry.student_id)
        # NOTE that if dedicated type is `RATING_POLL_NAME`,
        # we have to store a rating poll submission with poll questions/answers (not survey)
        submission_model_class = POLLS_SUBMISSIONS_MAPPING.get(survey_type)
        if user and submission_model_class:
            submission, created = submission_model_class.objects.update_or_create(
                student=user,
                course=submission_entry.course_id,
                question=question_entry,
                defaults={
                    "student": user,
                    "course": submission_entry.course_id,
                    "question": question_entry,
                    "answer": answer_entry,
                    "submission_date": submission_entry.created,
                    "employee_id": get_employee_id(user),
                }
            )
            print("A survey submission {!s} has been {!s}.".format(
                submission,
                "created" if created else "updated",
            ))
        else:
            msg = WARNING_5.format(
                submission_entry.pk,
                log_data["xblock_key"],
                submission_entry.student_id,
            )
            fprint(warn_file, msg)
            print(msg)
