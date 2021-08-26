import glob
import os.path
import sys
import io
import edxval.api
import edxval.transcript_utils

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '''
    Copies all transcripts from /edx/var/edxapp/media/video-transcripts
    to a course export directory. Overwrites all active transcripts for
    the specified language for this course. Run this command after you
    have exported from edx.
    '''

    def add_arguments(self, parser):
        parser.add_argument('course_dir', help='absolute path to the course export directory')
        parser.add_argument('language', help='two-letter abbreviation for the course language, one of [en, ja, fr, es]')

    def handle(self, *args, **options):
        course_dir = options['course_dir']
        language = options['language']

        if language not in ['en', 'ja', 'fr', 'es']:
            print('ERROR: Unrecognized course language ({0})'.format(language))
            sys.exit(1)

        static_transcripts = glob.glob('{0}/static/*-{1}.srt'.format(course_dir, language))

        if len(static_transcripts) <= 0:
            print('ERROR: Did not find any transcripts in {0}/static for language {1}'.format(course_dir, language))
            print(
                'Confirm that the directory exists, is readable, and '
                'that it contains at least one transcript for the specified language.'
            )
            sys.exit(1)

        for static_transcript_filepath in static_transcripts:
            video_filename = os.path.basename(static_transcript_filepath)
            video_id = video_filename[0:video_filename.find('-{0}.srt'.format(language))]

            transcript_dict = edxval.api.get_video_transcript(video_id, language)
            if transcript_dict is not None:
                video_transcript_filename = '/edx/var/edxapp{0}'.format(transcript_dict['url'])
                video_transcript_format = transcript_dict['file_format']

                with io.open(video_transcript_filename, 'r', encoding='utf8') as video_transcript_file:
                    transcript_contents = video_transcript_file.read()
                video_transcript_file.close()

                # Convert from sjson (may be used for video-transcripts) to srt
                # (format used for transcripts in static course directory) if required
                if video_transcript_format == 'sjson':
                    transcript_obj = edxval.transcript_utils.Transcript()
                    transcript_contents = transcript_obj.convert(transcript_contents, 'sjson', 'srt')

                with io.open (static_transcript_filepath, 'w', encoding='utf8') as video_transcript_file:
                    video_transcript_file.write(transcript_contents)
                video_transcript_file.close()
            else:
                print(
                    'WARNING: Unable to retrieve transcript URL from '
                    'contentstore for video_id {0} in language {1}'.format(video_id, language)
                )
                print('No transcript was copied for this video.')
