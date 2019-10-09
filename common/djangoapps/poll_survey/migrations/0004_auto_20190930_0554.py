# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0003_auto_20190919_0529'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreCourseSurveyQuestionTemplateLink',
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
            name='PreCourseSurveyTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('is_enabled', models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.')),
                ('questions', models.ManyToManyField(to='poll_survey.SurveyQuestion', through='poll_survey.PreCourseSurveyQuestionTemplateLink')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='surveypollcommonsection',
            name='contains_pre_course_survey',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='precoursesurveyquestiontemplatelink',
            name='template',
            field=models.ForeignKey(to='poll_survey.PreCourseSurveyTemplate'),
        ),
    ]
