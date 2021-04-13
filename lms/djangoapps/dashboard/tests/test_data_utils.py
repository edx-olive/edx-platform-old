from datetime import datetime

from django.test import TestCase
import pytz

from courseware.tests.factories import StudentModuleFactory
from courseware.models import StudentModule
from dashboard.background_download.data_utils import _get_closest_to_dt


class TestGetClosest(TestCase):

    def test_get_closest_to_dt(self):
        """
        Test for _get_closest_to_dt utils function.
        """
        sm1 = StudentModuleFactory()
        dt = datetime.now(pytz.utc)
        sm2 = StudentModuleFactory()

        qs = StudentModule.objects.all()
        res = _get_closest_to_dt(qs, dt)

        closest = sm1 if (abs(sm1.created - dt) < abs(sm2.created - dt)) else sm2
        self.assertEqual(res, closest)
