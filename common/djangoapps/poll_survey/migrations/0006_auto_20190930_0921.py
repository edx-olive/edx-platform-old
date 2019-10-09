# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import openedx.core.djangoapps.xmodule_django.models
import model_utils.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('poll_survey', '0005_auto_20190930_0604'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseQualitySurveyQuestionTemplateLink',
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
            name='CourseQualitySurveySubmission',
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
            name='CourseQualitySurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('questions', models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.CourseQualitySurveyQuestionTemplateLink')),
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
                ('question', models.ForeignKey(to='poll_survey.SurveyQuestion')),
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
            name='PostCourseSurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('questions', models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.PostCourseSurveyQuestionTemplateLink')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='surveypollcommonsection',
            name='contains_course_quality_survey',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='surveypollcommonsection',
            name='contains_post_course_survey',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='postcoursesurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.PostCourseSurveyTemplate'),
        ),
        migrations.AddField(
            model_name='coursequalitysurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.CourseQualitySurveyTemplate'),
        ),
        migrations.AlterUniqueTogether(
            name='postcoursesurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='coursequalitysurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
    ]
