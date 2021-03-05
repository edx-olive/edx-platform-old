"""
Management command to generate a report
that includes when students'submitted their credits for a course.
"""
import csv
from datetime import datetime
import json
import os
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from courseware.models import StudentModule


class Command(BaseCommand):
    """
    Management command for generate_course_completion_report
    """

    help = """
    Generate a report for all students
    that are completed a course.

    CSV will include the following:
        "Course ID"
        "Employee ID"
        "Work mail"
        "Completion Date"

    Outputs grades to a csv file.

    Example (Run as edxapp user):
        source ~edxapp/edxapp_env
        ./manage.py lms generate_course_completion_report -o /tmp/temp_report.csv --settings=aws
    """

    option_list = BaseCommand.option_list + (
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='Course ID for grade distribution'),
        make_option('-o', '--output',
                    metavar='FILE',
                    dest='output',
                    default=False,
                    help='Filename for grade output'))

    def handle(self, *args, **options):
        if os.path.exists(options['output']):
            raise CommandError("File {0} already exists".format(
                options['output']))

        rows = []
        courses = []
        # parse out the course into a coursekey
        if options['course']:
            try:
                course_key = CourseKey.from_string(options['course'])
            # if it's not a new-style course key, parse it from an old-style
            # course key
            except InvalidKeyError:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(options['course'])
            courses = [course_key]
        else:
            courses = [
                "course-v1:appliedx+SBC-101+all",
                "course-v1:appliedx+CIFX+2020_Q2",
                "course-v1:appliedx+CIFX-ITALIAN+2020_Q2",
                "course-v1:appliedx+CIFX-GERMAN+2020_Q2",
                "course-v1:appliedx+CIFX-HEBREW+2020_Q2",
                "course-v1:appliedx+CIFX-JAPANESE+2020_Q2",
                "course-v1:appliedx+CIFX-CHINESE-CHINA+2020_Q2",
                "course-v1:appliedx+CIFX-CHINESE-TAIWAN+2020_Q2",
                "course-v1:appliedx+CIFX-KOREAN+2020_Q2",
                "course-v1:appliedx+INFSECPRIV-FRENCH+2020_Q4",
                "course-v1:appliedx+INFSECPRIV+2021_Q1",
                "course-v1:appliedx+INFSECPRIV+2020_Q3",
                "course-v1:appliedx+INFSECPRIV-GERMAN+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-ITALIAN+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-HEBREW+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-TRADITIONAL-CHINESE+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-SIMPLIFIED-CHINESE+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-JAPANESE+2020_Q4",
                "course-v1:appliedx+INFSECPRIV-KOREAN+2020_Q4",
            ]
            courses = [CourseKey.from_string(c_id) for c_id in courses]

        rows.append(["Course ID", "Employee ID", "Work mail", "Completion Date"])

        for count, exam in enumerate(StudentModule.objects.filter(
                                        course_id__in=courses, module_type="course").iterator()):
            try:
                state = json.loads(exam.state)
            except ValueError:
                continue

            credit_completion_status = state.get("credit_completion_status")

            request_date = None
            if credit_completion_status == "Complete":
                request_date = datetime.strptime(
                    state.get("credit_requested", ""), "%Y-%m-%d %H:%M:%S.%f")
            else:
                continue

            rows.append([exam.course_id, exam.student.profile.employee_id, exam.student.email, request_date])

        with open(options['output'], 'wb') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
