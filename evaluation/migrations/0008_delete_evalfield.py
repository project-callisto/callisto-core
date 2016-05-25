# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0007_newevalfield'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='evalfield',
            name='question',
        ),
        migrations.DeleteModel(
            name='EvalField',
        ),
    ]
