# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0002_connect_eval_to_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='evalfield',
            name='label',
            field=models.CharField(unique=True, default='test', max_length=500),
            preserve_default=False,
        ),
    ]
