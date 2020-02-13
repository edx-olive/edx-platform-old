# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('poll_survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ratingpollsubmission',
            name='catalog_marker',
            field=models.CharField(blank=True, max_length=64, null=True, help_text=b'Marker as a result of rating processing and pushing to the AMAT Catalog (Pathway).', choices=[(b'CATALOG_AUTH_ERROR', b'CATALOG_AUTH_ERROR'), (b'CATALOG_BAD_GATEWAY_ERROR', b'CATALOG_BAD_GATEWAY_ERROR'), (b'CATALOG_CONNECTION_ERROR', b'CATALOG_CONNECTION_ERROR'), (b'CATALOG_FORBIDDEN_ERROR', b'CATALOG_FORBIDDEN_ERROR'), (b'CATALOG_OTHER_ERROR', b'CATALOG_OTHER_ERROR'), (b'CATALOG_RATING_BAD_REQUEST', b'CATALOG_RATING_BAD_REQUEST'), (b'CATALOG_RATING_OTHER_ERROR', b'CATALOG_RATING_OTHER_ERROR'), (b'CATALOG_RESPONSE_PARSING_ERROR', b'CATALOG_RESPONSE_PARSING_ERROR'), (b'CATALOG_SERVER_ERROR', b'CATALOG_SERVER_ERROR'), (b'CATALOG_DEFAULT_CASE', b'CATALOG_DEFAULT_CASE'), (b'CATALOG_RATING_SUCCESS', b'CATALOG_RATING_SUCCESS'), (b'EDX_ERROR', b'EDX_ERROR'), (b'RATING_INCORRECT_USER_ID', b'RATING_INCORRECT_USER_ID'), (b'RATING_INVALID_COURSE_ID', b'RATING_INVALID_COURSE_ID'), (b'RATING_INVALID_RATING', b'RATING_INVALID_RATING'), (b'RATING_NON_EXISTING_COURSE', b'RATING_NON_EXISTING_COURSE'), (b'RATING_USER_WITHOUT_EMPLOYEE_ID', b'RATING_USER_WITHOUT_EMPLOYEE_ID')]),
        ),
        migrations.AddField(
            model_name='ratingpollsubmission',
            name='catalog_processed_date',
            field=models.DateTimeField(help_text=b'The date of rating processing for the AMAT Catalog (Pathway).', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='ratingpollsubmission',
            name='course_agu_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='completioneffortpollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='coursequalitysurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='openendedsurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='pollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='postcoursesurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='precoursesurveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='ratingpollsubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
        migrations.AlterField(
            model_name='surveysubmission',
            name='submission_date',
            field=model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, help_text=b'The submission/re-submission date. Might differ from the entry creation date.', editable=False),
        ),
    ]
