# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wizard_builder', '0001_initial'),
        ('evaluation', '0006_auto_20151211_1846'),
    ]

    operations = [
        migrations.AddField(
            model_name='evalfield',
            name='wb_question',
            field=models.OneToOneField(to='wizard_builder.FormQuestion', null=True, blank=True),
        ),
    ]
