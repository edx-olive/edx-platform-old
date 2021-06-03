"""
Search the videos available in the video library course.
"""
from django.conf import settings
from django.core.management import CommandError
from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from six import text_type
from xmodule.modulestore.exceptions import ItemNotFoundError

from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.content.block_structure.exceptions import BlockStructureNotFound


class Command(BaseCommand):
    """
    Search for videos in the video library.

    By default, retrieve all the videos from library.
    To check existance of a particular video, specify the --find-one=<video_locator> argument.

    Example usage:
        `./manage.py lms search_video_library --settings=devstack_docker`
        `./manage.py lms search_video_library --find-one=block-v1:00+00+00+type@video+block@1974e9f1ff584bf9a7f1d3a272570a8d --settings=devstack_docker`

    Raises:
        CommandError: if there is no VIDEO_LIBRARY_COURSE in the settings or its value is invalid.
    """
    help = 'Search for videos in the video library course.'

    def add_arguments(self, parser):
        parser.add_argument('--find-one',
                            action='store',
                            dest='find_one',
                            type=str,
                            default='',
                            help='Video locator string. If defined, search for this video only.')

    def handle(self, *args, **options):
        find_one = options.get('find_one')

        video_library_id = getattr(settings, 'VIDEO_LIBRARY_COURSE', None)
        if not video_library_id:
            raise CommandError('There is no VIDEO_LIBRARY_COURSE value in the settings.')

        try:
            library_key = CourseKey.from_string(video_library_id)
            block_structure = get_course_in_cache(library_key)
        except (InvalidKeyError, BlockStructureNotFound, ItemNotFoundError):
            raise CommandError('Library course was not found. Please, check the VIDEO_LIBRARY_COURSE setting.')

        block_keys_to_remove = []
        for block_key in block_structure:
            block_type = block_structure.get_xblock_field(block_key, 'category')
            if block_type != 'video':
                block_keys_to_remove.append(block_key)
        for block_key in block_keys_to_remove:
            block_structure.remove_block(block_key, keep_descendants=True)

        if not len(block_structure):
            self.stdout.write(self.style.WARNING('There are no videos in the library yet.'))

        if find_one:
            for block_key in block_structure:
                locator = text_type(block_key)
                if locator == find_one:
                    self.stdout.write(self.style.SUCCESS(
                        'Found video [{}]: {}'.format(
                            locator, block_structure.get_xblock_field(block_key, 'display_name')
                        )
                    ))
                    return
            self.stdout.write(
                self.style.ERROR('Video with locator [{}] was not found in the library.'.format(find_one))
            )
            return

        for block in block_structure:
            name = block_structure.get_xblock_field(block, 'display_name')
            self.stdout.write(
                self.style.SUCCESS('[{}]: {}'.format(text_type(block), name))
            )
