# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0008_auto_20191010_1256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='surveypollcommonsection',
            name='contains_poll',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='surveypollcommonsection',
            name='contains_survey',
            field=models.BooleanField(default=False),
        ),
    ]
