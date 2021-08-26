import sys
import xml.etree.ElementTree as ET

from os import listdir, rename
from shutil import copy2

from edxval.api import get_videos_for_course, remove_video_for_course, create_external_video
from edxval.models import CourseVideo, Video
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '''
    Run this command before importing a localized course into edX.
    Use it to clean up old invalid course to video mappings in the MySQL database,
    to create new video ids for new videos, and to update XML files with the
    correct video ids, video URLs, and transcripts. Renames files in the /static
    directory to the correct name when you are creating new video ids.
    '''

    def add_arguments(self, parser):
        parser.add_argument('course_id', help='edx course id')
        parser.add_argument('course_dir', help='absolute path to the course export/import directory')
        parser.add_argument('language', help='two-letter abbreviation for the course language, one of [ja, fr, es]')
        parser.add_argument(
            '-x',
            '--delete',
            action='store_true',
            help='soft delete any existing course to video mappings for this course'
        )
        parser.add_argument(
            '-c',
            '--create_ids',
            action='store_true',
            help='create new video ids for the videos in this course'
        )
        parser.add_argument(
            '-r',
            '--replace_transcripts',
            action='store_true',
            help='replace English transcript filenames with new language (default is to add new language)'
        )
        parser.add_argument(
            '-k',
            '--keep_urls',
            action='store_true',
            help='retain existing video URLs (localized course uses English videos + audio as-is)'
        )

    def handle(self, *args, **options):
        course_id = options['course_id']
        course_dir = options['course_dir']
        language = options['language']
        do_delete = options.get('delete')
        do_create = options.get('create_ids')
        do_replace = options.get('replace_transcripts')
        do_keep_urls = options.get('keep_urls')

        if language not in ['ja', 'fr', 'es']:
            print('ERROR: Unrecognized course language ({0})'.format(language))
            sys.exit(1)

        if 'video' not in listdir(course_dir):
            print(
                "ERROR: The path {0} for the course import/export "
                "directory does not appear to be a valid course.".format(course_dir)
            )
            print("Please check that the path is readable by your user id, and that it contains a video subdirectory")
            sys.exit(1)

        video_dir = course_dir + "/video/"

        if do_delete:
            coursevideo = get_videos_for_course(course_id)
            for video in coursevideo:
                current_vid = video['edx_video_id']
                remove_video_for_course(course_id, current_vid)  # sets hidden flag in edxval_coursevideo table

        for file in listdir(video_dir):
            # Rename the existing XML file in /videos to a new file
            # name(.old) and then write the updated XML to the original path
            filepath = video_dir + file
            old_filepath = filepath + '.old'
            rename(filepath, old_filepath)

            root = ET.parse(old_filepath).getroot()

            if do_create:
                new_vid = create_external_video('External Video')
                video_object = Video.objects.get(edx_video_id=new_vid)
                CourseVideo.objects.get_or_create(video_id=video_object.id, course_id=course_id)

            current_vid = root.get('edx_video_id')

            transcript_file_format = root.find('video_asset/transcripts/transcript').get('file_format')
            current_transcript_filename = root.find('transcript').get('src')
            lang_transcript_filename = current_transcript_filename.replace(
                '-en.' + transcript_file_format,
                '-' + language + '.' + transcript_file_format
            )

            static_dir = course_dir + "/static/"
            # Copy the static/<current_vid>-en.srt file to static/<current_vid>-lang.srt
            try:
                copy2(static_dir + current_transcript_filename, static_dir + lang_transcript_filename)
            except IOError:
                print(
                    "WARNING: unable to copy {0} to {1}".format(current_transcript_filename, lang_transcript_filename)
                )

            if do_create:

                en_transcript_filename = current_transcript_filename.replace(current_vid, new_vid)
                # Rename -en file with new video id
                try:
                    rename(static_dir + current_transcript_filename, static_dir + en_transcript_filename)
                except OSError:
                    print("WARNING: unable to rename file {0}".format(current_transcript_filename))

                # Then rename the -lang file with the new video id
                temp_lang_transcript_filename = lang_transcript_filename
                lang_transcript_filename = lang_transcript_filename.replace(current_vid, new_vid)
                try:
                    rename(static_dir + temp_lang_transcript_filename, static_dir + lang_transcript_filename)
                except OSError:
                    print("WARNING: unable to rename file {0}".format(temp_lang_transcript_filename))

                # Set the new video id in the XML root
                root.set('edx_video_id', new_vid)

                if not do_keep_urls:
                    # Replace video URL twice (html5_sources, src)
                    # Before '/videos/ext/vod/cbt/GD101/join/11_join_03-05.smil/11_join_03-05.m3u8'
                    # After '/videos/ext/vod/cbt/fr/GD101/join/11_join_03-05.smil/11_join_03-05.m3u8'
                    value = root.get('html5_sources')
                    if "/" + language + "/" not in value:
                        root.set('html5_sources', value.replace('/videos/ext/vod/cbt/', '/videos/ext/vod/cbt/' + language + '/'))

                    element = root.find('source')
                    value = element.get('src')
                    if "/" + language + "/" not in value:
                        element.set('src', value.replace('/videos/ext/vod/cbt/', '/videos/ext/vod/cbt/' + language + '/'))

            if do_replace:
                # Replace transcripts language and filename {"en": "bd70863a-8fc5-4ad2-86ff-c7d992cd8237-en.srt"}
                value = root.get('transcripts')
                new_value = value.replace(
                    '"en"',
                    '"' + language + '"'
                ).replace(
                    current_transcript_filename,
                    lang_transcript_filename
                )
                root.set('transcripts', new_value)

                element = root.find('video_asset/transcripts/transcript')
                element.set('language_code', language)

                element = root.find('transcript')
                element.set('language', language)
                element.set('src', lang_transcript_filename)
            
            # Otherwise, add an additional transcript filename and language
            else:
                value = root.get('transcripts')

                if do_create:
                    # Update video id for English
                    value = value.replace(current_transcript_filename, en_transcript_filename)

                # Add new language to list of transcripts
                root.set('transcripts', value.replace('}', ', "' + language + '": "' + lang_transcript_filename + '"}'))

                # Add a new transcript element to /video/video_asset/transcripts 
                # <transcript file_format="srt" language_code="en" provider="Custom"/>
                element = root.find('video_asset/transcripts')
                new_element = ET.SubElement(element, 'transcript')
                new_element.set('language_code', language)
                new_element.set('file_format', transcript_file_format)
                new_element.set('provider', 'Custom')

                if do_create: 
                    # Update video id for English in transcript element
                    element = root.find('transcript')
                    element.set('src', en_transcript_filename)

                # Add a new transcript element to video root 
                # <transcript language="en" src="bd70863a-8fc5-4ad2-86ff-c7d992cd8237-en.srt"/>
                element = ET.SubElement(root, 'transcript')
                element.set('language', language)
                element.set('src', lang_transcript_filename)

            tree = ET.ElementTree(root)
            tree.write(filepath)
