# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0005_add_actions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='evalfield',
            name='label',
            field=models.CharField(max_length=500),
        ),
    ]
