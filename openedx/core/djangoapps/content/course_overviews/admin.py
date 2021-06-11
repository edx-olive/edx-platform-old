"""
Django admin page for CourseOverviews, the basic metadata about a course that
is used in user dashboard queries and other places where you need info like
name, and start dates, but don't actually need to crawl into course content.
"""

from django import forms
from django.forms.widgets import SelectMultiple as SelectMultipleOriginal
from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin
from django.core.exceptions import ValidationError

from lms.djangoapps.courseware.utils import get_video_library_blocks_no_request
from .models import (
    CourseOverview,
    CourseOverviewImageConfig,
    CourseOverviewImageSet,
    SimulateCoursePublishConfig,
    NewAndInterestingTag,
    Series,
    Curriculum,
)


class CourseOverviewAdmin(admin.ModelAdmin):
    """
    Simple, read-only list/search view of Course Overviews.
    """
    list_display = [
        'id',
        'display_name',
        'version',
        'enrollment_start',
        'enrollment_end',
        'created',
        'modified',
    ]

    search_fields = ['id', 'display_name']


class CourseOverviewImageConfigAdmin(ConfigurationModelAdmin):
    """
    Basic configuration for CourseOverview Image thumbnails.

    By default this is disabled. If you change the dimensions of the images with
    a new config after thumbnails have already been generated, you need to clear
    the entries in CourseOverviewImageSet manually for new entries to be
    created.
    """
    list_display = [
        'change_date',
        'changed_by',
        'enabled',
        'large_width',
        'large_height',
        'small_width',
        'small_height'
    ]

    def get_list_display(self, request):
        """
        Restore default list_display behavior.

        ConfigurationModelAdmin overrides this, but in a way that doesn't
        respect the ordering. This lets us customize it the usual Django admin
        way.
        """
        return self.list_display


class CourseOverviewImageSetAdmin(admin.ModelAdmin):
    """
    Thumbnail images associated with CourseOverviews. This should be used for
    debugging purposes only -- e.g. don't edit these values.
    """
    list_display = [
        'course_overview',
        'small_url',
        'large_url',
    ]
    search_fields = ['course_overview__id']
    readonly_fields = ['course_overview_id']
    fields = ('course_overview_id', 'small_url', 'large_url')


class SimulateCoursePublishConfigAdmin(ConfigurationModelAdmin):
    pass


class NewAndInterestingTagAdmin(admin.ModelAdmin):
    """
    NewAndInterestingTag admin representation.

    list_display was modified to represent custom date format.
    """
    def formated_date(self, obj):
        return obj.expiration_date.strftime('%m/%d/%Y')

    formated_date.admin_order_field = 'expiration_date'
    formated_date.short_description = 'Expiration date (mm/dd/YYYY)'

    list_display = ('course', 'formated_date',)


class BaseCourseCollectionAdmin(admin.ModelAdmin):
    """
    Base class for the CourseCollection descendants.
    """
    readonly_fields = [
        'created_by',
        'creation_date',
        'last_modified',
    ]


class SeriesAdmin(BaseCourseCollectionAdmin):
    """
    Series model admin.
    """
    list_display = [
        'series_id',
        'title',
        'creation_date',
        'last_modified',
        'created_by'
    ]

    def save_model(self, request, obj, form, change):
        """
        Set created_by if it was not set.
        """
        if getattr(obj, 'created_by', None) is None:
            obj.created_by = request.user
        obj.save()


class SelectMultiple(SelectMultipleOriginal):
    """
    Custom SelectMultiple widget.

    Overrides `optgroups` to fix visibility for previosly selected values.
    """
    def optgroups(self, name, value, attrs):
        val = value[0] if len(value) else value
        return super().optgroups(name, val, attrs=attrs)


class CurriculumAdminForm(forms.ModelForm):
    """
    ModelForm for Currucula that provides custom `standalone_videos` field.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        video_library_choises = [
            (v['id'], v['name'] + ': ' + v['id']) for v in get_video_library_blocks_no_request()
        ]
        self.fields['standalone_videos'] = forms.MultipleChoiceField(
            choices=video_library_choises, required=False, widget=SelectMultiple
        )

    def clean_curriculum_id(self):
        """
        Validate curriculum_id is one word.
        """
        curriculum_id = self.cleaned_data.get('curriculum_id')
        if ' ' in curriculum_id:
            raise forms.ValidationError("Spaces are not allowed.")
        return curriculum_id

    def clean(self):
        """
        Validate at least one element is selected.
        """
        if not (
            self.cleaned_data.get('series') or
            self.cleaned_data.get('courses') or
            self.cleaned_data.get('standalone_videos')
        ):
            raise ValidationError("Curriculum should include at least one series, course or standalone video.")
        return super().clean()

    class Meta:
        model = Curriculum
        fields = '__all__'


class CurriculumAdmin(BaseCourseCollectionAdmin):
    """
    Curriculum model admin.
    """

    form = CurriculumAdminForm

    fields = (
        'title',
        'collection_type',
        'description',
        'image',
        'courses',
        'series',
        'standalone_videos',
        'curriculum_id',
        'created_by',
        'creation_date',
        'last_modified'
    )

    def save_model(self, request, obj, form, change):
        """
        Set created_by if it was not set.
        """
        if getattr(obj, 'created_by', None) is None:
            obj.created_by = request.user
        obj.save()


admin.site.register(CourseOverview, CourseOverviewAdmin)
admin.site.register(CourseOverviewImageConfig, CourseOverviewImageConfigAdmin)
admin.site.register(CourseOverviewImageSet, CourseOverviewImageSetAdmin)
admin.site.register(SimulateCoursePublishConfig, SimulateCoursePublishConfigAdmin)
admin.site.register(NewAndInterestingTag, NewAndInterestingTagAdmin)
admin.site.register(Series, SeriesAdmin)
admin.site.register(Curriculum, CurriculumAdmin)
