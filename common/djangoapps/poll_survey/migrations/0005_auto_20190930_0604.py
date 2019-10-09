# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import openedx.core.djangoapps.xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('poll_survey', '0004_auto_20190930_0554'),
    ]

    operations = [
        migrations.CreateModel(
            name='PreCourseSurveySubmission',
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
        migrations.AlterUniqueTogether(
            name='precoursesurveysubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
    ]
