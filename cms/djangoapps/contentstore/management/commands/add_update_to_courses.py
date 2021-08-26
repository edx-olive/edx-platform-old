"""
Usage example:

cd /edx/app/edxapp/edx-platform
sudo -u www-data /edx/bin/python.edxapp ./manage.py cms --settings=production add_update_to_courses rbuchheit@abinitio.com /u/rbuchheit/new_term_text.html '["GD200", "GD201", "GD202", "GD203"]' "T2018_2019" '{"$NEW_START_DATE" : "August 15", "$END_DATE" : "August 31"}'
"""

import datetime
import io
import sys
import ast

from django.core.management.base import BaseCommand
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locator import CourseLocator
from contentstore.course_info_model import delete_course_update, get_course_updates, update_course_updates
from contentstore.management.commands.utils import user_from_str


class Command(BaseCommand):
    help = '''
    Add updates (info/updates.items.json) to a course, given: the email address of the author,
    the text (formatted as HTML) to add to the updates, a list of course numbers, and the course term.
    The text can reference parameters using $-references. If so, use the replacement_text argument to
    provide a name-value pair for each parameter and its replacement value.
    '''

    def add_arguments(self, parser):
        parser.add_argument('email', help='email address of user adding this update')
        parser.add_argument('update_text', help='absolute path to the HTML file containing the text for the update')
        parser.add_argument('course_nums', help='list of course numbers, for example, ["GD101", "GD203-JA", "AI100"]')
        parser.add_argument('term', help='course term, for example, T2019_2020')
        parser.add_argument(
            'replacement_text',
            help='name-value pairs for replacing $-references in the text, for example, '
                 '{"$NEW_START_DATE" : "August 15", "$END_DATE" : "August 31"}'
        )

    def handle(self, *args, **options):
        email = options['email']
        update_text = options['update_text']
        course_nums = ast.literal_eval(options['course_nums'])
        term = options['term']
        replacement_text = ast.literal_eval(options['replacement_text'])

        module_store = modulestore()

        user_object = user_from_str(email)

        with io.open(update_text, 'r', encoding='utf8') as update_text_file:
            update_contents = update_text_file.read()
        update_text_file.close()

        for n, v in replacement_text.items():
            update_contents = update_contents.replace(n, v)

        print(update_contents)
        print("-----")
        print("This update will be added to the course updates in the courses {0}".format(", ".join(course_nums)))
        print("-----")
        response = input(
            'If the updated text above is correct, and you wish to add it to the listed courses, enter Y > '
        )

        if response != "Y":
            print(
                "Exiting this command. Edit the file {0} to correct it, "
                "and then run the command again.".format(update_text)
            )
            sys.exit(1)
        else:
            for c in course_nums:
                course_key = CourseLocator('AbInitioSoftware', c, term)
                course = module_store.get_course(course_key)
                updates_usage_key = course.id.make_usage_key('course_info', 'updates')

                update = {"date": datetime.date.today().strftime("%B %d, %Y"), "content": update_contents}
                update_course_updates(updates_usage_key, update, passed_id=None, user=user_object)
