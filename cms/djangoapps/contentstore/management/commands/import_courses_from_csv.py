"""
Script for uploading courses from csv file.
"""

import csv
import logging
import os

from pytz import UTC
from datetime import datetime

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File

from cms.djangoapps.contentstore.views.course import create_new_course
from cms.djangoapps.contentstore.views.assets import update_course_run_asset
from xmodule.modulestore.exceptions import DuplicateCourseError


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Create courses from cvs file.
    """
    help = '''
    Create courses from csv file. The file must contain following columns:
    Vendor, CourseAcronym, Course Title, Marketing URL, Picture Name, Price.
    Picture Name column should contain file names from MEDIA_ROOT directory.
    '''

    def add_arguments(self, parser):
        parser.add_argument('file_path')

    def handle(self, *args, **options):
        path = options['file_path']
        user = User.objects.get(email='staff@example.com')
        rows_with_errors = []
        media_files = os.listdir(settings.MEDIA_ROOT)
        with open(path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            line_count = 0
            logger.info('Starting to process the records...')
            for row in csv_reader:
                for col_name in ('Vendor', 'CourseAcronym'):
                    if not row[col_name]:
                        logger.error(
                            f"Cannot create course from record on line {line_count + 1} with "
                            f"Organization: {row['Vendor']}, Course Number: {row['CourseAcronym']}. "
                            f"All these fields are required and cannot be empty."
                        )
                        rows_with_errors.append(line_count + 1)
                        break
                else:
                    try:
                        image_name = ''
                        if row['Picture Name']:
                            # image names are not correct in csv file, so we have to do this :(
                            # in csv file image extension is always .jpg but provided files can have
                            # .png and .jpeg extensions also, so we have to search for correct image first
                            initial_name = row['Picture Name'].split('.')[0]
                            image_name = next((name for name in media_files if name.startswith(initial_name + '.')), '')
                        price = 0
                        price_str = row['Price'].strip()
                        if price_str.startswith('$'):
                            price = round(float(price_str[1:].replace(',', '')))
                        course = create_new_course(
                            user,
                            row['Vendor'],
                            row['CourseAcronym'],
                            '2021',
                            {
                                'display_name': row['Course Title'],
                                'marketing_url': row['Marketing URL'],
                                'course_image': image_name,
                                'start': datetime.strptime(row['Course Start Date'], '%m/%d/%Y').replace(tzinfo=UTC),
                                'enrollment_start': datetime.strptime(
                                    row['Course Enrollment Date'],
                                    '%m/%d/%Y'
                                ).replace(tzinfo=UTC),
                                'cosmetic_display_price': price,
                            }
                        )
                        if image_name:
                            path = settings.MEDIA_ROOT + image_name
                            with open(path, 'rb') as image:
                                file_obj = File(image)
                                # this is just a simple workaround, because update_course_run_asset
                                # function requires the file to have these attributes
                                file_obj.content_type = 'image'
                                file_obj.name = image_name
                                file_obj.multiple_chunks = lambda: False
                                update_course_run_asset(course.id, file_obj)
                            os.remove(path)
                        else:
                            logger.error(
                                f"Could not upload image for record {line_count + 1}, the image does not "
                                f"exist in media directory (image name: {row['Picture Name']}, "
                                f"media dir: {settings.MEDIA_ROOT})"
                            )
                    except DuplicateCourseError:
                        logger.error(
                            f"Course already exists for Organization: {row['Vendor']},"
                            f"Course Number: {row['CourseAcronym']}, Course Run: 2021"
                        )
                        rows_with_errors.append(line_count + 1)
                    line_count += 1
                    if line_count % 50 == 0:
                        logger.info(f'Processed {line_count} records')
        logger.info(f'Successfully processed all courses ({line_count} records)')
        if rows_with_errors:
            logger.info(
                f'Skipped courses on lines {rows_with_errors} due to insufficient data or duplicate records. '
                f'Logs above should contain error messages.'
            )
