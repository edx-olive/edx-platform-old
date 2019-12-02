"""Save historical polls to the `poll_survey` tables."""

from datetime import datetime
import json
from optparse import make_option

from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from courseware.models import StudentModule
from poll_survey.management.commands.utils.commands_utils import (
    fetch_xblock,
    get_comma_separated_args,
    get_employee_id,
    prepare_submissions_entries,
    UserService
)
from poll_survey.models import PollAnswerOption, PollQuestion, PollSubmission


class Command(BaseCommand):
    """
    Command to store historical polls data in `poll_survey` tables.

    Examples of command to execute on devstack:
    ```
    ./manage.py lms --settings=devstack process_historical_polls_data --courses_ids="course-v1:RG+CS101+2019_T1, course-v1:edX+DemoX+Demo_Course" --submission_date_to="2019-11-15"
    ./manage.py lms --settings=devstack process_historical_polls_data --exclude_ids="1L, 2L" --chunk_size=5 --submission_date_to="2019-11-15"
    ```
    """

    MODULE_TYPE = "poll"
    CHUNK_SIZE = 2000
    FROM_PK = 1L

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
                    type="long",
                    default=FROM_PK,
                    help="PK of a student xblock submission to start from (from the 'courseware_studentmodule' table)."),
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

        Example of "poll" submission `state`:
            ```
            {"submissions_count": 2, "choice": "7"}
            ```
        """
        print("Processing historical polls...")

        exclude_ids = options.get("exclude_ids")
        courses_ids = [CourseKey.from_string(k.strip()) for k in options.get("courses_ids")] \
            if options.get("courses_ids") else None
        chunk_size = options.get("chunk_size")
        from_pk = options.get("from_pk")
        submission_date_to = datetime.strptime(options.get("submission_date_to"), '%Y-%m-%d')

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
            print("Found {!s} poll xblock submissions.".format(subs_count))
        else:
            print("No poll xblock submissions found.")
            return

        processed_subs_counter = 0

        for offset in range(0, subs_count, chunk_size):
            print("===================================offset: {!s}====================================\n"
                  "===================================================================================\n"                  
                  "Starting to process poll XBlock submissions from {!s} to {!s}."
                  .format(offset, offset, chunk_size+offset))
            for submission_entry in prepare_submissions_entries(module_type=self.MODULE_TYPE, exclude_ids=exclude_ids,
                                                                offset=offset, chunk_size=chunk_size, from_pk=from_pk,
                                                                submission_date_to=submission_date_to,
                                                                courses_ids=courses_ids):
                print("=============submission entry {!s}=============".format(submission_entry.id))
                xblock = fetch_xblock(module_state_key=submission_entry.module_state_key)
                if xblock:
                    # There's always a single submission to extract from poll module `state`
                    submission = self._get_submission_data(submission_entry.state)
                    question = None
                    answer = None
                    print("Parsed submission data for a submission entry with PK {!s}".format(submission_entry.id))
                    if submission:
                        print("Starting to process submission data: {!s}".format(submission))
                        question = xblock.question
                        answer = self._get_item(label=submission, items=xblock.answers)
                    if question and answer:
                        # Persist poll structure before to save submissions.
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
                print("Processed {!s} poll xblock submissions (submissions entries) out of {!s}.".format(
                    processed_subs_counter,
                    subs_count
                ))
                print("Latest processed submission entry id - {!s}, submission date - {!s}"
                      .format(submission_entry.id, submission_entry.created))
                print("Current offset: {!s}".format(offset))
        print("============= THE END. =============")

    @staticmethod
    def _get_submission_data(submission_state):
        """
        Parse a submission state and return a choice.

        Arguments:
            submission_state (str): submission state from the `courseware_studentmodule` table.
                Example of state (str):
                    ```
                    '{"submissions_count": 2, "choice": "7"}'
                    ```
        Returns:
            submission data (str): Label of an answer submitted by a user.
                     Example:
                     ```
                     "Y"  # for text "Yes"
                     ```
        """
        choice = json.loads(submission_state).get("choice")
        if choice:
            return choice
        else:
            print("Choice is null in a poll submission state {!s}. "
                  "Won't persist a submission.".format(submission_state))

    @staticmethod
    def _get_item(label, items):
        """
        Look up a answer by label.

        For poll, we lookup answers only
        (there's always a single question in a poll).

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
            question (str): question data (question text itself).
                Example:
                ```
                'Are you enjoying the course?'
                ```
        """
        text = question.strip().lower()  # Strict check
        data = {"text": text, "is_default": True}
        question_entry, _ = PollQuestion.get_first_or_create(data)
        print("Processed/persisted a poll question: {!s}".format(question_entry))
        return question_entry

    @staticmethod
    def _get_or_create_answer(answer):
        """
        Persist an answer.

        Arguments:
            answer (list): answer data
                Example:
                ```
                ['R', {'img': '', 'img_alt': '', 'label': 'Red'}]
                ```
        """
        text = answer[1]["label"].strip().lower()  # Strict check
        data = {
            "text": text,
            # Images info doesn't really matter (we won't query against it anyway)
            "image_url": answer[1]["img"] or None,
            "image_alt_text": answer[1]["img_alt"] or None,
        }
        answer_entry, _ = PollAnswerOption.get_first_or_create(data)
        print("Processed/persisted a poll answer: {!s}".format(answer_entry))
        return answer_entry

    @staticmethod
    def _store_submission(question_entry, answer_entry, submission_entry):
        """Persist poll submission data."""
        user = UserService.get_user(user_id=submission_entry.student_id)
        if user:
            # Xblock submissions are immutable; store the latest submission
            submission, created = PollSubmission.objects.update_or_create(
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
            print("A poll submission {!s} has been persisted.".format(submission))
        else:
            print("Could not store a poll submission. "
                  "No user with id {!s} was found.".format(submission_entry.student_id))
