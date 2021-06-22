

from datetime import timedelta
import json

from django.utils import timezone
import factory
from factory.fuzzy import FuzzyChoice
from factory.django import DjangoModelFactory
from opaque_keys.edx.locator import CourseLocator

from ..models import CourseOverview, Curriculum, Series


def add_m2m_data(m2m_relation, data):
    """
    Helper function to enable factories to easily associate many-to-many data with created objects.
    """
    if data:
        m2m_relation.add(*data)


class CourseOverviewFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseOverview
        django_get_or_create = ('id', )
        exclude = ('run', )

    version = CourseOverview.VERSION
    pre_requisite_courses = []
    org = 'edX'
    run = factory.Sequence('2012_Fall_{}'.format)

    @factory.lazy_attribute
    def _pre_requisite_courses_json(self):
        return json.dumps(self.pre_requisite_courses)

    @factory.lazy_attribute
    def _location(self):
        return self.id.make_usage_key('course', 'course')

    @factory.lazy_attribute
    def id(self):
        return CourseLocator(self.org, 'toy', self.run)

    @factory.lazy_attribute
    def display_name(self):
        return "{} Course".format(self.id)

    @factory.lazy_attribute
    def start(self):
        return timezone.now()

    @factory.lazy_attribute
    def end(self):
        return timezone.now() + timedelta(30)

class SeriesFactory(DjangoModelFactory):
    class Meta:
        model = Series

    series_id = factory.Sequence('series_{}'.format)

class CurriculumFactory(DjangoModelFactory):
    class Meta:
        model = Curriculum

    curriculum_id = factory.Sequence('curriculum_{}'.format)
    collection_type = FuzzyChoice((c[0] for c in Curriculum.type_choices))

    @factory.post_generation
    def series(self, create, extracted, **kwargs):
        if create:
            add_m2m_data(self.series, extracted)

    @factory.post_generation
    def courses(self, create, extracted, **kwargs):
        if create:
            add_m2m_data(self.courses, extracted)
