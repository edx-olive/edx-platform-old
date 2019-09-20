# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0002_auto_20190916_0517'),
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
            model_name='openendedsurveyquestion',
            name='text',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='openendedsurveysubmission',
            name='answer_text',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='pollquestion',
            name='text',
            field=models.CharField(max_length=512),
        ),
        migrations.AlterField(
            model_name='surveyquestion',
            name='text',
            field=models.CharField(max_length=512),
        ),
    ]
