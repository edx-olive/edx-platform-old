"""Admin site bindings for the `polls_survey` app."""

from django.contrib import admin

from poll_survey.models import (
    OpenEndedSurveyQuestion,
    OpenEndedSurveyQuestionTemplateLink,
    OpenEndedSurveySubmission,
    OpenEndedSurveyTemplate,
    PollAnswerOption,
    PollQuestion,
    PollQuestionAnswerLink,
    PollSubmission,
    PollTemplate,
    SurveyAnswerOption,
    SurveyPollCommonsection,
    SurveyQuestion,
    SurveyQuestionAnswerLink,
    SurveySubmission,
    SurveyTemplate,
    SurveyQuestionTemplateLink
)


class PollAnswerOptionAdmin(admin.ModelAdmin):
    """Admin interface for the `PollAnswerOption` model."""

    model = PollAnswerOption
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'text', 'created', 'modified')
    list_display_links = ('id', 'text', 'created', 'modified')
    search_fields = ['text']


class SurveyAnswerOptionAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveyAnswerOption` model."""

    model = SurveyAnswerOption
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'text', 'created', 'modified')
    list_display_links = ('id', 'text', 'created', 'modified')
    search_fields = ['text']


class PollQuestionAnswerLinkInline(admin.TabularInline):
    """Admin inline structure for the `PollQuestionAnswerLink` model."""
    model = PollQuestionAnswerLink
    min_num = 1  # Enforce indication of at least one answer (otherwise, poll xblock will break)
    extra = 1


class SurveyQuestionAnswerLinkInline(admin.TabularInline):
    """Admin inline structure for the `SurveyQuestionAnswerLink` model."""
    model = SurveyQuestionAnswerLink
    min_num = 1  # Enforce indication of at least one answer (otherwise, survey xblock will break)
    extra = 1


class PollQuestionAdmin(admin.ModelAdmin):
    """Admin interface for the `PollQuestion` model."""

    model = PollQuestion
    # Can't use `filter_horizontal` because of intermediary table,
    # ref.: https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#working-with-many-to-many-intermediary-models
    # filter_horizontal = ('answers', )
    inlines = (PollQuestionAnswerLinkInline,)
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_display_links = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_filter = ('is_default',)
    search_fields = ['text']

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(PollQuestionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            # Course id comes from xblocks only
            django_readonly = django_readonly + ('course',)
        if obj and obj.course:
            return django_readonly + ('is_default', 'text')
        return django_readonly


class SurveyQuestionAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveyQuestion` model."""

    model = SurveyQuestion
    # Can't use `filter_horizontal` because of intermediary table,
    # ref.: https://docs.djangoproject.com/en/1.8/ref/contrib/admin/#working-with-many-to-many-intermediary-models
    # filter_horizontal = ('answers', )
    inlines = (SurveyQuestionAnswerLinkInline,)
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_display_links = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_filter = ('is_default',)
    search_fields = ['text', 'image_url', 'image_alt_text']

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(SurveyQuestionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            # Course id comes from xblocks only
            django_readonly = django_readonly + ('course',)
        if obj and obj.course:
            return django_readonly + ('is_default', 'text', 'image_url', 'image_alt_text')
        return django_readonly


class OpenEndedSurveyQuestionAdmin(admin.ModelAdmin):
    """Admin interface for the `OpenEndedSurveyQuestion` model."""

    model = OpenEndedSurveyQuestion
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_display_links = ('id', 'text', 'is_default', 'course', 'created', 'modified')
    list_filter = ('is_default',)
    search_fields = ['text', 'image_url', 'image_alt_text']

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(OpenEndedSurveyQuestionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            # Course id comes from xblocks only
            django_readonly = django_readonly + ('course',)
        if obj and obj.course:
            return django_readonly + ('is_default', 'text', 'image_url', 'image_alt_text')
        return django_readonly


class PollTemplateAdmin(admin.ModelAdmin):
    """Admin interface for the `PollTemplate` model."""

    model = PollTemplate
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'question', 'is_enabled', 'created', 'modified')
    list_display_links = ('id', 'question', 'created', 'modified')


class SurveyQuestionTemplateLinkInline(admin.TabularInline):
    """Admin inline structure for the `SurveyQuestionTemplateLink` model."""

    model = SurveyQuestionTemplateLink
    min_num = 1  # Enforce indication of at least one question (otherwise, a survey xblock will break)
    extra = 1


class SurveyTemplateAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveyTemplate` model."""

    model = SurveyTemplate
    inlines = (SurveyQuestionTemplateLinkInline,)
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'is_enabled', 'created', 'modified')
    list_display_links = ('id', 'is_enabled', 'created', 'modified')


class OpenEndedSurveyQuestionTemplateLinkInline(admin.TabularInline):
    """Admin inline structure for the `OpenEndedSurveyQuestionTemplateLink` model."""

    model = OpenEndedSurveyQuestionTemplateLink
    min_num = 1  # Enforce indication of at least one question (otherwise, an open-ended survey xblock will break)
    extra = 1


class OpenEndedSurveyTemplateAdmin(admin.ModelAdmin):
    """Admin interface for the `OpenEndedSurveyTemplate` model."""

    model = OpenEndedSurveyTemplate
    inlines = (OpenEndedSurveyQuestionTemplateLinkInline,)
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'is_enabled', 'created', 'modified')
    list_display_links = ('id', 'is_enabled', 'created', 'modified')


class PollSubmissionAdmin(admin.ModelAdmin):
    """Admin interface for the `PollSubmission` model."""

    model = PollSubmission
    readonly_fields = ('created', 'modified', 'submission_date')
    list_display = ('student', 'course', 'question', 'answer', 'created', 'modified')
    list_display_links = ('student', 'course', 'question', 'answer', 'created', 'modified')

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(PollSubmissionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return django_readonly + ('student', 'course', 'question', 'answer')
        return django_readonly


class SurveySubmissionAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveySubmission` model."""

    model = SurveySubmission
    readonly_fields = ('created', 'modified', 'submission_date')
    list_display = ('student', 'course', 'question', 'answer', 'created', 'modified')
    list_display_links = ('student', 'course', 'question', 'answer', 'created', 'modified')

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(SurveySubmissionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return django_readonly + ('student', 'course', 'question', 'answer')
        return django_readonly


class OpenEndedSurveySubmissionAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveySubmission` model."""

    model = OpenEndedSurveySubmission
    readonly_fields = ('created', 'modified', 'submission_date')
    list_display = ('student', 'course', 'question', 'created', 'modified')
    list_display_links = ('student', 'course', 'question', 'created', 'modified')

    def get_readonly_fields(self, request, obj=None):
        django_readonly = super(OpenEndedSurveySubmissionAdmin, self).get_readonly_fields(request, obj)
        if obj:
            return django_readonly + ('student', 'course', 'question', 'answer_text')
        return django_readonly


class SurveyPollCommonsectionAdmin(admin.ModelAdmin):
    """Admin interface for the `SurveyPollCommonsection` model."""

    model = SurveyPollCommonsection
    readonly_fields = ('created', 'modified')
    list_display = ('id', 'contains_poll', 'contains_survey', 'contains_open_ended_survey', 'created', 'modified')
    list_display_links = ('id', 'contains_poll', 'contains_survey', 'contains_open_ended_survey', 'created', 'modified')


admin.site.register(PollAnswerOption, PollAnswerOptionAdmin)
admin.site.register(SurveyAnswerOption, SurveyAnswerOptionAdmin)
admin.site.register(PollQuestion, PollQuestionAdmin)
admin.site.register(SurveyQuestion, SurveyQuestionAdmin)
admin.site.register(OpenEndedSurveyQuestion, OpenEndedSurveyQuestionAdmin)
admin.site.register(PollTemplate, PollTemplateAdmin)
admin.site.register(SurveyTemplate, SurveyTemplateAdmin)
admin.site.register(OpenEndedSurveyTemplate, OpenEndedSurveyTemplateAdmin)
admin.site.register(PollSubmission, PollSubmissionAdmin)
admin.site.register(SurveySubmission, SurveySubmissionAdmin)
admin.site.register(OpenEndedSurveySubmission, OpenEndedSurveySubmissionAdmin)
admin.site.register(SurveyPollCommonsection, SurveyPollCommonsectionAdmin)
