# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone
import openedx.core.djangoapps.xmodule_django.models
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OpenEndedSurveyQuestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_default', models.BooleanField(default=True)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(help_text=b"Course location id e.g. 'course-v1:RF+CS101+2019_T1'", max_length=255, null=True, blank=True)),
                ('text', models.CharField(max_length=255)),
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
            },
        ),
        migrations.CreateModel(
            name='OpenEndedSurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from entry creation date.', editable=False)),
                ('answer_text', models.TextField(max_length=200)),
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
                ('is_enabled', models.BooleanField(default=False)),
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
                ('text', models.CharField(max_length=255)),
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
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from entry creation date.', editable=False)),
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
                ('is_enabled', models.BooleanField(default=False)),
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
                ('contains_poll', models.BooleanField(default=True)),
                ('contains_survey', models.BooleanField(default=True)),
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
                ('text', models.CharField(max_length=255)),
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
            },
        ),
        migrations.CreateModel(
            name='SurveySubmission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('course', openedx.core.djangoapps.xmodule_django.models.CourseKeyField(max_length=255)),
                ('submission_date', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from entry creation date.', editable=False)),
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
                ('is_enabled', models.BooleanField(default=False)),
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
            model_name='pollquestion',
            name='answers',
            field=models.ManyToManyField(to='poll_survey.PollAnswerOption', through='poll_survey.PollQuestionAnswerLink'),
        ),
        migrations.AddField(
            model_name='openendedsurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.OpenEndedSurveyTemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='surveysubmission',
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
    ]
