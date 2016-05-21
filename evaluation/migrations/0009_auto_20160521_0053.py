# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0008_auto_20160521_0049'),
    ]

    operations = [
        migrations.RenameField(
            model_name='evalfield',
            old_name='wb_question',
            new_name='question',
        ),
    ]
