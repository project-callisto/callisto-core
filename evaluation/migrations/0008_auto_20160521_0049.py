# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0007_evalfield_wb_question'),
        ('reports', '0082_migrate_to_wizard_builder')
    ]

    operations = [
        migrations.RemoveField(
            model_name='evalfield',
            name='question',
        ),
        migrations.AlterField(
            model_name='evalfield',
            name='wb_question',
            field=models.OneToOneField(serialize=False, to='wizard_builder.FormQuestion', primary_key=True),
        ),
    ]
