"""
Functionality to store Saba credits completion results.
"""
from __future__ import print_function
import csv
from datetime import datetime
from optparse import make_option
import os
import sys
import time
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError

from courseware.models import StudentModule


def _create_log_files():
    """
    Create log files to store results of the command.

    One-time operation. Supposed to remove logs afterwards.

    Filepath example: '/edx/app/edxapp/data/saba_credits_data/saba_credits_success_15900699480.txt'
    """

    # Create `/edx/app/edxapp/data/saba_credits_data` dir if non-existent.
    # Using `/edx/app/edxapp/data`, not `/edx/var/`, because of write permissions availability.
    # NOTE: `GITHUB_REPO_ROOT` contains clonned repos of courses
    #  imported via /sysadmin/courses, and third-party modifications can break
    #  the "Load new course from GitHub" functionality.
    saba_credits_data_path = settings.GITHUB_REPO_ROOT / "saba_credits_data"
    # `settings.GITHUB_REPO_ROOT` is of `Path` type
    if not saba_credits_data_path.isdir():
        saba_credits_data_path.mkdir()

    # Mark files with (modified) timestamps to distinguish between command runs
    now = str(time.mktime(datetime.now().timetuple())).replace(".", "")
    success_filepath = os.path.join(
        str(saba_credits_data_path),
        "saba_credits_out_{}.txt".format(now)
    )
    error_filepath = os.path.join(
        str(saba_credits_data_path),
        "saba_credits_err_{}.txt".format(now)
    )

    return success_filepath, error_filepath


def fprint(filename, *args, **kwargs):
    """
    Redirect print to a particular file.

    Ref.: https://stackoverflow.com/a/14981125
    Avoiding global effects: https://stackoverflow.com/a/51340381
    """
    print(*args, file=filename, **kwargs)


def _process_data(row, row_number, err_file, out_file):
    """
    Parse and process a data row.

    Don't stop if any error occurs.

    Have to pass in stdout success and error files to avoid
    re-opening the files in `fprint`.

    Error logs file will get all unexpected cases.

    `row` example:
    ```
        ['staff@example.com;"2017-06-10 09:43:56.535934";"Complete";"course-v1:PDE1+210+210"']
    ```
    """
    data = row[0].replace('"', '').split(";")

    user_id = data[0]  # email; user_id field in Saba services.
    credit_requested_date = data[1]  # updated_on in Saba services.
    credit_completion_status = data[2]
    course_id = data[3]

    course_id_msg = "==== Row #{!s}: no valid course id defined for an entry; skipping. Email: " \
        "'{!s}', completion status: '{!s}', course id: '{!s}'.".format(
             row_number, user_id, credit_completion_status, course_id
        )

    if not course_id:
        # We expect certain number of entries (~4K) to not have course id,
        # that's why success file.
        fprint(out_file, course_id_msg)
        return

    if not user_id:
        fprint(
            out_file,
            "==== Row #{!s}: won't process the row because an "
            "input user email is undefined. Email: '{!s}', "
            "course id: '{!s}', completion status: '{!s}'.".format(
                row_number, user_id, course_id, credit_completion_status
            )
        )
        return

    if not credit_completion_status:
        credit_completion_status_msg = "==== Row #{!s}: won't process the row because " \
            "a completion status is undefined. Email: '{!s}', " \
            "course id: '{!s}', completion status: '{!s}'.".format(
                row_number, user_id, course_id, credit_completion_status
            )
        fprint(out_file, credit_completion_status_msg)
        return

    try:
        course_key = CourseKey.from_string(course_id)
        if not course_key:
            raise ValueError
    except (InvalidKeyError, ValueError):
        # Not an error: we expect input course_id to have invalid values, e.g. "-", "\n".
        fprint(out_file, "{} Error occurred creating 'CourseKey'.".format(course_id_msg))
        return

    user = User.objects.filter(email=user_id).first()
    if user:
        # NOTE: should write this function as a function that returns the result of the operation,
        #  and then, separately, write the result to the files (CR comments).
        _store_saba_credit_completion_state(
            user,
            course_key,
            credit_completion_status,
            credit_requested_date,
            row_number=row_number,
            err_file=err_file,
            out_file=out_file,
        )
    else:
        user_id_error_msg = "==== Row #{!s}: won't process the row because " \
            "a matching user doesn't exist. Email: '{!s}', " \
            "course id: '{!s}', completion status: '{!s}'.".format(
                row_number, user_id, course_id, credit_completion_status
            )
        if not user:
            # The only case classified as an error (that we really hit)
            fprint(err_file, user_id_error_msg)
            return

        # Generic case; not supposed to reach here.
        fprint(
            err_file,
            "==== Row #{!s}: won't process the row "
            "because matching or input data are absent. "
            "Email: '{!s}', course id: '{!s}', completion status: '{!s}'.".format(
                row_number, user_id, course_id, credit_completion_status
            )
        )


def _store_saba_credit_completion_state(
        user, course_id, credit_completion_status,
        credit_requested_date, row_number, out_file, err_file):
    """
    Update student's submission with Saba credit data.

    Log the results.

    It's enough to update the latest entry,
    as we return one in `courseware.views.credit_requested_details`.
    """
    qs = StudentModule.objects.filter(
        student=user,
        course_id=course_id,
        module_type="course",
    )
    if qs.exists():
        exam = qs.latest("created")
        state = json.loads(exam.state) if exam else {}
        # We won't update retro entries w/o "credit_requested" date, on purpose.
        if exam and state.get("credit_requested"):
            # "2020-05-22 09:58:00.000000" (format already compatible)
            state["credit_requested"] = credit_requested_date
            state["credit_completion_status"] = credit_completion_status
            try:
                exam.state = json.dumps(state)
            except TypeError:
                fprint(
                    err_file,
                    "==== Row #{!s}: unable to serialize the submission state. "
                    "Email: '{!s}', course id: '{!s}', completion status: '{!s}'.".format(
                        row_number, user.email, course_id, credit_completion_status
                    )
                )
            exam.save()
            fprint(
                out_file,
                "==== Row #{!s}: successfully updated the "
                "credit completion status.".format(row_number)
            )
        else:
            # Absence of exam entry or credit state in it isn't our problem here.
            fprint(
                out_file,
                "==== Row #{!s}: won't update credit completion status, "
                "not enough prerequisites (absent exam entry or no "
                "historical credit state stored). "
                "Email: '{!s}', course id: '{!s}', completion status: '{!s}'.".format(
                    row_number, user.email, course_id, credit_completion_status
                )
            )
    else:
        # It's not an error per se; if there's no matching entry, we don't care
        fprint(
            out_file,
            "==== Row #{!s}: won't update credit completion status, "
            "a matching StudentModule entry doesn't exist. "
            "Email: '{!s}', course id: '{!s}', completion status: '{!s}'.".format(
                row_number, user.email, course_id, credit_completion_status
            )
        )


class Command(BaseCommand):
    """
    Command to store Saba credits completion results.

    Process retro data as per AMATX-281.
    ~700K entries to process.

    Input file example, to support understanding and unit tests:
    `lms/djangoapps/courseware/management/commands/tests/saba_credits_data.csv`

    Data in an input file should be sorted by the "updated date" in ascending order.

    Commands examples:
    ```
    ./manage.py lms store_saba_credits_statuses --settings=devstack --input_file="path_to_dir/input.csv"
    ./manage.py lms store_saba_credits_statuses --settings=devstack --input_file="path_to_dir/input.csv" --start_from_row=5
    ```
    """
    args = ""
    help = "Store Saba credits completion results in StudentModule."

    option_list = BaseCommand.option_list + (
        make_option("--start_from_row",
                    dest="start_from_row",
                    type="long",
                    help="Row number to start processing from (including). "
                         "Numeration start from 1."),
        make_option("--input_file_path",
                    dest="input_file_path",
                    type="string",
                    help="Path to a CSV file with data to process. "
                         "Refer to an example mentioned in the command docstring."),
    )

    def handle(self, *args, **options):
        """
        Store Saba credits completion results.
        """
        print(
            "======== Start. Stdout will be redirected to dedicated files "
            "in '/edx/app/edxapp/data/saba_credits_data'. ========"
        )

        input_file_path = options.get("input_file_path")
        start_from_row = options.get("start_from_row")

        if start_from_row and start_from_row < 1:
            raise ValueError("Argument 'start_from_row' should not be smaller than 1.")

        if not os.path.exists(input_file_path):
            raise ValueError("Provide an existing input filename.")

        if not input_file_path.endswith(".csv"):
            raise ValueError("Provide a CSV input file.")

        success_log_path, error_log_path = _create_log_files()

        with open(success_log_path, "w+") as out_file, open(error_log_path, "w+") as err_file:

            with open(input_file_path, "r") as csv_file:

                if start_from_row:
                    # Skip rows; ref.: https://stackoverflow.com/a/31894107
                    reader = csv.reader(islice(csv_file, start=start_from_row - 1, stop=None))
                else:
                    reader = csv.reader(csv_file)

                # Go through all (remaining) rows
                # In the logs, actual row number matters
                counter = 0
                for j, row in enumerate(reader, start=start_from_row or 1):
                    _process_data(row, row_number=j, out_file=out_file, err_file=err_file)
                    counter += 1

        print("======== Processed {} entries. The End. ========".format(counter))
