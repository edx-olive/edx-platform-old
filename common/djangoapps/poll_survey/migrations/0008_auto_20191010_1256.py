# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0007_auto_20191010_1230'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveypollcommonsection',
            name='contains_completion_effort_poll',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='surveypollcommonsection',
            name='contains_rating_poll',
            field=models.BooleanField(default=True),
        ),
    ]
