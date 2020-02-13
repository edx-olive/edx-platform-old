"""Save historical surveys to the `poll_survey` tables."""

from datetime import datetime
import json
from optparse import make_option

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from courseware.models import StudentModule
from poll_survey.configs import RATING_POLL_NAME, REGULAR_SURVEY_NAME, POLLS_SUBMISSIONS_MAPPING
from poll_survey.management.commands.process_historical_polls_data import Command as PollCommand
from poll_survey.management.commands.utils.commands_utils import (
    fetch_xblock,
    get_comma_separated_args,
    get_employee_id,
    prepare_submissions_entries,
    UserService
)
from poll_survey.management.commands.utils.configs import (
    DEDICATED_POLLS_NAMES_TO_MIGRATE,
    POLLS_ELEMENTS_NAMES_MAPPING,
)
from poll_survey.models import SurveyAnswerOption, SurveyQuestion


class Command(BaseCommand):
    """
    Command to store historical surveys data in `poll_survey` tables.

    Examples of command to execute on devstack:
    ```
    ./manage.py lms --settings=devstack process_historical_surveys_data --courses_ids="course-v1:RG+CS101+2019_T1, course-v1:edX+DemoX+Demo_Course" --submission_date_to="2019-11-15"
    ./manage.py lms --settings=devstack process_historical_surveys_data --exclude_ids="129L, 130L" --chunk_size=5 --submission_date_to="2019-11-15"
    ```
    """

    MODULE_TYPE = "survey"
    CHUNK_SIZE = 2000
    FROM_PK = 1L
    MEASURE = 0

    args = ""
    help = "Store historical polls data in poll_survey tables"
    option_list = BaseCommand.option_list + (
        make_option("--exclude_ids",
                    dest="exclude_ids",
                    type="string",
                    action="callback",
                    callback=get_comma_separated_args,
                    help="Exclude processed xblock submissions ids ('courseware_studentmodule' table)."),
        make_option("--courses_ids",
                    dest="courses_ids",
                    type="string",
                    action="callback",
                    callback=get_comma_separated_args,
                    help="Run the command for particular courses only. Course id should be of the standard course key "
                         "format, e.g. 'course-v1:RF+CS101+2019_T1'"),
        make_option("--submission_date_to",
                    dest="submission_date_to",
                    type="string",
                    help="Student submissions date (will fetch entries created before this date). "
                         "Format: YYYY-MM-DD, e.g. '2019-09-13'"),
        make_option("--from_pk",
                    dest="from_pk",
                    default=FROM_PK,
                    type="long",
                    help="PK of a student xblock submission to start from (from the 'courseware_studentmodule' table)."),
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
        Save polls historical data.

        Store both polls structure (questions and answers)
        and submissions.

        All questions and answers will be marked default.
        We don't need to store question/answer links.

        If an xblock was removed from the courseware, we won't be able to
        fetch its structure (questions/answers), thus respective submissions
        won't be stored.

        We ignore `module_type`'s other than "poll" and "survey" (e.g. "open_ended_survey"),
        as they've been introduced together with the "poll_survey" app
        i.e. there's no historical data for other module types.

        Example of "survey" submission `state`:
            ```
            {"submissions_count": 2, "choices": {"enjoy": "Y", "learn": "Y", "1561550057662": "Y", "recommend": "Y"}}
            ```
        """
        print("Processing historical surveys...")
        exclude_ids = options.get("exclude_ids")
        courses_ids = [CourseKey.from_string(k.strip()) for k in options.get("courses_ids")] \
            if options.get("courses_ids") else None
        chunk_size = options.get("chunk_size")
        from_pk = options.get("from_pk")
        submission_date_to = datetime.strptime(options.get("submission_date_to"), '%Y-%m-%d')
        measure = options.get("measure")

        if courses_ids:
            print("Considering particular courses only: {!s}".format(courses_ids))
            subs_count = StudentModule.objects.filter(
                created__lte=submission_date_to,
                pk__gte=from_pk,
                module_type=self.MODULE_TYPE,
                course_id__in=courses_ids
            ).count()
        else:
            subs_count = StudentModule.objects.filter(
                created__lte=submission_date_to,
                pk__gte=from_pk,
                module_type=self.MODULE_TYPE
            ).count()
        if subs_count:
            print("Found {!s} survey xblock submissions.".format(subs_count))
        else:
            print("No survey xblock submissions found.")
            return

        processed_subs_counter = 0
        sub_processing_time = 0

        for offset in range(0, subs_count, chunk_size):
            print("===================================offset: {!s}====================================\n"
                  "===================================================================================\n"
                  "Starting to process survey XBlock submissions from {!s} to {!s}."
                  .format(offset, offset, chunk_size+offset))
            for submission_entry in prepare_submissions_entries(module_type=self.MODULE_TYPE, exclude_ids=exclude_ids,
                                                                offset=offset, chunk_size=chunk_size, from_pk=from_pk,
                                                                submission_date_to=submission_date_to,
                                                                courses_ids=courses_ids):
                sub_t1 = datetime.now() if measure else 0
                print("=============submission entry {!s}=============".format(submission_entry.id))
                xblock = fetch_xblock(module_state_key=submission_entry.module_state_key)
                if xblock:
                    _, survey_type = self._define_survey_type(xblock)
                    print("XBlock's type is '{!s}'.".format(survey_type))

                    submissions = self._get_submissions_data(submission_entry.state)
                    if submissions:
                        print("Starting to process survey XBlock submissions: {!s}".format(submissions))
                    for submission in submissions:
                        print("-------submission datum-------")
                        print("Starting to process submission data: {!s}".format(submission))
                        question = self._get_item(label=submission[0], items=xblock.questions)
                        answer = self._get_item(label=submission[1], items=xblock.answers)
                        if question and answer:
                            # Persist survey structure before to save submissions.
                            question_entry = self._get_or_create_question(question, survey_type=survey_type)
                            # We store answers appeared in submissions only
                            answer_entry = self._get_or_create_answer(answer, survey_type=survey_type)
                            if question_entry and answer_entry:
                                self._store_submission(
                                    question_entry,
                                    answer_entry,
                                    submission_entry,
                                    survey_type=survey_type
                                )
                            else:
                                print("A question or an answer couldn't be persisted. "
                                      "Won't persist the submission either.")
                        else:
                            print("A question or an answer must have been removed from the xblock. "
                                  "Won't persist the submission.")
                processed_subs_counter += 1
                print("Processed {!s} survey xblock submissions (submissions entries) out of {!s}.".format(
                    processed_subs_counter,
                    subs_count
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
            print("\n\n\nAverage processing time for one submission_entry (out of {!s} entries): {!s} microseconds."
                  .format(processed_subs_counter, float(sub_processing_time / processed_subs_counter)))
        print("============= THE END. =============")

    @staticmethod
    def _get_submissions_data(submission_state):
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
        data = []
        choices = json.loads(submission_state).get("choices")
        if choices:
            for key, value in choices.items():
                data.append((key, value))
        else:
            print("Choices are null in a survey submission state {!s}. "
                  "Won't persist submissions.".format(submission_state))
        return tuple(data)

    @staticmethod
    def _get_item(label, items):
        """
        Look up a question/answer by label.

        Use case: get an xblock question corresponding
        to a submission label.

        Arguments:
            label (str): question label from a submission.
            items (list): questions to search over.

        Returns:
             data (list): either question data, e.g.
                ```
                ['enjoy', {'img': '', 'img_alt': '', 'label': 'Are you enjoying the course?'}]
                ```
                or answer data, e.g.
                ```
                ['Y', 'Yes']
                ```
        """
        for item in items:
            if item[0] == label:
                return item

    def _define_survey_type(self, xblock):
        """
        Check if a survey is a dedicated one and return its type.

        Check if a survey is a dedicated:
        - by its title,
        - by its questions (if applicable),
        - by its answers
        (all should be dedicated).

        Arguments:
            xblock (`xblock.internal.SurveyBlockWithMixins` obj): xblock itself.
                Example of its questions and answers:
                ```
                (Pdb) xblock.answers
                [[u'8', u'aaaaaa'], [u'9', u'aaaa2']]
                (Pdb) xblock.questions
                [[u'6', {u'img': u'', u'img_alt': u'', u'label': u'qqqqq'}],]
                ```
        Returns:
            results (tuple) with check results (True if a survey was recognized as a dedicated
                ones, False otherwise), and survey type.
        """
        for name in DEDICATED_POLLS_NAMES_TO_MIGRATE:
            # Check them all
            title_check = self._check_survey_title_dedicated_type(title=xblock.block_name.strip().lower(), name=name)
            questions_check = self._check_survey_questions_dedicated_type(
                questions=[q[1]["label"].strip().lower() for q in xblock.questions],
                name=name
            )
            answers_check = self._check_survey_answers_dedicated_type(
                answers=[a[1].strip().lower() for a in xblock.answers],
                name=name
            )
            # Names checks are mutually exclusive (well, they should be: see `commands.configs`)
            if title_check and questions_check and answers_check:
                return True, name

        return False, REGULAR_SURVEY_NAME

    @staticmethod
    def _check_survey_title_dedicated_type(title, name):
        """
        Check if a title qualifies as a dedicated survey's one.
        """
        return title == POLLS_ELEMENTS_NAMES_MAPPING.get(name, {}).get("title", "").strip().lower()

    @staticmethod
    def _check_survey_questions_dedicated_type(questions, name):
        """
        Check if all questions qualify as a dedicated survey's ones.
        """
        questions_map = POLLS_ELEMENTS_NAMES_MAPPING.get(name, {}).get("questions", [])
        if not questions_map:
            # If questions aren't configured, validation is passed
            return True
        questions_map_updated = [m.strip().lower() for m in questions_map]
        for question in questions:
            if question not in questions_map_updated:
                return False
        return True

    @staticmethod
    def _check_survey_answers_dedicated_type(answers, name):
        """
        Check if all answers qualify as a dedicated survey's ones.
        """
        answers_map = POLLS_ELEMENTS_NAMES_MAPPING.get(name, {}).get("answers", [])
        if not answers_map:
            # If answers aren't configured, validation is passed
            return True
        answers_map_updated = [m.strip().lower() for m in answers_map]
        for answer in answers:
            if answer not in answers_map_updated:
                return False
        return True

    @staticmethod
    def _get_or_create_question(question, survey_type=REGULAR_SURVEY_NAME):
        """
        Persist a question.

        Arguments:
            question (list): question data
                Example:
                ```
                ['enjoy', {'img': '', 'img_alt': '', 'label': 'Are you enjoying the course?'}]
                ```
        """
        survey_type = survey_type or REGULAR_SURVEY_NAME  # Just in case
        text = question[1]["label"].strip().lower()  # Strict check
        data = {"text": text, "is_default": True}
        if survey_type == RATING_POLL_NAME:
            # Re-define for poll
            # It's so bad... No time to refactor
            question_entry = PollCommand._get_or_create_question(question[1]["label"])
        else:
            # Images info doesn't really matter (we won't query against it anyway)
            data["image_url"] = question[1]["img"] or None
            data["image_alt_text"] = question[1]["img_alt"] or None
            question_entry, _ = SurveyQuestion.get_first_or_create(data)
            print("Processed/persisted a survey question: {!s}".format(question_entry))
        return question_entry

    @staticmethod
    def _get_or_create_answer(answer, survey_type=REGULAR_SURVEY_NAME):
        """
        Persist an answer.

        Arguments:
            answer (list): answer data
                Example:
                ```
                ['Y', 'Yes']
                ```
        """
        survey_type = survey_type or REGULAR_SURVEY_NAME  # Just in case
        text = answer[1].strip().lower()  # Strict check
        answer_entry, _ = SurveyAnswerOption.get_first_or_create(text=text)
        if survey_type == RATING_POLL_NAME:
            # Re-define for poll
            # It's so bad... No time to refactor
            # Example of poll answer:
            #  ['R', {'img': '', 'img_alt': '', 'label': 'Red'}]
            answer_entry = PollCommand._get_or_create_answer(
                answer=[answer[0], {'img': '', 'img_alt': '', 'label': answer[1]}]
            )
        else:
            answer_entry, _ = SurveyAnswerOption.get_first_or_create(text=text)
        print("Processed/persisted a survey answer: {!s}".format(answer_entry))
        return answer_entry

    @staticmethod
    def _store_submission(question_entry, answer_entry, submission_entry, survey_type=REGULAR_SURVEY_NAME):
        """Persist survey submission data."""
        survey_type = survey_type or REGULAR_SURVEY_NAME  # Just in case
        user = UserService.get_user(user_id=submission_entry.student_id)
        # NOTE that if dedicated type is `RATING_POLL_NAME`,
        # we have to store a rating poll with poll questions/answers (not survey)
        submission_model_class = POLLS_SUBMISSIONS_MAPPING.get(survey_type)
        if user and submission_model_class:
            # Xblock submissions are immutable; store the latest submission
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
            print("A survey submission {!s} has been persisted.".format(submission))
        else:
            print("Could not store a survey submission. "
                  "No user with id {!s} was found.".format(submission_entry.student_id))
