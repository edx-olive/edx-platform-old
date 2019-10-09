"""Poll/Survey models."""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Max
from django.dispatch import receiver
from django.db.models.signals import post_save

from model_utils.fields import AutoCreatedField
from model_utils.models import TimeStampedModel
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class AnswerOptionBase(TimeStampedModel):
    """Base answer model."""

    text = models.CharField(max_length=255)

    class Meta:
        abstract = True


class PollAnswerOption(AnswerOptionBase):
    """Poll answer model."""

    image_url = models.CharField(max_length=255, blank=True, null=True)
    image_alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):  # NOQA
        return "PollAnswer #{!s}".format(self.id)

    def clean(self):
        super(PollAnswerOption, self).clean()
        if self.image_url and not self.image_alt_text:
            raise ValidationError({'image_alt_text': 'Please indicate the image alt text.'})
        elif not self.image_url and self.image_alt_text:
            raise ValidationError({'image_url': 'Please indicate the image path.'})


class SurveyAnswerOption(AnswerOptionBase):
    """Survey answer model."""

    def __unicode__(self):  # NOQA
        return "SurveyAnswer #{!s}".format(self.id)


class QuestionBase(TimeStampedModel):
    """
    Base question model.

    Question can be open-ended (no answer options
    will be associated with it then).
    """

    is_default = models.BooleanField(default=True)
    course = CourseKeyField(max_length=255, blank=True, null=True,
                            help_text="Course location id e.g. 'course-v1:RF+CS101+2019_T1'")
    text = models.CharField(max_length=512)

    class Meta:
        abstract = True


class SurveyQuestion(QuestionBase):
    """Survey question model."""

    answers = models.ManyToManyField(SurveyAnswerOption, through="SurveyQuestionAnswerLink")
    image_url = models.CharField(max_length=255, blank=True, null=True)
    image_alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):  # NOQA
        return "SurveyQuestion #{!s}".format(self.id)

    def clean(self):
        super(SurveyQuestion, self).clean()
        if self.course and self.is_default:
            raise ValidationError({'is_default': 'Please indicate either "course" or "is_default".'})
        if self.image_url and not self.image_alt_text:
            raise ValidationError({'image_alt_text': 'Please indicate the image path.'})
        elif not self.image_url and self.image_alt_text:
            raise ValidationError({'image_url': 'Please indicate the image alt text.'})


class PollQuestion(QuestionBase):
    """Poll question model."""

    answers = models.ManyToManyField(PollAnswerOption, through="PollQuestionAnswerLink")

    def __unicode__(self):  # NOQA
        return "PollQuestion #{!s}".format(self.id)

    def clean(self):
        super(PollQuestion, self).clean()
        if self.course and self.is_default:
            raise ValidationError({'is_default': 'Please indicate either "course" or "is_default".'})


class OpenEndedSurveyQuestion(QuestionBase):
    """Open Ended Survey question model."""

    image_url = models.CharField(max_length=255, blank=True, null=True)
    image_alt_text = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):  # NOQA
        return "OpenEndedSurveyQuestion #{!s}".format(self.id)

    def clean(self):
        super(OpenEndedSurveyQuestion, self).clean()
        if self.course and self.is_default:
            raise ValidationError({'is_default': 'Please indicate either "course" or "is_default".'})
        if self.image_url and not self.image_alt_text:
            raise ValidationError({'image_alt_text': 'Please indicate the image path.'})
        elif not self.image_url and self.image_alt_text:
            raise ValidationError({'image_url': 'Please indicate the image alt text.'})


class BaseQuestionAnswerLink(TimeStampedModel):
    """
    Intermediary model to keep question-answer relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    MIN_ORDER = 1
    # Django field to be defined in derived models
    question = None

    order = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ("order",)

    def __unicode__(self):  # NOQA
        return "Question-Answer Link #{!s}".format(self.id)

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new order."""
        if not self.question:
            raise ValueError("Define the question field of the question-answer model.")
        n = self._get_answer_links(self.question).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    def _get_answer_links(self, question):
        """Get ordered entries for a given template. """
        return self.__class__.objects.filter(question=question).order_by("order")

    @staticmethod
    def clean_orders(klass, question):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            klass (`BaseQuestionAnswerLink` subclass)
            question (question obj)
        """
        # Get ordered answers for a given question (e.g. `SurveyQuestionAnswerLink` objects)
        entries = klass.objects.filter(question=question).order_by("order")
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=klass.MIN_ORDER):
            if entry.order and i != int(entry.order):
                klass.objects.filter(id=entry.id).update(order=i)


class SurveyQuestionAnswerLink(BaseQuestionAnswerLink):
    """
    Intermediary model to keep question-answer relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(SurveyQuestionAnswerLink, self).save(force_insert, force_update, using, update_fields)


class PollQuestionAnswerLink(BaseQuestionAnswerLink):
    """
    Intermediary model to keep question-answer relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.PollDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    question = models.ForeignKey(PollQuestion)
    answer = models.ForeignKey(PollAnswerOption)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(PollQuestionAnswerLink, self).save(force_insert, force_update, using, update_fields)


class SubmissionBase(TimeStampedModel):
    """
    Base submission model.

    For historical data, (first) submission date
    might differ from creation date.
    """

    student = models.ForeignKey(User)
    course = CourseKeyField(max_length=255)
    submission_date = AutoCreatedField(help_text="First submission date. Might differ from entry creation date.")

    class Meta:
        abstract = True
        # Submission entry gets updated with new answer upon resubmission
        unique_together = ("student", "course", "question")


class PollSubmission(SubmissionBase):
    """Poll submission model."""

    question = models.ForeignKey(PollQuestion)
    answer = models.ForeignKey(PollAnswerOption)

    def __unicode__(self):  # NOQA
        return "PollSubmission #{!s}".format(self.id)


class SurveySubmission(SubmissionBase):
    """Survey submission model."""

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)

    def __unicode__(self):  # NOQA
        return "SurveySubmission #{!s}".format(self.id)


class OpenEndedSurveySubmission(SubmissionBase):
    """Open Ended Survey submission model."""

    question = models.ForeignKey(OpenEndedSurveyQuestion)
    answer_text = models.CharField(max_length=200)

    def __unicode__(self):  # NOQA
        return "OpenEndedSurveySubmission #{!s}".format(self.id)


class PreCourseSurveySubmission(SubmissionBase):
    """Pre-Course Survey submission model."""

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)

    def __unicode__(self):  # NOQA
        return "PreCourseSurveySubmission #{!s}".format(self.id)


class PostCourseSurveySubmission(SubmissionBase):
    """Post-Course Survey submission model."""

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)

    def __unicode__(self):  # NOQA
        return "PostCourseSurveySubmission #{!s}".format(self.id)


class CourseQualitySurveySubmission(SubmissionBase):
    """Course Quality Survey submission model."""

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)

    def __unicode__(self):  # NOQA
        return "CourseQualitySurveySubmission #{!s}".format(self.id)


class BaseTemplate(TimeStampedModel):
    """Base template model."""

    is_enabled = models.BooleanField(
        default=False,
        help_text="Warning: any changes in default templates will take effect only after the edX platform "
                  "CMS and LMS stack gets restarted. Please contact the application team "
                  "for them to follow a deployment procedure."
    )

    class Meta:
        abstract = True


class PollTemplate(BaseTemplate):
    """
    Poll template model.

    Define a poll component default structure.

    A poll contains a single question.
    """

    question = models.OneToOneField(PollQuestion)

    def __unicode__(self):  # NOQA
        return "PollTemplate #{!s}".format(self.id)

    def clean(self):
        super(PollTemplate, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default question can be stored in a poll template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValueError("Only default question can be stored in a poll template.")
        super(PollTemplate, self).save(force_insert, force_update, using, update_fields)


class SurveyTemplate(BaseTemplate):
    """
    Survey template model.

    Define a survey component default structure.

    A survey can contain multiple questions.
    """

    questions = models.ManyToManyField(SurveyQuestion, through="SurveyQuestionTemplateLink")

    def __unicode__(self):  # NOQA
        return "SurveyTemplate #{!s}".format(self.id)


class OpenEndedSurveyTemplate(BaseTemplate):
    """
    Open Ended Survey template model.

    Define an open-ended survey component default structure.

    An open-ended survey can contain multiple questions.
    """

    questions = models.ManyToManyField(OpenEndedSurveyQuestion, through="OpenEndedSurveyQuestionTemplateLink")

    def __unicode__(self):  # NOQA
        return "OpenEndedSurveyTemplate #{!s}".format(self.id)


class PreCourseSurveyTemplate(BaseTemplate):
    """
    Pre-course survey template model.

    Define a survey component default structure.

    A survey can contain multiple questions.
    """

    questions = models.ManyToManyField(SurveyQuestion, through="PreCourseSurveyQuestionTemplateLink")

    def __unicode__(self):  # NOQA
        return "PreCourseSurveyTemplate #{!s}".format(self.id)


class PostCourseSurveyTemplate(BaseTemplate):
    """
    Post-course survey template model.

    Define a survey component default structure.

    A survey can contain multiple questions.
    """

    questions = models.ManyToManyField(SurveyQuestion, through="PostCourseSurveyQuestionTemplateLink")

    def __unicode__(self):  # NOQA
        return "PostCourseSurveyTemplate #{!s}".format(self.id)


class CourseQualitySurveyTemplate(BaseTemplate):
    """
    Course quality survey template model.

    Define a survey component default structure.

    A survey can contain multiple questions.
    """

    questions = models.ManyToManyField(SurveyQuestion, through="CourseQualitySurveyQuestionTemplateLink")

    def __unicode__(self):  # NOQA
        return "CourseQualitySurveyTemplate #{!s}".format(self.id)


class BaseQuestionTemplateLink(TimeStampedModel):
    """
    Abstract intermediary model to keep question-template relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    MIN_ORDER = 1
    # Django fields to be defined in subclasses.
    template = None

    order = models.IntegerField(null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ("order",)

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new order."""
        if not self.template:
            raise ValueError("Define the template field in the question-template link model.")
        n = self._get_question_links(self.template).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    def _get_question_links(self, template):
        """Get ordered entries for a given template. """
        return self.__class__.objects.filter(template=template).order_by("order")

    @staticmethod
    def clean_orders(klass, template):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            klass (`BaseSurveyQuestionTemplateLink` subclass)
            template (template obj): particular poll template.
        """
        # Get ordered questions for a given template (e.g. `PreCourseSurveyQuestionTemplateLink` objects)
        entries = klass.objects.filter(template=template).order_by("order")
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=klass.MIN_ORDER):
            if entry.order and i != int(entry.order):
                klass.objects.filter(id=entry.id).update(order=i)


class SurveyQuestionTemplateLink(BaseQuestionTemplateLink):
    """
    Intermediary model to keep question-template relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    template = models.ForeignKey(SurveyTemplate)
    question = models.ForeignKey(SurveyQuestion)

    def __unicode__(self):  # NOQA
        return "SurveyQuestionTemplateLink #{!s}".format(self.id)

    def clean(self):
        super(SurveyQuestionTemplateLink, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default questions can be stored in a survey template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(SurveyQuestionTemplateLink, self).save(force_insert, force_update, using, update_fields)


class OpenEndedSurveyQuestionTemplateLink(BaseQuestionTemplateLink):
    """
    Intermediary model to keep question-template relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.OpenEndedSurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    template = models.ForeignKey(OpenEndedSurveyTemplate)
    question = models.ForeignKey(OpenEndedSurveyQuestion)

    def __unicode__(self):  # NOQA
        return "OpenEndedSurveyQuestionTemplateLink #{!s}".format(self.id)

    def clean(self):
        super(OpenEndedSurveyQuestionTemplateLink, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default questions can be stored "
                                                   "in an open ended survey template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(OpenEndedSurveyQuestionTemplateLink, self).save(force_insert, force_update, using, update_fields)


class PreCourseSurveyQuestionTemplateLink(BaseQuestionTemplateLink):
    """Intermediary model to keep pre-course survey question-template relations."""

    template = models.ForeignKey(PreCourseSurveyTemplate)
    question = models.ForeignKey(SurveyQuestion)

    def __unicode__(self):  # NOQA
        return "PreCourseSurveyQuestionTemplateLink #{!s}".format(self.id)

    def clean(self):
        super(PreCourseSurveyQuestionTemplateLink, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default questions can be stored in a survey template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(PreCourseSurveyQuestionTemplateLink, self).save(force_insert, force_update, using, update_fields)


class PostCourseSurveyQuestionTemplateLink(BaseQuestionTemplateLink):
    """Intermediary model to keep post-course survey question-template relations."""

    template = models.ForeignKey(PostCourseSurveyTemplate)
    question = models.ForeignKey(SurveyQuestion)

    def __unicode__(self):  # NOQA
        return "PostCourseSurveyQuestionTemplateLink #{!s}".format(self.id)

    def clean(self):
        super(PostCourseSurveyQuestionTemplateLink, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default questions can be stored in a survey template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(PostCourseSurveyQuestionTemplateLink, self).save(force_insert, force_update, using, update_fields)


class CourseQualitySurveyQuestionTemplateLink(BaseQuestionTemplateLink):
    """Intermediary model to keep post-course survey question-template relations."""

    template = models.ForeignKey(CourseQualitySurveyTemplate)
    question = models.ForeignKey(SurveyQuestion)

    def __unicode__(self):  # NOQA
        return "CourseQualitySurveyQuestionTemplateLink #{!s}".format(self.id)

    def clean(self):
        super(CourseQualitySurveyQuestionTemplateLink, self).clean()
        question = getattr(self, "question", None)
        if question:
            if not question.is_default:
                raise ValidationError({"question": "Only default questions can be stored in a survey template."})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(CourseQualitySurveyQuestionTemplateLink, self).save(force_insert, force_update, using, update_fields)


class SurveyPollCommonsection(TimeStampedModel):
    """
    Survey/Poll/Open-Ended Survey commonsection settings model.

    Consider replacing with custom Sysadmin settings.
    """

    contains_poll = models.BooleanField(default=True)
    contains_survey = models.BooleanField(default=True)
    contains_open_ended_survey = models.BooleanField(default=True)
    # Dedicated survey xblocks
    contains_pre_course_survey = models.BooleanField(default=True)
    contains_post_course_survey = models.BooleanField(default=True)
    contains_course_quality_survey = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "commonsections"


@receiver(post_save, sender=OpenEndedSurveyTemplate)
def cleanup_open_ended_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""

    OpenEndedSurveyQuestionTemplateLink.clean_orders(
        klass=OpenEndedSurveyQuestionTemplateLink,
        template=instance
    )


@receiver(post_save, sender=SurveyTemplate)
def cleanup_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""

    SurveyQuestionTemplateLink.clean_orders(
        klass=SurveyQuestionTemplateLink,
        template=instance
    )


@receiver(post_save, sender=PreCourseSurveyTemplate)
def cleanup_pre_course_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""

    PreCourseSurveyQuestionTemplateLink.clean_orders(
        klass=PreCourseSurveyQuestionTemplateLink,
        template=instance
    )


@receiver(post_save, sender=PostCourseSurveyTemplate)
def cleanup_post_course_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""

    PostCourseSurveyQuestionTemplateLink.clean_orders(
        klass=PostCourseSurveyQuestionTemplateLink,
        template=instance
    )


@receiver(post_save, sender=CourseQualitySurveyTemplate)
def cleanup_course_quality_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""

    CourseQualitySurveyQuestionTemplateLink.clean_orders(
        klass=CourseQualitySurveyQuestionTemplateLink,
        template=instance
    )


@receiver(post_save, sender=PollQuestion)
def cleanup_open_ended_survey_question_answer_links(sender, instance, **kwargs):
    """Go over all related question-answer links and clean them up."""

    PollQuestionAnswerLink.clean_orders(
        klass=PollQuestionAnswerLink,
        question=instance
    )


@receiver(post_save, sender=SurveyQuestion)
def cleanup_survey_question_answer_links(sender, instance, **kwargs):
    """Go over all related question-answer links and clean them up."""

    SurveyQuestionAnswerLink.clean_orders(
        klass=SurveyQuestionAnswerLink,
        question=instance
    )
