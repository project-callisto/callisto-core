# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0003_evalfield_label'),
    ]

    operations = [
        migrations.RenameField(
            model_name='evalrow',
            old_name='identifier',
            new_name='record_identifier',
        ),
        migrations.AddField(
            model_name='evalrow',
            name='user_identifier',
            field=models.CharField(max_length=500, default='default'),
            preserve_default=False,
        ),
    ]
