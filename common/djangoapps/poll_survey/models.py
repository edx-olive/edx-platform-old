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
    text = models.CharField(max_length=255)

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


class SurveyQuestionAnswerLink(TimeStampedModel):
    """
    Intermediary model to keep question-answer relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    MIN_ORDER = 1

    question = models.ForeignKey(SurveyQuestion)
    answer = models.ForeignKey(SurveyAnswerOption)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ("order",)

    def __unicode__(self):  # NOQA
        return "Question-Answer Link #{!s}".format(self.id)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(SurveyQuestionAnswerLink, self).save(force_insert, force_update, using, update_fields)

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new `SurveyQuestionAnswerLink.order`"""
        n = self.get_answer_links(self.question).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    @staticmethod
    def get_answer_links(question):
        """Get ordered entries for a given template. """
        return SurveyQuestionAnswerLink.objects.filter(question=question).order_by("order")

    @staticmethod
    def clean_orders(entries):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            entries (`SurveyQuestionAnswerLink` objects): entries ordered by `order` field.
        """
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=SurveyQuestionAnswerLink.MIN_ORDER):
            if entry.order and i != int(entry.order):
                SurveyQuestionAnswerLink.objects.filter(id=entry.id).update(order=i)


class PollQuestionAnswerLink(TimeStampedModel):
    """
    Intermediary model to keep question-answer relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.PollDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """
    MIN_ORDER = 1

    question = models.ForeignKey(PollQuestion)
    answer = models.ForeignKey(PollAnswerOption)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ("order",)

    def __unicode__(self):  # NOQA
        return "Question-Answer Link #{!s}".format(self.id)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        self.set_order()
        super(PollQuestionAnswerLink, self).save(force_insert, force_update, using, update_fields)

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new `PollQuestionAnswerLink.order`"""
        n = self.get_answer_links(self.question).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    @staticmethod
    def get_answer_links(question):
        """Get ordered entries for a given template. """
        return PollQuestionAnswerLink.objects.filter(question=question).order_by("order")

    @staticmethod
    def clean_orders(entries):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            entries (`PollQuestionAnswerLink` objects): entries ordered by `order` field.
        """
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=PollQuestionAnswerLink.MIN_ORDER):
            if entry.order and i != int(entry.order):
                PollQuestionAnswerLink.objects.filter(id=entry.id).update(order=i)


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
    answer_text = models.TextField(max_length=200)

    def __unicode__(self):  # NOQA
        return "OpenEndedSurveySubmission #{!s}".format(self.id)


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


class SurveyQuestionTemplateLink(TimeStampedModel):
    """
    Intermediary model to keep question-template relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.SurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    MIN_ORDER = 1

    template = models.ForeignKey(SurveyTemplate)
    question = models.ForeignKey(SurveyQuestion)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ("order",)

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

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new `SurveyQuestionTemplateLink.order`"""
        n = self.get_question_links(self.template).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    @staticmethod
    def get_question_links(template):
        """Get ordered entries for a given template. """
        return SurveyQuestionTemplateLink.objects.filter(template=template).order_by("order")

    @staticmethod
    def clean_orders(entries):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            entries (`SurveyQuestionTemplateLink` objects): entries ordered by `order` field.
        """
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=SurveyQuestionTemplateLink.MIN_ORDER):
            if entry.order and i != int(entry.order):
                SurveyQuestionTemplateLink.objects.filter(id=entry.id).update(order=i)


class OpenEndedSurveyQuestionTemplateLink(TimeStampedModel):
    """
    Intermediary model to keep question-template relations.

    Introduced because standard M2M querying breaks when xblocks'
    defaults are initialized (see poll xblock `defaults.OpenEndedSurveyDefaults`).
    Ref.: https://code.djangoproject.com/attachment/ticket/1796
    """

    MIN_ORDER = 1

    template = models.ForeignKey(OpenEndedSurveyTemplate)
    question = models.ForeignKey(OpenEndedSurveyQuestion)
    order = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ("order",)

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

    def set_order(self):
        """Set the order id."""
        order = getattr(self, "order", None)
        if order is None:
            # e.g. newly created entry w/ order
            order = self._next_order()
        self.order = order

    def _next_order(self):
        """Get the next order value for appending a new `OpenEndedSurveyQuestionTemplateLink.order`"""
        n = self.get_question_links(self.template).aggregate(Max("order"))["order__max"]
        if n is None:
            return self.MIN_ORDER
        else:
            return n + 1

    @staticmethod
    def get_question_links(template):
        """Get ordered entries for a given template. """
        return OpenEndedSurveyQuestionTemplateLink.objects.filter(template=template).order_by("order")

    @staticmethod
    def clean_orders(entries):
        """
        Clean up orders.

        Get rid of duplicates, large numbers etc.

        Arguments:
            entries (`OpenEndedSurveyQuestionTemplateLink` objects): entries ordered by `order` field.
        """
        if not entries:
            return
        if len(entries) == 1:
            return
        for i, entry in enumerate(entries, start=OpenEndedSurveyQuestionTemplateLink.MIN_ORDER):
            if entry.order and i != int(entry.order):
                OpenEndedSurveyQuestionTemplateLink.objects.filter(id=entry.id).update(order=i)


class SurveyPollCommonsection(TimeStampedModel):
    """
    Survey/Poll/Open-Ended Survey commonsection settings model.

    Consider replacing with custom Sysadmin settings.
    """

    contains_poll = models.BooleanField(default=True)
    contains_survey = models.BooleanField(default=True)
    contains_open_ended_survey = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "commonsections"


@receiver(post_save, sender=OpenEndedSurveyTemplate)
def cleanup_open_ended_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""
    link_entries = OpenEndedSurveyQuestionTemplateLink.get_question_links(template=instance)
    OpenEndedSurveyQuestionTemplateLink.clean_orders(entries=link_entries)


@receiver(post_save, sender=SurveyTemplate)
def cleanup_survey_question_template_links(sender, instance, **kwargs):
    """Go over all related template-question links and clean them up."""
    link_entries = SurveyQuestionTemplateLink.get_question_links(template=instance)
    SurveyQuestionTemplateLink.clean_orders(entries=link_entries)


@receiver(post_save, sender=PollQuestion)
def cleanup_open_ended_survey_question_answer_links(sender, instance, **kwargs):
    """Go over all related question-answer links and clean them up."""
    link_entries = PollQuestionAnswerLink.get_answer_links(question=instance)
    PollQuestionAnswerLink.clean_orders(entries=link_entries)


@receiver(post_save, sender=SurveyQuestion)
def cleanup_survey_question_answer_links(sender, instance, **kwargs):
    """Go over all related question-answer links and clean them up."""
    link_entries = SurveyQuestionAnswerLink.get_answer_links(question=instance)
    SurveyQuestionAnswerLink.clean_orders(entries=link_entries)
