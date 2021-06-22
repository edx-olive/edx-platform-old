"""
Tests for the edit_curriculum management command.
"""

import json

from django.conf import settings
from django.core.management.base import CommandError
from six import text_type
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from openedx.core.djangoapps.content.course_overviews.management.commands import edit_curriculum
from openedx.core.djangoapps.content.course_overviews.models import Curriculum
from openedx.core.djangoapps.content.course_overviews.tests.factories import (
    CourseOverviewFactory,
    CurriculumFactory,
    SeriesFactory
)

LOGGER_NAME = 'openedx.core.djangoapps.content.course_overviews.management.commands.edit_curriculum'


class TestEditCurriculum(ModuleStoreTestCase):
    """
    Tests for the edit_curriculum management command.
    """
    def setUp(self):
        super().setUp()
        with self.store.default_store(ModuleStoreEnum.Type.mongo):
            self.video_course = CourseFactory.create()
            self.chapter = ItemFactory.create(category="chapter", parent_location=self.video_course.location)
            self.sequential = ItemFactory.create(category="sequential", parent_location=self.chapter.location)
            self.vertical = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_1 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.video_2 = ItemFactory.create(category="video", parent_location=self.vertical.location)
            self.vertical_2 = ItemFactory.create(category="vertical", parent_location=self.sequential.location)
            self.video_3 = ItemFactory.create(category="video", parent_location=self.vertical_2.location)
        self.courses = CourseOverviewFactory.create_batch(3)
        self.series = SeriesFactory.create_batch(3)
        self.curriculum = CurriculumFactory.create(
            courses=[self.courses[0]], standalone_videos=json.dumps([text_type(self.video_1.location)]), series=[self.series[0]]
        )
        self.videos_ids = [text_type(v.location) for v in [self.video_1, self.video_2, self.video_3]]
        self.command = edit_curriculum.Command()
        settings.VIDEO_LIBRARY_COURSE = text_type(self.video_course.id)

    def _call_comand(self, curriculum_id=None, **kwargs):
        """
        Helper method to call the command.
        """
        curriculum_id = curriculum_id or self.curriculum.curriculum_id
        options = {
            'add_courses': kwargs.get('add_courses', []),
            'remove_courses': kwargs.get('remove_courses', []),
            'add_series': kwargs.get('add_series', []),
            'remove_series': kwargs.get('remove_series', []),
            'add_videos': kwargs.get('add_videos', []),
            'remove_videos': kwargs.get('remove_videos', []),
            'title': kwargs.get('title', ''),
            'description': kwargs.get('description', '')
        }
        self.command.handle(curriculumID=curriculum_id, **options)


    def test_invalid_curriculum_id(self):
        """
        Test command error when passing invalid target curriculum id.
        """
        errstring = "Curriculum not found. Provide a valid value for curriculumID."
        with self.assertRaisesRegex(CommandError, errstring):
            self.command.handle(curriculumID='fake_id')

    def test_add_courses(self):
        """
        Test add courses positive flow.
        """
        self._call_comand(add_courses=[text_type(c.id) for c in self.courses[1:]])
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
            3
        )

    def test_add_duplicated_course(self):
        """
        Test add duplicated course.
        """
        errstring = 'already added to this curriculum'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_courses=[text_type(self.courses[0].id)])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
                1
            )

    def test_add_invalid_course(self):
        """
        Test adding invalid course id has no effect.
        """
        errstring = 'seems to be invalid, skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_courses=['course-v1:fake+invalid+key'])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
                1
            )

    def test_add_courses_mixed(self):
        """
        Test add courses along with duplicate one.
        """
        errstring = 'already added to this curriculum'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_courses=[text_type(c.id) for c in self.courses])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
                3
            )

    def test_remove_course(self):
        """
        Test remove course positive flow.
        """
        self._call_comand(remove_courses=[text_type(self.courses[0].id)])
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
            0
        )

    def test_remove_external_course(self):
        """
        Test remove course than doesn't belong to this curriculum.
        """
        errstring = 'does not belong to this curriculum. Skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(remove_courses=[text_type(self.courses[1].id)])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
                1
            )

    def test_remove_invalid_course_id(self):
        """
        Test removing passing invalid course id.
        """
        errstring = 'does not belong to this curriculum. Skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(remove_courses=['course-v1:fake+course+id'])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).courses.count(),
                1
            )

    def test_add_series(self):
        """
        Test add series positive flow.
        """
        self._call_comand(add_series=[s.series_id for s in self.series[1:]])
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
            3
        )

    def test_add_duplicate_series(self):
        """
        Test add duplicate series.
        """
        errstring = 'already added to this curriculum'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_series=[self.series[0].series_id])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
                1
            )

    def test_add_invalid_series(self):
        """
        Test add non existing series.
        """
        errstring = 'seems to be invalid, skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_series=['fake_series_id'])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
                1
            )

    def test_add_series_mixed(self):
        """
        Test add valid series along with duplicate.
        """
        errstring = 'already added to this curriculum'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_series=[s.series_id for s in self.series])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
                3
            )

    def test_remove_series(self):
        """
        Test remove series positive flow.
        """
        self._call_comand(remove_series=[self.series[0].series_id])
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
            0
        )

    def test_remove_external_series(self):
        """
        Test remove series that not included in the curriculum.
        """
        errstring = 'does not belong to this curriculum or provided value is invalid'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(remove_series=[self.series[1].series_id])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
                1
            )

    def test_remove_invalid_series_id(self):
        """
        Test remove invalid series id.
        """
        self._call_comand(remove_series=['fake_series_id'])
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).series.count(),
            1
        )

    def add_videos(self):
        """
        Test add video positive flow.
        """
        self._call_comand(add_videos=self.videos_ids[1:])
        result_count = len(json.loads(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
        ))
        self.assertEqual(
            result_count,
            3
        )

    def add_duplicate_video(self):
        """
        Test add video that already included in the curriculum.
        """
        errstring = 'already added to the curriculum. Skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_videos=self.videos_ids[0])
            self.assertIn(errstring, cm.output[0])
            result_count = len(json.loads(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
            ))
            self.assertEqual(
                result_count,
                1
            )

    def test_add_video_no_video_library(self):
        """
        Test imposible to add video if there is no video library.
        """
        settings.VIDEO_LIBRARY_COURSE = ''
        errstring = 'Can\'t process videos. Video library is empty'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_videos=self.videos_ids)
            self.assertIn(errstring, cm.output[0])
            result_count = len(json.loads(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
            ))
            self.assertEqual(
                result_count,
                1
            )

    def test_video_not_in_library(self):
        """
        Test add video from outside the library.
        """
        external_video_id = 'block-v1:fake+course+id+type@video+block@fakeaa5796f3445391ff0d7326b2ab7d'
        errstring = 'does not exist in the library. Skipping...'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(add_videos=[external_video_id])
            self.assertIn(errstring, cm.output[0])
            result_count = len(json.loads(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
            ))
            self.assertEqual(
                result_count,
                1
            )

    def test_remove_video(self):
        """
        Test video removing positive flow.
        """
        self._call_comand(remove_videos=[self.videos_ids[0]])
        result_count = len(json.loads(
            Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
        ))
        self.assertEqual(
            result_count,
            0
        )

    def test_remove_external_or_invalid_video(self):
        """
        Test remove video that was not included to curriculum or invalid one.
        """
        errstring = 'Check that video id is correct'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(remove_videos=[self.videos_ids[2]])
            self.assertIn(errstring, cm.output[0])
            result_count = len(json.loads(
                Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id).standalone_videos
            ))
            self.assertEqual(
                result_count,
                1
            )

    def test_remove_last_course(self):
        """
        Test can't remove last course if there is no videos and series.
        """
        curriculum_with_lonely_course = CurriculumFactory.create(
            courses=[self.courses[0].id]
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_course.curriculum_id).standalone_videos,
            ''
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_course.curriculum_id).series.count(),
            0
        )
        errstring = 'Curriculum should include at least one series, course or standalone video.'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(
                curriculum_id=curriculum_with_lonely_course.curriculum_id,
                remove_courses=[text_type(self.courses[0])]
            )
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=curriculum_with_lonely_course.curriculum_id).courses.count(),
                1
            )

    def test_remove_last_series(self):
        """
        Test can't remove last series if there is no courses and videos.
        """
        curriculum_with_lonely_series = CurriculumFactory.create(
            series=[self.series[0]]
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_series.curriculum_id).courses.count(),
            0
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_series.curriculum_id).standalone_videos,
            ''
        )
        errstring = 'Curriculum should include at least one series, course or standalone video.'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(
                curriculum_id=curriculum_with_lonely_series.curriculum_id, remove_series=[self.series[0].series_id]
            )
            self.assertIn(errstring, cm.output[0])
            self.assertIn(errstring, cm.output[0])
            self.assertEqual(
                Curriculum.objects.get(curriculum_id=curriculum_with_lonely_series.curriculum_id).series.count(),
                1
            )

    def test_remove_last_video(self):
        """
        Test can't remove last video if there is no courses and series.
        """
        curriculum_with_lonely_video = CurriculumFactory.create(
            standalone_videos=json.dumps([self.videos_ids[0]])
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_video.curriculum_id).courses.count(),
            0
        )
        self.assertEqual(
            Curriculum.objects.get(curriculum_id=curriculum_with_lonely_video.curriculum_id).series.count(),
            0
        )
        errstring = 'Curriculum should include at least one series, course or standalone video.'
        with self.assertLogs(logger=LOGGER_NAME, level='INFO') as cm:
            self._call_comand(
                curriculum_id=curriculum_with_lonely_video.curriculum_id, remove_videos=[self.videos_ids[2]]
            )
            self.assertIn(errstring, cm.output[0])
            result_count = len(json.loads(
                Curriculum.objects.get(curriculum_id=curriculum_with_lonely_video.curriculum_id).standalone_videos
            ))
            self.assertEqual(
                result_count,
                1
            )

    def test_complex_call(self):
        """
        Add all courses, videos and series, change title and description.
        Then remove first video, series and course.
        """
        kwargs = {
            'add_courses': [text_type(c.id) for c in self.courses],
            'remove_courses': [text_type(self.courses[0].id)],
            'add_series': [s.series_id for s in self.series],
            'remove_series': [self.series[0].series_id],
            'add_videos': self.videos_ids,
            'remove_videos': [self.videos_ids[0]],
            'title': 'Brand new title',
            'description': 'your advertising could be here'
        }
        self._call_comand(**kwargs)
        res = Curriculum.objects.get(curriculum_id=self.curriculum.curriculum_id)
        self.assertEqual(res.title, kwargs['title'])
        self.assertEqual(res.description, kwargs['description'])
        self.assertEqual(res.courses.count(), 2)
        self.assertEqual(res.series.count(), 2)
        self.assertEqual(json.loads(res.standalone_videos), self.videos_ids[1:])
