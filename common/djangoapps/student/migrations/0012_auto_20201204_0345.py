# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import student.models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0011_userprofile_employee_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='employee_id',
            field=student.models.CharNullField(max_length=50, unique=True, null=True, blank=True),
        ),
    ]
