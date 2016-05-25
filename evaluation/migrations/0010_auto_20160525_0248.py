# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0009_auto_20160521_0053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evalfield',
            name='question',
            field=models.OneToOneField(primary_key=True, to='reports.RecordFormItem', serialize=False),
        ),
    ]
