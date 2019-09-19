# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_overviews', '0014_auto_20180604_0613'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseoverview',
            name='short_description',
            field=models.TextField(null=True),
        ),
    ]
