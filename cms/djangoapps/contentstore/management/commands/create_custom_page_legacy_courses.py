"""
Create a custom AMAT page in existing courses.

"""
from __future__ import print_function

import logging
import os
import time
from datetime import datetime
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from cms.djangoapps.contentstore.views.course import _create_custom_static_page
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from path import Path
from xmodule.modulestore.django import modulestore

CONTENTSTORE_BASE_DIR = Path(__file__).parent.parent.parent


class DummyRequest(object):
    """
    Dummy request to pass in to the management command.

    Mimic required Django request functionality.
    """

    def is_secure(self):
        return True


def _create_log_files():
    """
    Create log files to store results of the command.

    Create `/edx/app/edxapp/data/amat_customizations` dir if non-existent.
    Using `/edx/app/edxapp/data`, not `/edx/var/`, because of write permissions availability.
    NOTE: consider moving here all AMAT dirs e.g. "poll_survey_commands_data".

    NOTE: `GITHUB_REPO_ROOT` contains cloned repos of courses
     imported via /sysadmin/courses, and third-party modifications can break
     the "Load new course from GitHub" functionality.

    Examples:
    '/edx/app/edxapp/data/amat_customizations/courses_custom_page_success_15900699480.txt'
    '/edx/app/edxapp/data/amat_customizations/courses_custom_page_error_15900699480.txt'
    """
    # Workaround: the Path obj corresponds to the `settings.GITHUB_REPO_ROOT` value,
    #  as it appears in the `common` pkg.
    amat_data_data_path = Path('/edx/app/edxapp/data') / "amat_customizations"
    # `settings.GITHUB_REPO_ROOT` is of `Path` type
    if not amat_data_data_path.isdir():
        amat_data_data_path.mkdir()

    # Mark files with (modified) timestamps to distinguish between command runs
    now = str(time.mktime(datetime.now().timetuple())).replace(".", "")
    info_filepath = os.path.join(
        str(amat_data_data_path),
        "courses_custom_page_success_{}.txt".format(now)
    )
    warning_filepath = os.path.join(
        str(amat_data_data_path),
        "courses_custom_page_error_{}.txt".format(now)
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
    Command to create a custom AMAT page in existing courses.

    Additional conditions:
    - page location: after "About the Course" page;
    - add the page only if doesn't exist already.

    2 files serve as additional output:
    - a file containing list of the courses with a custom page, e.g.
      '/edx/app/edxapp/data/amat_customizations/courses_custom_page_success_15900699480.txt'
    - a file containing list of the courses we failed to add a custom page to, e.g.
      '/edx/app/edxapp/data/amat_customizations/courses_custom_page_error_15900699480.txt'

    Example:
    ```
    ./manage.py cms --settings=devstack create_custom_page_legacy_courses
    ```
    """

    help = "Create a custom AMAT page in legacy courses"

    CHUNK_SIZE = 2000
    FROM_OFFSET = 0

    org_to_exclude = "EngineeringIT"
    username = "staff"

    option_list = BaseCommand.option_list + (
        make_option("--from_offset",
                    dest="from_offset",
                    type="long",
                    default=FROM_OFFSET,
                    help="Positional index of a CourseOverview entry to start processing from "
                         "(including)."),
        make_option("--chunk_size",
                    dest="chunk_size",
                    type="int",
                    default=CHUNK_SIZE,
                    help="Number of entries in a chunk to process."),
    )

    def handle(self, *args, **options):
        """
        Create a custom AMAT page in existing courses.
        """
        logging.disable(logging.CRITICAL)

        tab_content = None
        with open(CONTENTSTORE_BASE_DIR / "views/course_static_tab_content.html") as tab_content_file:
            tab_content = tab_content_file.read()

        chunk_size = options.get("chunk_size")
        # `CourseOverview` has course key for PK, so we are left with slicing
        from_offset = options.get("from_offset")

        qs = CourseOverview.objects.exclude(org=self.org_to_exclude)[from_offset:]

        found_entries_n = qs.count()

        print("============= Found {!s} CourseOverview entries. =============\n".format(
            found_entries_n,
        ))

        if not found_entries_n:
            return

        current_entry_index = 0
        success_n = 0
        error_n = 0

        user = User.objects.filter(username=self.username).first()
        request = DummyRequest()
        request.user = user

        if not user:
            print("No user {!s} found.".format(self.username))
            return

        success_filepath, error_filepath = _create_log_files()
        start = datetime.now()

        with open(success_filepath, "w+") as success_file, open(error_filepath, "w+") as err_file:

            for offset in range(0, found_entries_n, chunk_size):
                print("offset " + str(offset))

                courses_overviews = qs[offset:chunk_size+offset]

                for course_overview in courses_overviews:

                    # We have a `course` module, `cms/djangoapps/contentstore/views/course.py`,
                    # so the `kourse` naming is to avoid any confusion.
                    kourse = modulestore().get_course(course_overview.id)

                    print(
                        "-------- Course : {!s}. "
                        "Entry index: {!s}. Offset: {!s}".format(
                            kourse.id,
                            current_entry_index,
                            offset,
                        ))

                    try:
                        if not tab_content:
                            raise ValueError("No static tab content provided.")
                        _create_custom_static_page(
                            request,
                            kourse,
                            tab_content,
                            update_custom_tabs_order=True,
                        )
                        # We don't know if a new tab has just been added, or existed already.
                        print("Successfully processed the course {!s}.".format(kourse.id))
                        fprint(success_file, str(kourse.id))
                        success_n += 1
                    except Exception as e:
                        print(
                            "An error happened when trying to add "
                            "a custom page to the course {!s} : {!s}.".format(
                                kourse.id,
                                e,
                            ))
                        fprint(err_file, str(kourse.id))
                        error_n += 1

                    current_entry_index += 1

        finish = datetime.now()
        duration = (finish - start).microseconds

        logging.disable(logging.NOTSET)

        if from_offset:
            print("\n============= Processed {!s} CourseOverview entries, with 'from_offset' equal to {!s}. =============".format(current_entry_index + 1, from_offset))
        else:
            print("\n============= Processed {!s} CourseOverview entries out of {!s}. =============".format(current_entry_index + 1, found_entries_n))

        print("============= It took {!s} microseconds to process all entries. =============".format(duration))

        print("\n============= Success: {!s} entries. =============".format(success_n))
        print("============= Errors: {!s} entries. =============".format(error_n))

        print("\n============= THE END. =============\n")
