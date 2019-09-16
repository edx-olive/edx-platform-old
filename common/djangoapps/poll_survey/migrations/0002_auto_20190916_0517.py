# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pollquestionanswerlink',
            options={'ordering': ('order',)},
        ),
        migrations.AlterModelOptions(
            name='surveyquestionanswerlink',
            options={'ordering': ('order',)},
        ),
        migrations.AlterField(
            model_name='openendedsurveytemplate',
            name='is_enabled',
            field=models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.'),
        ),
        migrations.AlterField(
            model_name='polltemplate',
            name='is_enabled',
            field=models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.'),
        ),
        migrations.AlterField(
            model_name='surveytemplate',
            name='is_enabled',
            field=models.BooleanField(default=False, help_text=b'Warning: any changes in default templates will take effect only after the edX platform CMS and LMS stack gets restarted. Please contact the application team for them to follow a deployment procedure.'),
        ),
    ]
