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
        ('poll_survey', '0006_auto_20190930_0921'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletionEffortPollSubmission',
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
            name='CompletionEffortPollTemplate',
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
            name='RatingPollSubmission',
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
        migrations.AlterUniqueTogether(
            name='ratingpollsubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
        migrations.AlterUniqueTogether(
            name='completioneffortpollsubmission',
            unique_together=set([('student', 'course', 'question')]),
        ),
    ]
