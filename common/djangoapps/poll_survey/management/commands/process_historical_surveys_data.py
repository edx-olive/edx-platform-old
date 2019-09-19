"""Save historical surveys to the `poll_survey` tables."""

from datetime import datetime
import json
from optparse import make_option

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from courseware.models import StudentModule
from poll_survey.management.commands.commands_utils import (
    fetch_xblock,
    get_comma_separated_args,
    prepare_submissions_entries,
    UserService
)
from poll_survey.models import SurveyAnswerOption, SurveyQuestion, SurveySubmission


class Command(BaseCommand):
    """
    Command to store historical surveys data in `poll_survey` tables.

    Examples of command to execute on devstack:
    ```
    ./manage.py lms --settings=devstack process_historical_surveys_data --courses_ids="course-v1:RG+CS101+2019_T1, course-v1:edX+DemoX+Demo_Course"
    ./manage.py lms --settings=devstack process_historical_surveys_data --exclude_ids="129L, 130L" --chunk_size=5
    ```
    """

    MODULE_TYPE = "survey"
    CHUNK_SIZE = 2000
    FROM_PK = 1L
    SUBMISSION_DATE_TO = "2019-9-13"
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
                    default=SUBMISSION_DATE_TO,
                    help="Student submissions date to fetch entries TO. Format: YYYY-MM-DD, e.g. '2019-09-13'"),
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
        courses_ids = [CourseKey.from_string(k) for k in options.get("courses_ids")] \
            if options.get("courses_ids") else None
        chunk_size = options.get("chunk_size")
        from_pk = options.get("from_pk")
        submission_date_to = datetime.strptime(options.get("submission_date_to"), '%Y-%m-%d')
        measure = options.get("measure")

        # TODO use chained querysets
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
                            question_entry = self._get_or_create_question(question)
                            # We store answers appeared in submissions only
                            answer_entry = self._get_or_create_answer(answer)
                            if question_entry and answer_entry:
                                self._store_submission(question_entry, answer_entry, submission_entry)
                            else:
                                print("A question or an answer couldn't be persisted. "
                                      "Won't persist the submission either.")
                        else:
                            print("A question or an answer must have been removed from the xblock. "
                                  "Won't persist the submission.")
                processed_subs_counter += 1
                print("Processed {!s} survey xblock submissions (submissions entries).".format(processed_subs_counter))
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

    @staticmethod
    def _get_or_create_question(question):
        """
        Persist a question.

        Arguments:
            question (list): question data
                Example:
                ```
                ['enjoy', {'img': '', 'img_alt': '', 'label': 'Are you enjoying the course?'}]
                ```
        """
        text = question[1]["label"].strip().lower()  # Strict check
        data = {"text": text, "is_default": True}
        if question[1]["img"] and question[1]["img_alt"]:
            # Images info doesn't really matter (we won't query against it anyway),
            # so it's ok to lose it during next iterations
            data["image_url"] = question[1]["img"]
            data["image_alt_text"] = question[1]["img_alt"]
        question_entry, _ = SurveyQuestion.objects.get_or_create(
            text=text,
            is_default=True,
            defaults=data
        )
        print("Processed/persisted a survey question: {!s}".format(question_entry))
        return question_entry

    @staticmethod
    def _get_or_create_answer(answer):
        """
        Persist an answer.

        Arguments:
            answer (list): answer data
                Example:
                ```
                ['Y', 'Yes']
                ```
        """
        text = answer[1].strip().lower()  # Strict check
        answer_entry, created = SurveyAnswerOption.objects.get_or_create(
            text=text,
            defaults={"text": text}
        )
        print("Processed/persisted a survey answer: {!s}".format(answer_entry))
        return answer_entry

    @staticmethod
    def _store_submission(question_entry, answer_entry, submission_entry):
        """Persist survey submission data."""
        user = UserService.get_user(user_id=submission_entry.student_id)
        if user:
            # Xblock submissions are immutable; store the latest submission
            submission, created = SurveySubmission.objects.update_or_create(
                student=user,
                course=submission_entry.course_id,
                question=question_entry,
                defaults={
                    "student": user,
                    "course": submission_entry.course_id,
                    "question": question_entry,
                    "answer": answer_entry,
                    "submission_date": submission_entry.created
                }
            )
            print("A survey submission {!s} has been persisted.".format(submission))
        else:
            print("Could not store a survey submission. "
                  "No user with id {!s} was found.".format(submission_entry.student_id))
