"""
Usage example:

cd /edx/app/edxapp/edx-platform
sudo -u www-data /edx/bin/python.edxapp ./manage.py lms  --settings=production find_upload_userid course-v1:AbInitioSoftware+GD301+T2019_2020 564ef804cafc7ffe32359914ce524d6060a7fac2
"""

from django.core.management.base import BaseCommand
from submissions.api import get_all_course_submission_information
from student.models import user_by_anonymous_id


class Command(BaseCommand):
    help = '''
    Given a course id and filename (SHA1-hash) for a student upload,
    return the username of the student who uploaded the file.
    '''

    def add_arguments(self, parser):
        parser.add_argument(
            'course_id',
            help='full course id of the course to search, e.g., course-v1:AbInitioSoftware+GD301+T2019_2020'
        )
        parser.add_argument(
            'upload_id',
            help='sha1 hash that identifies the upload, e.g., 564ef804cafc7ffe32359914ce524d6060a7fac2'
        )

    def handle(self, *args, **options):
        course_id = options['course_id']
        upload_id = options['upload_id'].encode("utf-8")
        anonymous_uid = ""
        username = ""

        for s in get_all_course_submission_information(course_id, 'sga'):
            if s[1]['answer']['sha1'] == upload_id:
                anonymous_uid = s[0]['student_id']

        if anonymous_uid != "":
            username = user_by_anonymous_id(anonymous_uid).username.encode("ascii")

        print("The user who uploaded {0} for course {1} is: {2}".format(upload_id, course_id, username))
