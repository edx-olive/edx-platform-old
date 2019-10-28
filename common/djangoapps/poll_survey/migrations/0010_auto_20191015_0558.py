# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0009_auto_20191011_0843'),
    ]

    operations = [
        migrations.AddField(
            model_name='completioneffortpollsubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='coursequalitysurveysubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='openendedsurveysubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='pollsubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='postcoursesurveysubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='precoursesurveysubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='ratingpollsubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='surveysubmission',
            name='employee_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
    ]
