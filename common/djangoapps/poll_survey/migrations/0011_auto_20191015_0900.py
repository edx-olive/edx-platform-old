# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0010_auto_20191015_0558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='completioneffortpollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='coursequalitysurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='openendedsurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='pollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='postcoursesurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='precoursesurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='ratingpollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='surveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'First submission date. Might differ from the entry creation date.', editable=False),
        ),
    ]
