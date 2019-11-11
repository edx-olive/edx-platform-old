# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone
import model_utils.fields
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletionEffortPollSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CompletionEffortPollTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseQualitySurveyQuestionTemplateLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseQualitySurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseQualitySurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenEndedSurveyQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_default', models.BooleanField(default=True)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(help_text=b"Course location id e.g. 'course-v1:RF+CS101+2019_T1'", max_length=255, null=True, blank=True)),
                ('text', models.CharField(max_length=512)),
                ('image_url', models.CharField(max_length=255, null=True, blank=True)),
                ('image_alt_text', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenEndedSurveyQuestionTemplateLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('question', models.ForeignKey(to='poll_survey.OpenEndedSurveyQuestion')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenEndedSurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
                ('answer_text', models.CharField(max_length=200)),
                ('question', models.ForeignKey(to='poll_survey.OpenEndedSurveyQuestion')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OpenEndedSurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('questions', models.ManyToManyField(to='poll_survey.OpenEndedSurveyQuestion', through='poll_survey.OpenEndedSurveyQuestionTemplateLink')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PollAnswerOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('text', models.CharField(max_length=255)),
                ('image_url', models.CharField(max_length=255, null=True, blank=True)),
                ('image_alt_text', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PollQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_default', models.BooleanField(default=True)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(help_text=b"Course location id e.g. 'course-v1:RF+CS101+2019_T1'", max_length=255, null=True, blank=True)),
                ('text', models.CharField(max_length=512)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PollQuestionAnswerLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('answer', models.ForeignKey(to='poll_survey.PollAnswerOption')),
                ('question', models.ForeignKey(to='poll_survey.PollQuestion')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PollSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
                ('answer', models.ForeignKey(to='poll_survey.PollAnswerOption')),
                ('question', models.ForeignKey(to='poll_survey.PollQuestion')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PollTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('question', models.OneToOneField(to='poll_survey.PollQuestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PostCourseSurveyQuestionTemplateLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PostCourseSurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PostCourseSurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreCourseSurveyQuestionTemplateLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreCourseSurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PreCourseSurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RatingPollSubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
                ('answer', models.ForeignKey(to='poll_survey.PollAnswerOption')),
                ('question', models.ForeignKey(to='poll_survey.PollQuestion')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RatingPollTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('question', models.OneToOneField(to='poll_survey.PollQuestion')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyAnswerOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyPollCommonsection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('contains_poll', models.BooleanField(default=False)),
                ('contains_survey', models.BooleanField(default=False)),
                ('contains_pre_course_survey', models.BooleanField(default=True)),
                ('contains_post_course_survey', models.BooleanField(default=True)),
                ('contains_course_quality_survey', models.BooleanField(default=True)),
                ('contains_rating_poll', models.BooleanField(default=True)),
                ('contains_completion_effort_poll', models.BooleanField(default=True)),
                ('contains_open_ended_survey', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'commonsections',
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_default', models.BooleanField(default=True)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(help_text=b"Course location id e.g. 'course-v1:RF+CS101+2019_T1'", max_length=255, null=True, blank=True)),
                ('text', models.CharField(max_length=512)),
                ('image_url', models.CharField(max_length=255, null=True, blank=True)),
                ('image_alt_text', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestionAnswerLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('answer', models.ForeignKey(to='poll_survey.SurveyAnswerOption')),
                ('question', models.ForeignKey(to='poll_survey.SurveyQuestion')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyQuestionTemplateLink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('order', models.IntegerField(null=True, blank=True)),
                ('question', models.ForeignKey(to='poll_survey.SurveyQuestion')),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False)),
                ('employee_id', models.CharField(max_length=50, null=True, blank=True)),
                ('answer', models.ForeignKey(to='poll_survey.SurveyAnswerOption')),
                ('question', models.ForeignKey(to='poll_survey.SurveyQuestion')),
                ('student', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('questions', models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.SurveyQuestionTemplateLink')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='surveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.SurveyTemplate'),
        ),
        migrations.AddField(
            model_name='surveyquestion',
            name='answers',
            field=models.ManyToManyField(to='poll_survey.SurveyAnswerOption', through='poll_survey.SurveyQuestionAnswerLink'),
        ),
        migrations.AddField(
            model_name='precoursesurveytemplate',
            name='questions',
            field=models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.PreCourseSurveyQuestionTemplateLink'),
        ),
        migrations.AddField(
            model_name='precoursesurveysubmission',
            name='answer',
            field=models.ForeignKey(to='poll_survey.SurveyAnswerOption'),
        ),
        migrations.AddField(
            model_name='precoursesurveysubmission',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='precoursesurveysubmission',
            name='student',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='precoursesurveyquestiontemplatelink',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='precoursesurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.PreCourseSurveyTemplate'),
        ),
        migrations.AddField(
            model_name='postcoursesurveytemplate',
            name='questions',
            field=models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.PostCourseSurveyQuestionTemplateLink'),
        ),
        migrations.AddField(
            model_name='postcoursesurveysubmission',
            name='answer',
            field=models.ForeignKey(to='poll_survey.SurveyAnswerOption'),
        ),
        migrations.AddField(
            model_name='postcoursesurveysubmission',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='postcoursesurveysubmission',
            name='student',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='postcoursesurveyquestiontemplatelink',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='postcoursesurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.PostCourseSurveyTemplate'),
        ),
        migrations.AddField(
            model_name='pollquestion',
            name='answers',
            field=models.ManyToManyField(to='poll_survey.PollAnswerOption', through='poll_survey.PollQuestionAnswerLink'),
        ),
        migrations.AddField(
            model_name='openendedsurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.OpenEndedSurveyTemplate'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveytemplate',
            name='questions',
            field=models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.CourseQualitySurveyQuestionTemplateLink'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveysubmission',
            name='answer',
            field=models.ForeignKey(to='poll_survey.SurveyAnswerOption'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveysubmission',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveysubmission',
            name='student',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='coursequalitysurveyquestiontemplatelink',
            name='question',
            field=models.ForeignKey(to='poll_survey.SurveyQuestion'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.CourseQualitySurveyTemplate'),
        ),
        migrations.AddField(
            model_name='completioneffortpolltemplate',
            name='question',
            field=models.OneToOneField(to='poll_survey.PollQuestion'),
        ),
        migrations.AddField(
            model_name='completioneffortpollsubmission',
            name='answer',
            field=models.ForeignKey(to='poll_survey.PollAnswerOption'),
        ),
        migrations.AddField(
            model_name='completioneffortpollsubmission',
            name='question',
            field=models.ForeignKey(to='poll_survey.PollQuestion'),
        ),
        migrations.AddField(
            model_name='completioneffortpollsubmission',
            name='student',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='surveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='ratingpollsubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='precoursesurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='postcoursesurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='pollsubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='openendedsurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='coursequalitysurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='completioneffortpollsubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
    ]
